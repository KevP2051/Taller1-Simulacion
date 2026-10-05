import math
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from punto2_caminata_aleatoria import caminata
from punto3_generadores_pseudoaleatorios import inicializacion, pruebas

PASOS = 1_000_000
REPLICAS = 100
SEMILLA_BASE = 12345   
SEMILLAS = []          

CARPETA_RESULTADOS = Path(__file__).parent / "resultados"
ARCHIVO_SEMILLAS = Path(__file__).parent / "semillas_caminata.csv"

# Dimensión -> función que simula una réplica
FUNCIONES = {1: caminata.caminata_1d, 2: caminata.caminata_2d, 3: caminata.caminata_3d}


def elegir_semillas():
    """Menú de 2 opciones: las 100 semillas del CSV o una semilla tomada del reloj (time)."""
    while True:
        print("Origen de las semillas:")
        print(f"  1. Las {REPLICAS} semillas del archivo semillas_caminata.csv")
        print("  2. Semilla generada con la librería time (las réplicas se encadenan a partir de ella)")
        opcion = input("Elija una opción (1 o 2): ").strip()
        if opcion == "1":
            filas, errores = inicializacion.leer_archivo_de_semillas(ARCHIVO_SEMILLAS)
            for error in errores:
                print("Aviso en el archivo de semillas:", error)
            if len(filas) < REPLICAS:
                print(f"El archivo tiene {len(filas)} semillas válidas y se necesitan {REPLICAS}.")
                continue
            # Solo se usa la columna semilla de las primeras REPLICAS filas
            return [fila["semilla"] for fila in filas[:REPLICAS]]
        if opcion == "2":
            # Semilla base del reloj, reducida al rango [1, m - 1]
            base = time.time_ns() % (caminata.MODULO - 1) + 1
            print(f"Semilla por tiempo: {base}. Encadenando las {REPLICAS} semillas (unos segundos)...")
            return caminata.encadenar_semillas(base, REPLICAS, PASOS)
        print("Opción no válida.")


def validar_generador(semilla):
    # Pruebas del Punto 3 sobre los números de la primera réplica, antes de simular
    numeros_r = caminata.generar_numeros(semilla, PASOS)
    intervalos = pruebas.cantidad_de_intervalos_por_defecto(len(numeros_r))
    resultados = [
        pruebas.prueba_de_medias(numeros_r),
        pruebas.prueba_de_varianza(numeros_r),
        pruebas.prueba_chi_cuadrado(numeros_r, intervalos),
        pruebas.prueba_kolmogorov_smirnov(numeros_r, intervalos),
        pruebas.prueba_de_poker(numeros_r),
    ]
    print(f"Validación del generador (semilla {semilla}, {PASOS:,} números):")
    for resultado in resultados:
        print(f"  {resultado['prueba']:<20} estadístico = {resultado['estadistico']:<12} {'PASA' if resultado['pasa'] else 'NO PASA'}")


def ejecutar_replicas(dimension):
    funcion = FUNCIONES[dimension]
    posiciones_finales = []
    retornos = 0
    inicio = time.perf_counter()
    for i in range(REPLICAS):
        # Cada réplica usa su propia semilla
        posicion, retorno = funcion(SEMILLAS[i], PASOS)
        posiciones_finales.append(posicion)
        if retorno:
            retornos += 1
        print(f"  {dimension}D réplica {i + 1}/{REPLICAS}", end="\r")
    tiempo = time.perf_counter() - inicio
    print()
    # Posiciones finales, probabilidad estimada de retorno y tiempo en segundos
    return posiciones_finales, retornos / REPLICAS, tiempo


def medir_memoria(dimension):
    # Pico de memoria (MB) de una sola réplica
    tracemalloc.start()
    FUNCIONES[dimension](SEMILLA_BASE, PASOS)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pico / 1024 / 1024


