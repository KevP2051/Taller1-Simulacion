import csv
import math
import sys
import time
from enum import IntEnum
from pathlib import Path
from typing import NamedTuple, Protocol

try:
    from punto3_generadores_pseudoaleatorios.generadores import generar_congruencial_lineal
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from punto3_generadores_pseudoaleatorios.generadores import generar_congruencial_lineal

class State(IntEnum):
    """Compartimentos del modelo SEIR."""
    S = 0  # Susceptible
    E = 1  # Expuesto (infectado, aún no contagioso)
    I = 2  # Infectado (contagioso)
    R = 3  # Removido (recuperado o fallecido)

STATE_S, STATE_E, STATE_I, STATE_R = 0, 1, 2, 3

RANDOM_PARAMETERS: tuple[str, ...] = (
    "beta",
    "probabilidad_transmision",
    "tasa_vacunacion",
    "efectividad_vacuna",
    "letalidad",
)

FIXED_PARAMETERS: tuple[str, ...] = (
    "poblacion",
    "infectados_iniciales",
    "dias",
    "contactos_maximos_k",
    "umbral_control",
    "seleccion_solo_susceptibles",
    "periodo_incubacion",
    "periodo_infeccioso",
)

Config = dict[str, tuple[float, float]]

class UniformSource(Protocol):
    """Contrato mínimo que debe cumplir cualquier generador usado por el motor."""
    state: int
    def next(self) -> float:
        """Devuelve el siguiente U ~ U[0, 1)."""
 
 
class DailyRecord(NamedTuple):
    """Foto del sistema al cierre de un día. Sigue siendo una tupla (indexable)."""
    day: int
    S: int
    E: int
    I: int
    R: int
    F: int  # fallecidos acumulados (ya incluidos en R)

class PseudorandomGenerator:
    """Adaptador incremental para el generador por secuencias del punto 3."""

    def __init__(self, seed, a=1664525, c=1013904223, m=2 ** 32):
        self.state = seed % m
        self.a, self.c, self.m = a, c, m
        self._pending_sequence = []

    def next(self):
        if not self._pending_sequence:
            sequence = generar_congruencial_lineal(
                self.state, self.a, self.c, self.m, 256)
            self._pending_sequence = list(zip(
                sequence["valores_x"], sequence["numeros_r"]))
        self.state, number = self._pending_sequence.pop(0)
        return number


def uniform(gen, a, b):
    """Transformacion lineal X = a + (b - a) * U"""
    return a + (b - a) * gen.next()

def read_config(path):
    config = {}
    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            config[row["parametro"].strip()] = (
                float(row["min"]), float(row["max"]))
    return config

def sample_params(config, gen):
    """Devuelve dict con los parametros de UNA replica. Siempre consume
    un numero por parametro aleatorio (aunque min == max)."""
    params = {}
    for name in RANDOM_PARAMETERS:
        min, max = config[name]
        params[name] = uniform(gen, min, max)
    # Parametros fijos del escenario
    for name in ("poblacion", "infectados_iniciales", "dias",
                   "contactos_maximos_k", "umbral_control",
                   "seleccion_solo_susceptibles"):
        params[name] = int(config[name][0])
    params["incubacion_min"], params["incubacion_max"] = config["periodo_incubacion"]
    params["infeccioso_min"], params["infeccioso_max"] = config["periodo_infeccioso"]
    return params


# PASO 1 - GENERACION ESTOCASTICA DE CONTACTOS
# ---------------------------------------------------------------------
def build_contact_cdf(beta, k):
    q = beta / k
    cdf, cumulative = [], 0.0
    for contact_count in range(k + 1):
        cumulative += math.comb(k, contact_count) * (q ** contact_count) * ((1 - q) ** (k - contact_count))
        cdf.append(cumulative)
    cdf[-1] = 1.0
    return cdf  # CDF[c] = P(contactos <= c)

def sample_contact_count(gen, cdf_table):
    contact_random = gen.next()
    for contact_count, limit in enumerate(cdf_table):
        if contact_random < limit:
            return contact_count
    return len(cdf_table) - 1

