import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
if __package__ in (None, ""):
    script_dir = os.path.abspath(sys.path[0])
    if script_dir == BASE:
        sys.path.pop(0)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RES = os.path.join(BASE, "resultados")
GRA = os.path.join(BASE, "graficos")
os.makedirs(GRA, exist_ok=True)

ROT = {"sin_vacunacion": "No vaccination", "con_vacunacion": "Vaccination",
    "sin_vacunacion_homogenea": "No vaccination (homogeneous mixing)",
    "con_vacunacion_homogenea": "Vaccination (homogeneous mixing)"}
COL = {"S": "#1f77b4", "E": "#ff7f0e", "I": "#d62728", "R": "#2ca02c"}
NOM = {"S": "Susceptible (S)", "E": "Exposed (E)", "I": "Infected (I)",
    "R": "Removed (R)"}
plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.3,
                     "figure.dpi": 130})


def load_data(nombre):
    resumen = pd.read_csv(os.path.join(RES, f"{nombre}_resumen.csv"))
    series = pd.read_csv(os.path.join(RES, f"{nombre}_series.csv"))
    return resumen, series


def population_size(resumen):
    """Obtiene la población de los resultados, sin depender de la configuración."""
    tasa_ataque = pd.to_numeric(resumen["tasa_ataque"], errors="coerce")
    total_infectados = pd.to_numeric(resumen["total_infectados"], errors="coerce")
    poblaciones = (total_infectados / tasa_ataque).replace([np.inf, -np.inf], np.nan).dropna()
    if poblaciones.empty:
        raise ValueError("No se pudo inferir la población desde los resultados.")
    return int(round(poblaciones.median()))


def confidence_bands(series, col):
    """Matriz replica x dia -> media, IC95% de la media, percentiles 2.5-97.5."""
    m = series.pivot(index="replica", columns="dia", values=col).to_numpy(float)
    n = m.shape[0]
    media = m.mean(axis=0)
    err = 1.96 * m.std(axis=0, ddof=1) / np.sqrt(n)
    p025, p975 = np.percentile(m, [2.5, 97.5], axis=0)
    return media, media - err, media + err, p025, p975


# ------------------------------------------------------------- Fig 1-2
def plot_curves(nombre, numero):
    _, series = load_data(nombre)
    dias = np.arange(series["dia"].max() + 1)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for c in "SEIR":
        media, lo, hi, p1, p2 = confidence_bands(series, c)
        ax.fill_between(dias, p1, p2, color=COL[c], alpha=0.08)
        ax.fill_between(dias, lo, hi, color=COL[c], alpha=0.35)
        ax.plot(dias, media, color=COL[c], lw=2, label=NOM[c])
    ax.set_xlabel("Día"); ax.set_ylabel("Individuos")
    ax.set_title(f"Curva epidémica SEIR promedio – {ROT[nombre]}\n"
                 "(línea: media; banda oscura: IC 95 % de la media; banda clara: percentiles 2.5–97.5)",
                 fontsize=9.5)
    ax.legend(loc="center right")
    fig.tight_layout()
    fig.savefig(os.path.join(GRA, f"fig{numero:02d}_curva_epidemica_{nombre}.png"))
    plt.close(fig)