def graficar_histograma_1d(posiciones):
    valores = [p[0] for p in posiciones]
    media = sum(valores) / len(valores)
    # Desviación muestral (n - 1) y proporción dentro de ±1σ, para compararlas con la teoría
    desviacion = math.sqrt(sum((v - media) ** 2 for v in valores) / (len(valores) - 1))
    dentro = sum(1 for v in valores if abs(v) <= math.sqrt(PASOS)) / len(valores)
    print(f"1D -> media = {media:.2f} (teórica 0), desviación = {desviacion:.2f} (teórica {math.sqrt(PASOS):.0f})")
    print(f"1D -> dentro de ±1σ: {dentro:.2%} (teórico 68.27%)")

    plt.figure(figsize=(8, 5))
    plt.hist(valores, bins=15, density=True, edgecolor="black", label="Posiciones finales")
    # Densidad teórica N(0, n) entre -4σ y 4σ
    sigma = math.sqrt(PASOS)
    xs = [-4 * sigma + i * (8 * sigma) / 200 for i in range(201)]
    ys = [math.exp(-x * x / (2 * PASOS)) / math.sqrt(2 * math.pi * PASOS) for x in xs]
    plt.plot(xs, ys, color="red", label="Normal N(0, n)")
    plt.title(f"Caminata 1D: posición final tras {PASOS:,} pasos ({REPLICAS} réplicas)")
    plt.xlabel("Posición final")
    plt.ylabel("Densidad")
    plt.legend()
    plt.savefig(CARPETA_RESULTADOS / "histograma_1d.png", dpi=150, bbox_inches="tight")
    plt.close()


def graficar_trayectoria_1d():
    # Trayectoria corta (10.000 pasos) con la semilla base
    lista_x, _, _ = caminata.trayectoria(1, SEMILLA_BASE, 10000)
    plt.figure(figsize=(9, 4.5))
    plt.plot(range(len(lista_x)), lista_x, linewidth=0.6)
    plt.axhline(0, color="gray", linestyle="--", linewidth=0.8)
    plt.scatter([0], [0], color="green", zorder=3, label="Origen")
    plt.scatter([len(lista_x) - 1], [lista_x[-1]], color="red", zorder=3, label="Final")
    plt.title("Caminata 1D (10.000 pasos)")
    plt.xlabel("Paso")
    plt.ylabel("Posición de la rana")
    plt.legend()
    plt.savefig(CARPETA_RESULTADOS / "trayectoria_1d.png", dpi=150, bbox_inches="tight")
    plt.close()


