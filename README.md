# Taller Primer 50 %: Simulación por Computador

Universidad Pedagógica y Tecnológica de Colombia, código de curso 8108278.
Números pseudoaleatorios, caminatas aleatorias y método Montecarlo.

Este repositorio contiene el código de los puntos 2, 3 y 4 del taller; el punto 1
corresponde a la presentación del informe.

## Autores

- Andrés Felipe Melo Avellaneda
- Miguel Leonardo Avila Avila
- Sebastian Niño Niño
- Wilson Javier Soledad Martinez
- Kevin Johann Jimenez Poveda

Docente: Alex Puertas Gonzalez.

## Estructura

| Carpeta | Contenido | Sección del informe |
|---------|-----------|---------------------|
| [`punto2_caminata_aleatoria/`](punto2_caminata_aleatoria/) | Simulación de caminatas aleatorias en 1D, 2D y 3D (la rana estadística) | 2 |
| [`punto3_generadores_pseudoaleatorios/`](punto3_generadores_pseudoaleatorios/) | Generadores y validadores de números pseudoaleatorios | 3 |
| [`punto4_episim/`](punto4_episim/) | Simulación Montecarlo de propagación de enfermedades contagiosas | 4 |

Cada carpeta tiene su propio `README.md`, con el detalle de uso, archivos, funciones,
resultados y equipo de ejecución. La declaración de uso de herramientas de inteligencia
artificial está en el Anexo A del informe.

## Origen de la aleatoriedad

Ningún programa usa `random`, `numpy.random` ni otra biblioteca de números aleatorios:
todos los números pseudoaleatorios salen de los generadores del punto 3, implementados
desde cero. Por eso las tres carpetas deben conservarse juntas.

| Punto | Generador del punto 3 | Parámetros |
|---|---|---|
| 2 | Congruencial multiplicativo | a = 16807, m = 2³¹ − 1 |
| 4 | Congruencial lineal | a = 1664525, c = 1013904223, m = 2³² |

El reloj del sistema solo se usa, de forma opcional, para fijar la semilla base del
punto 2. `numpy` y `pandas` intervienen únicamente en el análisis del punto 4, sobre
resultados ya simulados.

El punto 3 incluye los generadores de cuadrados medios, congruencial lineal y
congruencial multiplicativo, las transformaciones uniforme y normal, y las pruebas de
medias, varianza, chi-cuadrado, Kolmogorov-Smirnov y póker. Por indicación del docente
no se implementan la prueba de rachas ni el generador congruencial aditivo.

## Requisitos

- Python 3.10 o superior.
- `matplotlib` para los gráficos de los tres puntos; `numpy` y `pandas` para el análisis
  del punto 4.
- `tkinter` para la ventana del punto 3 (viene incluido en el instalador de Python para
  Windows).

```bash
python -m pip install matplotlib numpy pandas
```

## Ejecución

Los programas se ejecutan desde la carpeta raíz del repositorio, como módulos:

| Punto | Comando | Qué hace |
|---|---|---|
| 2 | `python -m punto2_caminata_aleatoria.programa_principal` | Valida el generador y simula 100 réplicas de 1.000.000 de pasos en 1D, 2D y 3D |
| 3 | `python -m punto3_generadores_pseudoaleatorios.programa_principal` | Abre la ventana para generar secuencias y aplicarles las pruebas |
| 4 | `python -m punto4_episim.execute_episim` | Simula los cuatro escenarios y el análisis de sensibilidad |
| 4 | `python -m punto4_episim.analisis_episim` | Genera los gráficos y las tablas a partir de los resultados del comando anterior |

Los programas de los puntos 3 y 4 no funcionan si se ejecutan directamente desde su
carpeta (por ejemplo, `python programa_principal.py`), porque importan los paquetes desde
la raíz.


```bash
python -m punto4_episim.execute_episim --replicas 20 --rep-sensibilidad 5
python -m punto4_episim.analisis_episim
```

Esta prueba sobrescribe los archivos de `punto4_episim/resultados/` y
`punto4_episim/graficos/`; para recuperar los de 1.000 réplicas hay que repetir los dos
comandos sin argumentos.

## Reproducibilidad

- **Punto 2:** puede usar las 100 semillas de `semillas_caminata.csv` o una semilla base
  tomada del reloj; en ambos casos guarda las semillas de la ejecución en
  `resultados/semilla_usada.txt`.
- **Punto 3:** `semillas_ejemplo.csv` contiene los cuatro generadores evaluados en el
  informe (G1 a G4).
- **Punto 4:** la semilla base por defecto es 555555555. Con ella, los resultados por
  réplica se reproducen de forma exacta en los equipos en que se probó; solo cambian los tiempos.

## Salidas

| Punto | Dónde quedan |
|---|---|
| 2 | `punto2_caminata_aleatoria/resultados/`: gráficos y semillas de la última ejecución |
| 3 | tablas y gráficos que se exportan desde la ventana |
| 4 | `punto4_episim/resultados/` (archivos CSV) y `punto4_episim/graficos/` (figuras) |