# ------------------------------------------------------------- Fig 3
def plot_histograms():
    metricas = [("pico_I", "Magnitud del pico (infectados activos)"),
                ("dia_pico", "Día del pico"),
                ("total_infectados", "Total de infectados"),
                ("muertes", "Muertes acumuladas"),
                ("dia_control", "Días hasta el control (I ≤ 10)")]
    fig, axs = plt.subplots(2, 5, figsize=(17, 6.2))
    for fila, nombre in enumerate(["sin_vacunacion", "con_vacunacion"]):
        resumen, _ = load_data(nombre)
        for j, (col, titulo) in enumerate(metricas):
            datos = pd.to_numeric(resumen[col], errors="coerce").dropna()
            if datos.std() == 0:   # distribucion degenerada (p. ej. 100 % de la poblacion infectada)
                axs[fila, j].bar([datos.iloc[0]], [len(datos)], width=1, color="#4c72b0")
                axs[fila, j].set_xlim(datos.iloc[0] - 5, datos.iloc[0] + 5)
                axs[fila, j].text(0.5, 0.5, f"valor constante\nen las {len(datos):,} réplicas",
                                  transform=axs[fila, j].transAxes, ha="center", fontsize=8)
            else:
                axs[fila, j].hist(datos, bins=30, color="#4c72b0", edgecolor="white")
            axs[fila, j].axvline(datos.mean(), color="red", ls="--", lw=1.3,
                                 label=f"media = {datos.mean():.0f}")
            axs[fila, j].set_title(titulo, fontsize=9)
            axs[fila, j].legend(fontsize=8)
            if j == 0:
                axs[fila, j].set_ylabel(f"{ROT[nombre]}\nFrecuencia")
    fig.suptitle("Distribuciones de resultados por réplica", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(GRA, "fig03_histogramas_resultados.png"))
    plt.close(fig)


# ------------------------------------------------------------- Fig 4
def plot_comparison():
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    colores = {"sin_vacunacion": "#d62728", "con_vacunacion": "#1f77b4"}
    for nombre in colores:
        _, series = load_data(nombre)
        dias = np.arange(series["dia"].max() + 1)
        for ax, c, tit in ((axs[0], "I", "Infectados activos I(t)"),
                           (axs[1], "S", "Susceptibles S(t)")):
            media, lo, hi, _, _ = confidence_bands(series, c)
            ax.fill_between(dias, lo, hi, color=colores[nombre], alpha=0.3)
            ax.plot(dias, media, color=colores[nombre], lw=2, label=ROT[nombre])
            ax.set_title(tit + " – media e IC 95 %")
            ax.set_xlabel("Día"); ax.set_ylabel("Individuos"); ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(GRA, "fig04_comparacion_escenarios.png"))
    plt.close(fig)


# ------------------------------------------------------------- Fig 5
def plot_tornado():
    s = pd.read_csv(os.path.join(RES, "sensibilidad.csv"))
    base = s[s["variable"] == "base"].iloc[0]
    n = population_size(load_data("con_vacunacion")[0])
    etiquetas = {"beta": "β (tasa de contacto)", "probabilidad_transmision": "p (prob. transmisión)",
                 "tasa_vacunacion": "Tasa de vacunación", "efectividad_vacuna": "Efectividad vacuna"}
    filas = []
    for v, et in etiquetas.items():
        lo = s[(s.variable == v) & (s.nivel == "min")].iloc[0]
        hi = s[(s.variable == v) & (s.nivel == "max")].iloc[0]
        filas.append((et, lo, hi))
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.4))
    for ax, col, tit, esc in ((axs[0], "media_total_infectados", "Total de infectados (% de N)", 100 / n),
                              (axs[1], "media_pico_I", "Pico de infectados activos", 1)):
        filas_o = sorted(filas, key=lambda f: abs(f[2][col] - f[1][col]))
        for k, (et, lo, hi) in enumerate(filas_o):
            b = base[col]
            ax.barh(k, (lo[col] - b) * esc, left=b * esc, color="#4c72b0", label="mínimo del rango" if k == 0 else None)
            ax.barh(k, (hi[col] - b) * esc, left=b * esc, color="#dd8452", label="máximo del rango" if k == 0 else None)
        ax.axvline(base[col] * esc, color="k", lw=1)
        ax.set_yticks(range(len(filas_o))); ax.set_yticklabels([f[0] for f in filas_o])
        ax.set_title(f"Tornado – {tit}\n(base = punto medio de cada rango: {base[col] * esc:.1f})", fontsize=10)
        ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(GRA, "fig05_sensibilidad_tornado.png"))
    plt.close(fig)