def graficar_2d(posiciones):
    # Figura 1: trayectoria de 10.000 pasos
    lista_x, lista_y, _ = caminata.trayectoria(2, SEMILLA_BASE, 10000)
    plt.figure(figsize=(6, 6))
    plt.plot(lista_x, lista_y, linewidth=0.5)
    plt.scatter([0], [0], color="green", label="Origen")
    plt.scatter([lista_x[-1]], [lista_y[-1]], color="red", label="Final")
    plt.title("Caminata 2D (10.000 pasos)")
    plt.legend()
    plt.savefig(CARPETA_RESULTADOS / "trayectoria_2d.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Figura 2: dispersión de las posiciones finales
    plt.figure(figsize=(6, 6))
    plt.scatter([p[0] for p in posiciones], [p[1] for p in posiciones], s=15)
    plt.title(f"Posiciones finales 2D ({REPLICAS} réplicas)")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.savefig(CARPETA_RESULTADOS / "posiciones_finales_2d.png", dpi=150, bbox_inches="tight")
    plt.close()


def graficar_3d(posiciones):
    # Figura 1: trayectoria de 10.000 pasos
    lista_x, lista_y, lista_z = caminata.trayectoria(3, SEMILLA_BASE, 10000)
    figura = plt.figure(figsize=(8, 7))
    eje = figura.add_subplot(projection="3d")
    eje.plot(lista_x, lista_y, lista_z, linewidth=0.5)
    eje.scatter([0], [0], [0], color="green", s=60, label="Origen")
    eje.scatter([lista_x[-1]], [lista_y[-1]], [lista_z[-1]], color="red", s=60, label="Final")
    eje.set_title("Caminata 3D (10.000 pasos)")
    eje.set_xlabel("x")
    eje.set_ylabel("y")
    eje.set_zlabel("z")
    eje.legend()
    plt.savefig(CARPETA_RESULTADOS / "trayectoria_3d.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Figura 2: posiciones finales en 3D y sus proyecciones ortogonales (xy, xz, yz)
    xs = [p[0] for p in posiciones]
    ys = [p[1] for p in posiciones]
    zs = [p[2] for p in posiciones]
    figura = plt.figure(figsize=(11, 10))
    eje = figura.add_subplot(2, 2, 1, projection="3d")
    eje.scatter(xs, ys, zs, s=15)
    eje.scatter([0], [0], [0], color="green", s=60, label="Origen")
    eje.set_title("Scatter 3D")
    eje.set_xlabel("x")
    eje.set_ylabel("y")
    eje.set_zlabel("z")
    eje.legend()
    # En las proyecciones se pierde un eje, pero se leen las distancias sin la distorsión de la perspectiva
    for posicion, (horizontal, vertical, nombre_h, nombre_v) in enumerate(
        [(xs, ys, "x", "y"), (xs, zs, "x", "z"), (ys, zs, "y", "z")], start=2
    ):
        eje = figura.add_subplot(2, 2, posicion)
        eje.scatter(horizontal, vertical, s=15)
        eje.scatter([0], [0], color="green", s=40)
        eje.set_title(f"Proyección {nombre_h}{nombre_v}")
        eje.set_xlabel(nombre_h)
        eje.set_ylabel(nombre_v)
        eje.set_aspect("equal", adjustable="datalim")
    figura.suptitle(f"Posiciones finales 3D ({REPLICAS} réplicas)")
    plt.savefig(CARPETA_RESULTADOS / "posiciones_finales_3d.png", dpi=150, bbox_inches="tight")
    plt.close()


def main():
    global SEMILLAS, SEMILLA_BASE
    SEMILLAS = elegir_semillas()
    SEMILLA_BASE = SEMILLAS[0]
    CARPETA_RESULTADOS.mkdir(exist_ok=True)
    print(f"Semilla base: {SEMILLA_BASE}")
    validar_generador(SEMILLA_BASE)
    # Se guardan las semillas para poder reproducir la corrida
    (CARPETA_RESULTADOS / "semilla_usada.txt").write_text(
        f"Semilla base: {SEMILLA_BASE}\nSemillas de las réplicas:\n" + "\n".join(str(s) for s in SEMILLAS) + "\n",
        encoding="utf-8",
    )

    # Probabilidad exacta de retorno 1D: debe dar 0.5, 0.0 y 0.375
    print("Probabilidad exacta de retorno (1D):")
    for n in (2, 3, 4):
        print(f"  P(S_{n} = 0) = {caminata.probabilidad_exacta_retorno(n)}")

    # Filas del cuadro de eficiencia: (dimensión, tiempo, memoria, probabilidad de retorno)
    tabla = []
    for dimension in (1, 2, 3):
        print(f"\nSimulando {dimension}D...")
        posiciones, prob_retorno, tiempo = ejecutar_replicas(dimension)
        memoria = medir_memoria(dimension)
        tabla.append((dimension, tiempo, memoria, prob_retorno))
        if dimension == 1:
            graficar_histograma_1d(posiciones)
            graficar_trayectoria_1d()
        elif dimension == 2:
            graficar_2d(posiciones)
        else:
            graficar_3d(posiciones)

    print("\nDimensión | Tiempo (s) | Memoria pico (MB) | P(retorno en 1000 pasos)")
    for dimension, tiempo, memoria, prob in tabla:
        print(f"{dimension}D        | {tiempo:10.1f} | {memoria:17.1f} | {prob:.2f}")
    print(f"\nImágenes guardadas en: {CARPETA_RESULTADOS}")


if __name__ == "__main__":
    main()