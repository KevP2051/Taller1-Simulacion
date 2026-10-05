# =====================================================================
# Uso:  python execute_episim.py [--replicas 1000] [--semilla 555555555]
#                                 [--rep-sensibilidad 100]
# =====================================================================
import argparse
import csv
import ctypes
import os
import sys
import tracemalloc
import time

try:
    import resource
except ModuleNotFoundError:
    resource = None

from .random import PseudorandomGenerator
from .config import read_config
from .runner import run_scenario
from punto3_generadores_pseudoaleatorios import pruebas

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, "configuracion")
OUT = os.path.join(BASE, "resultados")

ESCENARIOS = {
    "sin_vacunacion": "config_sin_vacunacion.csv",
    "con_vacunacion": "config_con_vacunacion.csv",
    "sin_vacunacion_homogenea": "config_sin_vacunacion_homogenea.csv",
    "con_vacunacion_homogenea": "config_con_vacunacion_homogenea.csv",
}

class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("page_fault_count", ctypes.c_ulong),
        ("memory_values", ctypes.c_size_t * 8),
    ]

def _windows_peak_memory_mb() -> float:
    """Devuelve el pico de memoria residente del proceso en Windows."""
    counters = _ProcessMemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    get_process = ctypes.windll.kernel32.GetCurrentProcess
    get_process.restype = ctypes.c_void_p
    get_memory_info = ctypes.windll.psapi.GetProcessMemoryInfo
    get_memory_info.argtypes = (
        ctypes.c_void_p,
        ctypes.POINTER(_ProcessMemoryCounters),
        ctypes.c_ulong,
    )
    get_memory_info.restype = ctypes.c_bool
    if not get_memory_info(get_process(),
                           ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()

    return counters.memory_values[0] / (1024.0 ** 2)

def peak_memory_mb() -> float:
    """Devuelve la memoria máxima aproximada del proceso en MB."""
    if sys.platform == "win32":
        return _windows_peak_memory_mb()
    elif resource is not None:
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak / (1024.0 ** 2) if sys.platform == "darwin" else peak / 1024.0
    else:
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        _, peak_bytes = tracemalloc.get_traced_memory()
        return peak_bytes / (1024.0 ** 2)

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

def validate_generator(
    seed: int,
    n: int = 100_000,
    bins: int = 10,
) -> list[dict]:
    """Valida el generador con las pruebas del punto 3."""
    gen = PseudorandomGenerator(seed)
    numbers = [gen.next() for _ in range(n)]
    tests = (
        pruebas.prueba_de_medias(numbers),
        pruebas.prueba_de_varianza(numbers),
        pruebas.prueba_chi_cuadrado(numbers, bins),
        pruebas.prueba_kolmogorov_smirnov(numbers, bins),
        pruebas.prueba_de_poker(numbers),
    )
    return [{
        "n": n,
        "prueba": result["prueba"],
        "estadistico": result["estadistico"],
        "valor_critico": result["valor_critico"],
        "pasa": int(result["pasa"]),
        "avisos": " | ".join(result["avisos"]),
    } for result in tests]
    
def save_generator_validation(seed: int) -> list[dict]:
    """Ejecuta y guarda los resultados de la validación del generador."""
    result = validate_generator(seed)

    with open(
        os.path.join(OUT, "validacion_generador.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(f, fieldnames=list(result[0].keys()))
        writer.writeheader()
        writer.writerows(result)

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
