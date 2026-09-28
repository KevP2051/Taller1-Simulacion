import math
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from punto2_caminata_aleatoria import caminata
from punto3_generadores_pseudoaleatorios import inicializacion

PASOS = 1_000_000
REPLICAS = 100
SEMILLA_BASE = 12345           
SALTO_ENTRE_SEMILLAS = 104729  

CARPETA_RESULTADOS = Path(__file__).parent / "resultados"
ARCHIVO_SEMILLAS = Path(__file__).parent / "semillas_caminata.csv"
ARCHIVO_CONTADOR = Path(__file__).parent / "contador_semillas.txt"

FUNCIONES = {1: caminata.caminata_1d, 2: caminata.caminata_2d, 3: caminata.caminata_3d}


def semilla_nueva(filas):
    """Semilla generada con el congruencial multiplicativo del punto 3."""
    contador = 0
    if ARCHIVO_CONTADOR.exists():
        contador = int(ARCHIVO_CONTADOR.read_text().strip() or 0)
    contador += 1
    ARCHIVO_CONTADOR.write_text(str(contador))
    base = filas[0]["semilla"] if filas else 12345
    secuencia = caminata.generadores.generar_congruencial_multiplicativo(
        base, caminata.MULTIPLICADOR, caminata.MODULO, contador
    )
    return secuencia["valores_x"][-1]   


def elegir_semilla():
    filas, errores = inicializacion.leer_archivo_de_semillas(ARCHIVO_SEMILLAS)
    for error in errores:
        print("Aviso en el archivo de semillas:", error)
    print("Semillas disponibles:")
    for numero, fila in enumerate(filas, start=1):
        print(f"  {numero}. {fila['semilla']}")
    print("  0. Semilla nueva (generada con el congruencial del punto 3)")
    opcion = input("Elija una opción: ").strip()
    if opcion.isdigit() and 1 <= int(opcion) <= len(filas):
        return filas[int(opcion) - 1]["semilla"]
    return semilla_nueva(filas)


def ejecutar_replicas(dimension):
    funcion = FUNCIONES[dimension]
    posiciones_finales = []
    retornos = 0
    inicio = time.perf_counter()
    for i in range(REPLICAS):
        semilla = SEMILLA_BASE + i * SALTO_ENTRE_SEMILLAS
        posicion, retorno = funcion(semilla, PASOS)
        posiciones_finales.append(posicion)
        if retorno:
            retornos += 1
        print(f"  {dimension}D réplica {i + 1}/{REPLICAS}", end="\r")
    tiempo = time.perf_counter() - inicio
    print()
    return posiciones_finales, retornos / REPLICAS, tiempo


def medir_memoria(dimension):
    tracemalloc.start()
    FUNCIONES[dimension](SEMILLA_BASE, PASOS)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pico / 1024 / 1024  


def graficar_histograma_1d(posiciones):
    valores = [p[0] for p in posiciones]
    media = sum(valores) / len(valores)
    desviacion = math.sqrt(sum((v - media) ** 2 for v in valores) / (len(valores) - 1))
    dentro = sum(1 for v in valores if abs(v) <= math.sqrt(PASOS)) / len(valores)
    print(f"1D -> media = {media:.2f} (teórica 0), desviación = {desviacion:.2f} (teórica {math.sqrt(PASOS):.0f})")
    print(f"1D -> dentro de ±1σ: {dentro:.2%} (teórico 68.27%)")

    plt.figure(figsize=(8, 5))
    plt.hist(valores, bins=15, density=True, edgecolor="black", label="Posiciones finales")
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


def graficar_2d(posiciones):
    lista_x, lista_y, _ = caminata.trayectoria(2, SEMILLA_BASE, 10000)
    plt.figure(figsize=(6, 6))
    plt.plot(lista_x, lista_y, linewidth=0.5)
    plt.scatter([0], [0], color="green", label="Origen")
    plt.scatter([lista_x[-1]], [lista_y[-1]], color="red", label="Final")
    plt.title("Caminata 2D (10.000 pasos)")
    plt.legend()
    plt.savefig(CARPETA_RESULTADOS / "trayectoria_2d.png", dpi=150, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(6, 6))
    plt.scatter([p[0] for p in posiciones], [p[1] for p in posiciones], s=15)
    plt.title(f"Posiciones finales 2D ({REPLICAS} réplicas)")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.savefig(CARPETA_RESULTADOS / "posiciones_finales_2d.png", dpi=150, bbox_inches="tight")
    plt.close()


def graficar_3d():
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


def main():
    global SEMILLA_BASE
    SEMILLA_BASE = elegir_semilla()
    CARPETA_RESULTADOS.mkdir(exist_ok=True)
    print(f"Semilla base: {SEMILLA_BASE}")
    (CARPETA_RESULTADOS / "semilla_usada.txt").write_text(f"Semilla base: {SEMILLA_BASE}\n")

    print("Probabilidad exacta de retorno (1D):")
    for n in (2, 3, 4):
        print(f"  P(S_{n} = 0) = {caminata.probabilidad_exacta_retorno(n)}")

    tabla = []
    for dimension in (1, 2, 3):
        print(f"\nSimulando {dimension}D...")
        posiciones, prob_retorno, tiempo = ejecutar_replicas(dimension)
        memoria = medir_memoria(dimension)
        tabla.append((dimension, tiempo, memoria, prob_retorno))
        if dimension == 1:
            graficar_histograma_1d(posiciones)
        elif dimension == 2:
            graficar_2d(posiciones)
        else:
            graficar_3d()

    print("\nDimensión | Tiempo (s) | Memoria pico (MB) | P(retorno en 1000 pasos)")
    for dimension, tiempo, memoria, prob in tabla:
        print(f"{dimension}D        | {tiempo:10.1f} | {memoria:17.1f} | {prob:.2f}")
    print(f"\nImágenes guardadas en: {CARPETA_RESULTADOS}")


if __name__ == "__main__":
    main()