# PASO 2 - SELECCION ESTOCASTICA DEL INDIVIDUO CONTACTADO
# ---------------------------------------------------------------------
def select_susceptible(gen, susceptible_list):
    """Elige UN susceptible uniformemente (indice = piso(r * |S|))."""
    index = int(gen.next() * len(susceptible_list))
    return susceptible_list[index]

# PASO 3 - EVALUACION ESTOCASTICA DE TRANSMISION
#    p_efectiva = p_base * factor_vacunacion
#    factor_vacunacion = (1 - efectividad) si vacunado; 1 si no.
# ---------------------------------------------------------------------
def evaluate_transmission(gen, base_p, vaccinated, effectiveness):
    vaccination_factor = (1.0 - effectiveness) if vaccinated else 1.0
    effective_p = base_p * vaccination_factor
    transmission_r = gen.next()
    return transmission_r < effective_p

def init_population(params, gen):
    N = params["poblacion"]
    state = [STATE_S] * N
    vaccinated = [False] * N
    # Vacunacion: subconjunto aleatorio de tamano exacto round(v * N)
    vaccinated_count = int(round(params["tasa_vacunacion"] * N))
    ids = list(range(N))
    for i in range(vaccinated_count):
        j = i + int(gen.next() * (N - i))
        ids[i], ids[j] = ids[j], ids[i]
        vaccinated[ids[i]] = True
    # Casos indice: n distintos elegidos al azar
    initial_cases = set()
    while len(initial_cases) < params["infectados_iniciales"]:
        initial_cases.add(int(gen.next() * N))
    for i in initial_cases:
        state[i] = STATE_I
    return state, vaccinated, sorted(initial_cases)


def sample_duration(gen, min, max):
    """Periodo en dias: U(min, max) redondeado al entero mas cercano."""
    return int(min + (max - min) * gen.next() + 0.5)

def apply_scheduled_transitions(day, state, agenda_E_a_I, agenda_I_a_R,
                                  death, list_I, pos_I, containers):
    """Aplica las transiciones programadas para 'dia'. Devuelve nada;
    modifica listas de estado y contadores in-place."""
    # I -> R
    for i in agenda_I_a_R.pop(day, ()):
        p = pos_I.pop(i)
        last = list_I.pop()
        if last != i:
            list_I[p] = last
            pos_I[last] = p
        state[i] = STATE_R
        containers["I"] -= 1
        containers["R"] += 1
        if death[i]:
            containers["F"] += 1
    # E -> I
    for i in agenda_E_a_I.pop(day, ()):
        state[i] = STATE_I
        pos_I[i] = len(list_I)
        list_I.append(i)
        containers["E"] -= 1
        containers["I"] += 1

