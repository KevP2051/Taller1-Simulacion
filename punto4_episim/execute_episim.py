# =====================================================================
# Uso:  python execute_episim.py [--replicas 1000] [--semilla 555555555]
#                                 [--rep-sensibilidad 100]
# =====================================================================
import argparse
import csv
import os
import sys
import time

try:
    import resource
except ModuleNotFoundError:
    resource = None

from .random import PseudorandomGenerator
from .config import read_config
from .runner import run_scenario

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, "configuracion")
OUT = os.path.join(BASE, "resultados")

ESCENARIOS = {
    "sin_vacunacion": "config_sin_vacunacion.csv",
    "con_vacunacion": "config_con_vacunacion.csv",
    "sin_vacunacion_homogenea": "config_sin_vacunacion_homogenea.csv",
    "con_vacunacion_homogenea": "config_con_vacunacion_homogenea.csv",
}

def peak_memory_mb() -> float:
    """Devuelve la memoria máxima aproximada del proceso en MB."""
    if resource is not None:
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    return 0.0

def save_summary(name: str, summaries: list[dict]) -> None:
    """Guarda el resumen de cada réplica."""
    columns = ["replica", "semilla_inicial", "beta", "p", "tasa_vacunacion",
                "efectividad", "letalidad", "pico_I", "dia_pico",
                "total_infectados", "tasa_ataque", "muertes", "dia_control",
                "conservacion_ok"]
    with open(os.path.join(OUT, f"{name}_resumen.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(summaries)

def save_series(name: str, series) -> None:
    """Guarda la serie diaria S, E, I, R, F de cada réplica."""
    with open(os.path.join(OUT, f"{name}_series.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["replica", "dia", "S", "E", "I", "R", "F"])
        for r, serie in enumerate(series, start=1):
            for row in serie:
                w.writerow((r,) + row)

def validate_generator(seed: int,n: int = 100_000,bins: int = 10,) -> dict:
    """Chequeo rapido del flujo U(0,1): media, varianza y chi-cuadrado."""
    gen = PseudorandomGenerator(seed)
    xs = [gen.next() for _ in range(n)]
    media = sum(xs) / n
    var = sum((x - media) ** 2 for x in xs) / (n - 1)
    observed = [0] * bins
    for x in xs: observed[int(x * bins)] += 1

    expected = n / bins
    chi2 = sum(
        (observed_count - expected) ** 2 / expected
        for observed_count in observed
    )
    
    critical_value = 16.919
    return {
        "n": n,
        "media": media,
        "media_teorica": 0.5,
        "varianza": var,
        "varianza_teorica": 1 / 12,
        "chi2": chi2,
        "chi2_critico_0.05_9gl": critical_value,
        "pasa_chi2": int(chi2 < critical_value),
    }
    
def save_generator_validation(seed: int) -> dict:
    """Ejecuta y guarda la validación del generador."""
    result = validate_generator(seed)

    with open(
        os.path.join(OUT, "validacion_generador.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=list(result.keys()))
        writer.writeheader()
        writer.writerow(result)

    return result

def sensitivity_analysis(seed: int, n_rep: int) -> list[dict]:
    """Análisis de sensibilidad de una variable a la vez."""
    config_path = os.path.join(CONFIG,ESCENARIOS["con_vacunacion"])
    cfg = read_config(config_path)
    variables = [
        "beta",
        "probabilidad_transmision",
        "tasa_vacunacion",
        "efectividad_vacuna",
    ]
    medios = {
        variable: (cfg[variable][0] + cfg[variable][1]) / 2
        for variable in variables
    }
    medios["letalidad"] = ( cfg["letalidad"][0] + cfg["letalidad"][1] ) / 2
    filas = []
    gen = PseudorandomGenerator(seed)

    def run_case(label: tuple[str, str], fixed_values: dict) -> dict:
        variable, nivel = label

        results, _, _ = run_scenario(
            cfg,
            seed,
            n_rep,
            gen=gen,
            overwrite=fixed_values,
            verbose=False,
        )

        n = len(results)

        return {
            "variable": variable,
            "nivel": nivel,
            "valor": fixed_values.get(variable, ""),
            "media_total_infectados": (
                sum(r["total_infectados"] for r in results) / n
            ),
            "media_pico_I": (
                sum(r["pico_I"] for r in results) / n
            ),
            "media_muertes": (
                sum(r["muertes"] for r in results) / n
            ),
            "n_replicas": n,
        }

    print("  sensibilidad: caso base...", flush=True)
    filas.append(run_case(("base", "base"), dict(medios)))

    for variable in variables:
        for nivel, index in (("min", 0), ("max", 1)):
            print(
                f"  sensibilidad: {variable} = {nivel}...",
                flush=True,
            )

            valores_fijos = dict(medios)
            valores_fijos[variable] = cfg[variable][index]

            filas.append(
                run_case(
                    (variable, nivel),
                    valores_fijos,
                )
            )

    with open(
        os.path.join(OUT, "sensibilidad.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(filas[0].keys()),
        )
        writer.writeheader()
        writer.writerows(filas)

    return filas

def save_times(times: list[dict]) -> None:
    """Guarda los tiempos y memoria de cada escenario."""
    with open(
        os.path.join(OUT, "tiempos.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(times[0].keys()),
        )
        writer.writeheader()
        writer.writerows(times)

def parse_args() -> argparse.Namespace:
    """Procesa los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Ejecuta las simulaciones Montecarlo SEIR."
    )
    parser.add_argument(
        "--replicas",
        type=int,
        default=1000,
        help="Número de réplicas por escenario.",
    )
    parser.add_argument(
        "--semilla",
        type=int,
        default=555555555,
        help="Semilla inicial del generador.",
    )
    parser.add_argument(
        "--rep-sensibilidad",
        type=int,
        default=100,
        help="Réplicas para cada caso del análisis de sensibilidad.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    os.makedirs(OUT, exist_ok=True)

    print("== Validación rápida del generador ==")
    validation = save_generator_validation(args.semilla)
    print(validation)

    times = []

    for name, filename in ESCENARIOS.items():
        print(f"== Escenario: {name} ({args.replicas} réplicas) ==")
        
        config_path = os.path.join(CONFIG, filename)
        cfg = read_config(config_path)
        summaries, series, seconds = run_scenario(
            cfg,
            args.semilla,
            args.replicas,
        )
        save_summary(name, summaries)
        save_series(name, series)
        times.append(
            {
                "escenario": name,
                "replicas": args.replicas,
                "segundos": round(seconds, 2),
                "segundos_por_replica": round(
                    seconds / args.replicas,
                    4,
                ),
                "memoria_pico_MB": round(
                    peak_memory_mb(),
                    1,
                ),
            }
        )

        print(f"   tiempo: {seconds:.1f} s")

    print("== Análisis de sensibilidad ==")
    
    start = time.perf_counter()
    sensitivity_analysis(
        args.semilla,
        args.rep_sensibilidad,
    )
    sensitivity_seconds = time.perf_counter() - start
    sensitivity_replicas = 9 * args.rep_sensibilidad
    times.append(
        {
            "escenario": "sensibilidad",
            "replicas": sensitivity_replicas,
            "segundos": round(sensitivity_seconds, 2),
            "segundos_por_replica": round(
                sensitivity_seconds / sensitivity_replicas,
                4,
            ),
            "memoria_pico_MB": round(
                peak_memory_mb(),
                1,
            ),
        }
    )

    save_times(times)
    print("Listo. Resultados en", OUT)


if __name__ == "__main__":
    sys.exit(main())
