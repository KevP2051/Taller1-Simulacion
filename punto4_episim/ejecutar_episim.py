# =====================================================================
# Uso:  python ejecutar_episim.py [--replicas 1000] [--semilla 555555555]
#                                 [--rep-sensibilidad 100]
# Genera en ./resultados:
#   <escenario>_resumen.csv  (1 fila por replica)
#   <escenario>_series.csv   (1 fila por replica y dia: S,E,I,R,F)
#   sensibilidad.csv, tiempos.csv, validacion_generador.csv
# =====================================================================
import argparse
import csv
import os
import sys

try:
    import resource
except ModuleNotFoundError:
    resource = None

from motor_episim import (PseudorandomGenerator, run_scenario,
                          read_config)

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, "configuracion")
OUT = os.path.join(BASE, "resultados")

# Escenarios principales (siguen el enunciado) y extension (mezcla homogenea)
ESCENARIOS = {
    "sin_vacunacion": "config_sin_vacunacion.csv",
    "con_vacunacion": "config_con_vacunacion.csv",
    "sin_vacunacion_homogenea": "config_sin_vacunacion_homogenea.csv",
    "con_vacunacion_homogenea": "config_con_vacunacion_homogenea.csv",
}

def peak_memory_mb():
    if resource is not None:
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0  # Linux: KB -> MB
    return 0.0  # Windows no expone resource en la biblioteca estándar

def save_summary(name, summaries):
    columns = ["replica", "semilla_inicial", "beta", "p", "tasa_vacunacion",
                "efectividad", "letalidad", "pico_I", "dia_pico",
                "total_infectados", "tasa_ataque", "muertes", "dia_control",
                "conservacion_ok"]
    with open(os.path.join(OUT, f"{name}_resumen.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(summaries)

def save_series(name, series):
    with open(os.path.join(OUT, f"{name}_series.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["replica", "dia", "S", "E", "I", "R", "F"])
        for r, serie in enumerate(series, start=1):
            for row in serie:
                w.writerow((r,) + row)

def validate_generator(seed, n=100000, bins=10):
    """Chequeo rapido del flujo U(0,1): media, varianza y chi-cuadrado."""
    gen = PseudorandomGenerator(seed)
    xs = [gen.next() for _ in range(n)]
    media = sum(xs) / n
    var = sum((x - media) ** 2 for x in xs) / (n - 1)
    obs = [0] * bins
    for x in xs:
        obs[int(x * bins)] += 1
    esp = n / bins
    chi2 = sum((o - esp) ** 2 / esp for o in obs)
    # valor critico chi2(0.05, 9 gl) = 16.919
    return {"n": n, "media": media, "media_teorica": 0.5, "varianza": var,
            "varianza_teorica": 1 / 12, "chi2": chi2, "chi2_critico_0.05_9gl": 16.919,
            "pasa_chi2": int(chi2 < 16.919)}

def sensitivity_analysis(seed, n_rep):
    """Tornado (una variable a la vez). Base: punto medio de cada rango del
    escenario CON vacunacion. Cada parametro se lleva a su minimo y a su
    maximo con los demas en su punto medio."""
    cfg = read_config(os.path.join(CONFIG, ESCENARIOS["con_vacunacion"]))
    vars_ = ["beta", "probabilidad_transmision", "tasa_vacunacion", "efectividad_vacuna"]
    medios = {v: (cfg[v][0] + cfg[v][1]) / 2 for v in vars_}
    medios["letalidad"] = (cfg["letalidad"][0] + cfg["letalidad"][1]) / 2
    filas = []
    gen = PseudorandomGenerator(seed)   # una sola secuencia continua

    def run_case(etiqueta, fijos):
        res, _, _ = run_scenario(cfg, seed, n_rep, gen=gen,
                                       overwrite=fijos, verbose=False)
        n = len(res)
        return {
            "variable": etiqueta[0], "nivel": etiqueta[1],
            "valor": fijos.get(etiqueta[0], ""),
            "media_total_infectados": sum(r["total_infectados"] for r in res) / n,
            "media_pico_I": sum(r["pico_I"] for r in res) / n,
            "media_muertes": sum(r["muertes"] for r in res) / n,
            "n_replicas": n,
        }

    print("  sensibilidad: caso base...", flush=True)
    filas.append(run_case(("base", "base"), dict(medios)))
    for v in vars_:
        for nivel, idx in (("min", 0), ("max", 1)):
            print(f"  sensibilidad: {v} = {nivel}...", flush=True)
            fijos = dict(medios)
            fijos[v] = cfg[v][idx]
            filas.append(run_case((v, nivel), fijos))
    with open(os.path.join(OUT, "sensibilidad.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    return filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicas", type=int, default=1000)
    ap.add_argument("--semilla", type=int, default=555555555)
    ap.add_argument("--rep-sensibilidad", type=int, default=100)
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    print("== Validacion rapida del generador ==")
    val = validate_generator(args.semilla)
    print(val)
    with open(os.path.join(OUT, "validacion_generador.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(val.keys()))
        w.writeheader()
        w.writerow(val)

    times = []
    for name, file in ESCENARIOS.items():
        print(f"== Escenario: {name} ({args.replicas} replicas) ==")
        cfg = read_config(os.path.join(CONFIG, file))
        summaries, series, seg = run_scenario(cfg, args.semilla, args.replicas)
        save_summary(name, summaries)
        save_series(name, series)
        times.append({"escenario": name, "replicas": args.replicas,
                        "segundos": round(seg, 2),
                        "segundos_por_replica": round(seg / args.replicas, 4),
                        "memoria_pico_MB": round(peak_memory_mb(), 1)})
        print(f"   tiempo: {seg:.1f} s")

    print("== Analisis de sensibilidad ==")
    import time
    t0 = time.perf_counter()
    sensitivity_analysis(args.semilla, args.rep_sensibilidad)
    times.append({"escenario": "sensibilidad", "replicas": 9 * args.rep_sensibilidad,
                    "segundos": round(time.perf_counter() - t0, 2),
                    "segundos_por_replica": round((time.perf_counter() - t0) / (9 * args.rep_sensibilidad), 4),
                    "memoria_pico_MB": round(peak_memory_mb(), 1)})

    with open(os.path.join(OUT, "tiempos.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(times[0].keys()))
        w.writeheader()
        w.writerows(times)
    print("Listo. Resultados en", OUT)


if __name__ == "__main__":
    sys.exit(main())