def simulate_epidemic(params, gen):
    N, days = params["poblacion"], params["dias"]
    state, vaccinated, ids = init_population(params, gen)

    S_ids = [i for i in range(N) if state[i] == STATE_S]
    S_pos = {i: p for p, i in enumerate(S_ids)}
    I_ids = list(ids)
    I_pos = {i: p for p, i in enumerate(I_ids)}

    agenda_E_a_I, agenda_I_a_R, death = {}, {}, {}

    for i in ids:
        gamma = sample_duration(gen, params["infeccioso_min"], params["infeccioso_max"])
        dead = gen.next() < params["letalidad"]
        death[i] = dead
        agenda_I_a_R.setdefault(gamma, []).append(i)

    contact_table = build_contact_cdf(params["beta"], params["contactos_maximos_k"])
    counts = {"E": 0, "I": len(ids), "R": 0, "F": 0}
    serie = [(0, N - len(ids), 0, len(ids), 0, 0)]  # dia,S,E,I,R,F
    just_S = params["seleccion_solo_susceptibles"] == 1
    p_base, efect = params["probabilidad_transmision"], params["efectividad_vacuna"]
    fatality = params["letalidad"]

    for day in range(1, days + 1):
        # (a) transiciones programadas para hoy
        apply_scheduled_transitions(day, state, agenda_E_a_I, agenda_I_a_R,
                                      death, I_ids, I_pos, counts)
        # (b) contagios del dia (usa el conjunto de infectados vigente hoy)
        infected_today = list(I_ids)
        for _infected in infected_today:
            n_contacts = sample_contact_count(gen, contact_table)          # Paso 1
            for _c in range(n_contacts):
                if just_S:
                    if not S_ids:
                        break
                    goal = select_susceptible(gen, S_ids)        # Paso 2
                else:
                    goal = int(gen.next() * N)                     # Paso 2 (mezcla homogenea)
                    if state[goal] != STATE_S:
                        continue
                if evaluate_transmission(gen, p_base, vaccinated[goal], efect):  # Paso 3
                    # S -> E ; se sortean sus periodos y destino AL EXPONERSE
                    p = S_pos.pop(goal)
                    ultimo = S_ids.pop()
                    if ultimo != goal:
                        S_ids[p] = ultimo
                        S_pos[ultimo] = p
                    state[goal] = STATE_E
                    sigma = sample_duration(gen, params["incubacion_min"], params["incubacion_max"])
                    gamma = sample_duration(gen, params["infeccioso_min"], params["infeccioso_max"])
                    death[goal] = gen.next() < fatality
                    dia_I = day + sigma
                    dia_R = dia_I + gamma
                    if dia_I <= days:
                        agenda_E_a_I.setdefault(dia_I, []).append(goal)
                    if dia_R <= days:
                        agenda_I_a_R.setdefault(dia_R, []).append(goal)
                    counts["E"] += 1
        S = len(S_ids)
        E, I, R, F = counts["E"], counts["I"], counts["R"], counts["F"]
        assert S + E + I + R == N, f"Conservacion violada en dia {day}"
        serie.append((day, S, E, I, R, F))

    return serie

def summarize_replica(serie, params, initial_seed, threshold):
    """Metricas de una replica a partir de su serie diaria."""
    N = params["poblacion"]
    I = [f[3] for f in serie]
    peak = max(I)
    peak_day = I.index(peak)
    control_day = None
    for t in range(peak_day + 1, len(I)):
        if I[t] <= threshold:
            control_day = t
            break
    S_final = serie[-1][1]
    total_infected = N - S_final          # todos los que salieron de S (incl. indice)
    return {
        "semilla_inicial": initial_seed,
        "beta": params["beta"], "p": params["probabilidad_transmision"],
        "tasa_vacunacion": params["tasa_vacunacion"],
        "efectividad": params["efectividad_vacuna"], "letalidad": params["letalidad"],
        "pico_I": peak, "dia_pico": peak_day,
        "total_infectados": total_infected,
        "tasa_ataque": total_infected / N,
        "muertes": serie[-1][5],
        "dia_control": control_day if control_day is not None else "",
        "conservacion_ok": 1,   # el assert de simular_replica ya lo garantiza
    }

def run_scenario(config, semilla_base, n_replicas, gen=None,
                       overwrite=None, verbose=True):
    """sobrescribir: dict opcional {parametro: valor} que fija parametros
    (se usa en el analisis de sensibilidad). Devuelve (resumenes, series, segundos)."""
    if gen is None:
        gen = PseudorandomGenerator(semilla_base)
    summaries, series = [], []
    t0 = time.perf_counter()
    for r in range(1, n_replicas + 1):
        initial_seed = gen.state
        params = sample_params(config, gen)
        if overwrite:
            params.update(overwrite)
        serie = simulate_epidemic(params, gen)
        summary = summarize_replica(serie, params, initial_seed, params["umbral_control"])
        summary["replica"] = r
        summaries.append(summary)
        series.append(serie)
        if verbose and (r % 10 == 0 or r == n_replicas):
            print(f"  replica {r}/{n_replicas}", flush=True)
    return summaries, series, time.perf_counter() - t0
