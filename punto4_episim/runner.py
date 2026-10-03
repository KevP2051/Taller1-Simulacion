import time
from dataclasses import replace

from .config import sample_params
from .models import Config, DailyRecord, UniformSource
from .random import PseudorandomGenerator
from .simulation import simulate_epidemic


def summarize_replica(
    records: list[DailyRecord],
    params,
    initial_seed: int,
) -> dict:
    """Calcula las métricas finales de una réplica."""
    infected = [record.I for record in records]
    peak = max(infected)
    peak_day = infected.index(peak)

    control_day = next(
        (
            t
            for t in range(peak_day + 1, len(infected))
            if infected[t] <= params.umbral_control
        ),
        None,
    )

    total_infected = params.poblacion - records[-1].S

    return {
        "semilla_inicial": initial_seed,
        "beta": params.beta,
        "p": params.probabilidad_transmision,
        "tasa_vacunacion": params.tasa_vacunacion,
        "efectividad": params.efectividad_vacuna,
        "letalidad": params.letalidad,
        "pico_I": peak,
        "dia_pico": peak_day,
        "total_infectados": total_infected,
        "tasa_ataque": total_infected / params.poblacion,
        "muertes": records[-1].F,
        "dia_control": control_day if control_day is not None else "",
        "conservacion_ok": 1,
    }


def run_scenario(
    config: Config,
    semilla_base: int,
    n_replicas: int,
    gen: UniformSource | None = None,
    overwrite: dict[str, float] | None = None,
    verbose: bool = True,
) -> tuple[list[dict], list[list[DailyRecord]], float]:
    """Ejecuta varias réplicas sobre una secuencia continua del generador."""
    if gen is None:
        gen = PseudorandomGenerator(semilla_base)

    summaries: list[dict] = []
    all_series: list[list[DailyRecord]] = []

    start = time.perf_counter()

    for replica in range(1, n_replicas + 1):
        initial_seed = gen.state
        params = sample_params(config, gen)

        if overwrite:
            params = replace(params, **overwrite)

        records = simulate_epidemic(params, gen)
        summary = summarize_replica(records, params, initial_seed)
        summary["replica"] = replica

        summaries.append(summary)
        all_series.append(records)

        if verbose and (replica % 10 == 0 or replica == n_replicas):
            print(f"  replica {replica}/{n_replicas}", flush=True)

    return summaries, all_series, time.perf_counter() - start