# ------------------------------------------------------------- Fig 6
def plot_correlations():
    resumen, _ = load_data("con_vacunacion")
    cols = ["beta", "p", "tasa_vacunacion", "efectividad", "letalidad"]
    etq = ["β", "p", "Tasa vacunación", "Efectividad", "Letalidad"]
    resumen = resumen.apply(pd.to_numeric, errors="coerce")
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    tablas = {}
    for ax, out, tit in ((axs[0], "total_infectados", "Total de infectados"),
                         (axs[1], "pico_I", "Pico de infectados")):
        ranked = resumen[cols + [out]].rank(method="average")
        rho = [ranked[c].corr(ranked[out]) for c in cols]
        tablas[out] = rho
        colores = ["#4c72b0" if r >= 0 else "#c44e52" for r in rho]
        ax.bar(etq, rho, color=colores)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_ylim(-1, 1); ax.set_title(f"Spearman vs {tit}\n(escenario con vacunación)")
        ax.tick_params(axis="x", rotation=20)
        for i, r in enumerate(rho):
            ax.text(i, r + (0.04 if r >= 0 else -0.09), f"{r:.2f}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(GRA, "fig06_correlaciones_spearman.png"))
    plt.close(fig)
    pd.DataFrame(tablas, index=etq).round(3).to_csv(os.path.join(RES, "correlaciones_spearman.csv"))


# ------------------------------------------------------------- Fig 7
def plot_homogeneous_comparison():
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.4))
    pares = [("sin_vacunacion", "sin_vacunacion_homogenea"),
             ("con_vacunacion", "con_vacunacion_homogenea")]
    for ax, (a, b) in zip(axs, pares):
        for nombre, color in ((a, "#4c72b0"), (b, "#dd8452")):
            resumen, _ = load_data(nombre)
            n = population_size(resumen)
            ax.hist(resumen["total_infectados"] / n * 100, bins=30, alpha=0.65,
                    color=color, label=ROT[nombre])
        ax.set_xlabel("Total de infectados (% de la población)")
        ax.set_ylabel("Frecuencia"); ax.legend(fontsize=8)
        ax.set_title("Efecto de la regla de selección del contacto")
    fig.tight_layout()
    fig.savefig(os.path.join(GRA, "fig07_extension_mezcla_homogenea.png"))
    plt.close(fig)


# ------------------------------------------------------------- Tabla
def build_statistics_table():
    filas = []
    for nombre in ROT:
        resumen, _ = load_data(nombre)
        n = len(resumen)
        for col, et in (("pico_I", "Pico de infectados"), ("dia_pico", "Día del pico"),
                        ("total_infectados", "Total de infectados"),
                        ("muertes", "Muertes"), ("dia_control", "Días hasta control")):
            d = pd.to_numeric(resumen[col], errors="coerce").dropna()
            err = 1.96 * d.std(ddof=1) / np.sqrt(len(d)) if len(d) > 1 else np.nan
            filas.append({"escenario": nombre, "variable": et, "n": len(d),
                          "media": d.mean(), "desv_est": d.std(ddof=1),
                          "IC95_inf": d.mean() - err, "IC95_sup": d.mean() + err,
                          "min": d.min(), "p25": d.quantile(.25), "mediana": d.median(),
                          "p75": d.quantile(.75), "max": d.max()})
        brote = (pd.to_numeric(resumen["tasa_ataque"], errors="coerce") >= 0.05).mean() * 100
        sin_control = pd.to_numeric(resumen["dia_control"], errors="coerce").isna().mean() * 100
        filas.append({"escenario": nombre, "variable": "% réplicas con brote mayor (>=5 % de N)",
                      "n": n, "media": brote})
        filas.append({"escenario": nombre, "variable": "% réplicas sin control en 365 días",
                      "n": n, "media": sin_control})
    df = pd.DataFrame(filas).round(2)
    df.to_csv(os.path.join(RES, "estadisticas_descriptivas.csv"), index=False)
    return df


if __name__ == "__main__":
    plot_curves("sin_vacunacion", 1)
    plot_curves("con_vacunacion", 2)
    plot_histograms()
    plot_comparison()
    plot_tornado()
    plot_correlations()
    plot_homogeneous_comparison()
    df = build_statistics_table()
    print(df.to_string())
    print("Graficos en", GRA)
