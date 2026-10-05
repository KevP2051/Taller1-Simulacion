# Punto 2: La rana estadística, caminatas aleatorias en 1D, 2D y 3D

Simulación de una caminata aleatoria simétrica sobre la recta, el plano y el espacio,
con 100 réplicas independientes de 1.000.000 de pasos en cada dimensión. Los números
pseudoaleatorios provienen del generador congruencial multiplicativo del punto 3
(`punto3_generadores_pseudoaleatorios`); no se usa `random` ni `numpy.random`.

## Requisitos

- Python 3.10 o superior.
- `matplotlib` 3.5 o superior, para los gráficos.
- El paquete del punto 3 debe estar disponible desde la raíz del repositorio.

```bash
python -m pip install matplotlib
```

### Equipo de desarrollo y pruebas

| Elemento | Especificación |
|---|---|
| Lenguaje | Python 3.14.0 (matplotlib 3.10.8) |
| Sistema operativo | Windows 11 Pro 64 bits (versión 10.0.26200) |
| Procesador | AMD Ryzen 7 5800XT, 8 núcleos y 16 hilos |
| Memoria RAM | 16 GB |

## Uso

El programa se ejecuta desde la carpeta raíz del taller:

```bash
python -m punto2_caminata_aleatoria.programa_principal
```

Al iniciar se elige el origen de las semillas:

1. **Archivo `semillas_caminata.csv`:** se usan las 100 semillas del archivo, una por
   réplica. Para cambiar las semillas basta con editar la columna `semilla`.
2. **Semilla por tiempo:** se toma una semilla del reloj (`time.time_ns()`) y las 100
   semillas se encadenan a partir de ella (ver *Independencia de las réplicas*).

Después el programa, sin más intervención:

1. Valida el generador con las pruebas del punto 3 sobre los 1.000.000 de números de la
   primera réplica.
2. Muestra la probabilidad exacta de retorno al origen en 1D tras 2, 3 y 4 saltos.
3. Simula las 100 réplicas en 1D, 2D y 3D, mide tiempo y memoria y genera los gráficos.
4. Imprime el cuadro comparativo de eficiencia.

La ejecución completa tarda alrededor de tres minutos.

### Archivo de semillas

`semillas_caminata.csv` usa el mismo formato del punto 3 y se lee con su función
`leer_archivo_de_semillas`, que valida cada fila:

```
metodo,semilla,digitos,a,c,m,cantidad
congruencial_multiplicativo,12345,,16807,,2147483647,1000000
congruencial_multiplicativo,315789130,,16807,,2147483647,1000000
```

Las semillas del archivo están encadenadas: cada una es el estado del generador después
de los 1.000.000 de números de la anterior.

## Archivos

| Archivo | Contenido |
|---|---|
| `caminata.py` | modelo de la caminata: generación de números, simulación en 1D, 2D y 3D, trayectorias y probabilidad exacta |
| `programa_principal.py` | menú de semillas, validación del generador, réplicas, medición de eficiencia y gráficos |
| `semillas_caminata.csv` | las 100 semillas de las réplicas |
| `resultados/` | gráficos y semillas de la última ejecución |

## Modelo

### Generador

Congruencial multiplicativo del punto 3, X(i+1) = (16807·X(i)) mod (2³¹ − 1), el
generador "estándar mínimo" de Park y Miller. Como m es primo y 16807 es raíz primitiva
de m, el período es m − 1 = 2.147.483.646. Cada réplica consume 1.000.000 de números, así
que las 100 réplicas usan menos del 5 % del período.

### Variables de estado y eventos

- **Estado:** la posición de la rana, (x) en 1D, (x, y) en 2D y (x, y, z) en 3D. Empieza
  en el origen.
- **Evento:** un salto de una unidad por paso, a lo largo de un eje, en una dirección
  elegida con igual probabilidad.
- **Parámetros:** pasos por réplica (1.000.000), réplicas (100) y pasos para el retorno
  (1.000).

### Regla de cada salto

Cada número R en [0, 1) decide un salto:

| Dimensión | Direcciones | Regla |
|---|---|---|
| 1D | 2 (±x) | R < 0.5 → +1; si no, −1 |
| 2D | 4 (±x, ±y) | dirección = piso(4·R) |
| 3D | 6 (±x, ±y, ±z) | dirección = piso(6·R) |

Cada dirección tiene probabilidad 1/2, 1/4 o 1/6, según la dimensión.

### Retorno al origen

Una réplica cuenta como retorno si la rana pasa por el origen al menos una vez en los
primeros 1.000 pasos. La probabilidad estimada es la proporción de réplicas con retorno.

En 1D, la probabilidad exacta de estar en el origen tras n pasos es
P(S_n = 0) = C(n, n/2) / 2ⁿ si n es par y 0 si n es impar, porque se necesitan tantos
pasos a la derecha como a la izquierda. Para n = 2, 3 y 4 da 0.5, 0 y 0.375.

### Posición final y Teorema Central del Límite

La posición final en 1D es la suma de 1.000.000 de saltos independientes de media 0 y
varianza 1. Por el Teorema Central del Límite se aproxima a una normal N(0, n), con
desviación √n = 1000. El programa compara la media y la desviación de las 100 posiciones
finales con esos valores y cuenta cuántas quedan dentro de ±1σ (se espera el 68.27 %).

### Independencia de las réplicas

Cada réplica empieza donde terminó la anterior: su semilla es el último X de la réplica
previa. Así ninguna réplica repite números de otra. La función `encadenar_semillas`
calcula esas semillas a partir de una semilla base; las del archivo CSV se generaron de
la misma forma.

## Salidas

### Consola

- Resultado de las pruebas de medias, varianza, chi-cuadrado, Kolmogorov-Smirnov y póker.
- Probabilidad exacta de retorno en 1D para 2, 3 y 4 saltos.
- Media, desviación y proporción dentro de ±1σ de las posiciones finales en 1D.
- Cuadro de eficiencia: tiempo de las 100 réplicas, memoria pico de una réplica y
  probabilidad estimada de retorno, por dimensión.

### `resultados/`

| Archivo | Contenido |
|---|---|
| `histograma_1d.png` | histograma de las posiciones finales en 1D con la densidad N(0, n) |
| `trayectoria_1d.png` | posición contra paso de una caminata de 10.000 pasos |
| `trayectoria_2d.png` | recorrido de una caminata de 10.000 pasos en el plano |
| `posiciones_finales_2d.png` | dispersión (scatter) de las 100 posiciones finales en 2D |
| `trayectoria_3d.png` | recorrido de una caminata de 10.000 pasos en el espacio |
| `posiciones_finales_3d.png` | scatter 3D de las posiciones finales y sus proyecciones xy, xz e yz |
| `semilla_usada.txt` | semilla base y las 100 semillas de la ejecución, para reproducirla |

### Elección de los gráficos

- **1D:** el histograma muestra la forma de la distribución de las posiciones finales y
  permite compararla con la normal teórica.
- **2D:** el scatter muestra cómo se reparten las posiciones finales en el plano, sin
  dirección preferida; la trayectoria muestra el recorrido de una sola rana.
- **3D:** el scatter 3D da la imagen general, pero la perspectiva distorsiona las
  distancias; las proyecciones ortogonales permiten leerlas en cada par de ejes.

## Funciones

### caminata.py

| Función | Descripción | Parámetros | Retorno |
|---|---|---|---|
| `generar_numeros` | Pide al punto 3 los números R del congruencial multiplicativo | `semilla`, `cantidad` | lista de R en [0, 1) |
| `caminata_1d` | Simula una réplica en la recta | `semilla`, `pasos` | ((x,), retorno) |
| `caminata_2d` | Simula una réplica en el plano | `semilla`, `pasos` | ((x, y), retorno) |
| `caminata_3d` | Simula una réplica en el espacio | `semilla`, `pasos` | ((x, y, z), retorno) |
| `trayectoria` | Guarda todo el recorrido de una caminata corta para graficarla | `dimension`, `semilla`, `pasos` | listas x, y, z |
| `probabilidad_exacta_retorno` | Calcula P(S_n = 0) en 1D | `n` | probabilidad |
| `encadenar_semillas` | Calcula semillas consecutivas que no se solapan | `semilla_inicial`, `cantidad_de_semillas`, `pasos` | lista de semillas |

`retorno` es `True` si la rana pasó por el origen en los primeros 1.000 pasos.

### programa_principal.py

| Función | Descripción |
|---|---|
| `main` | Coordina toda la ejecución |
| `elegir_semillas` | Muestra el menú y devuelve las 100 semillas (archivo o reloj) |
| `validar_generador` | Corre las pruebas del punto 3 sobre los números de la primera réplica |
| `ejecutar_replicas` | Simula las 100 réplicas de una dimensión y mide su tiempo |
| `medir_memoria` | Mide con `tracemalloc` la memoria pico de una réplica |
| `graficar_histograma_1d` | Calcula media y desviación en 1D y guarda el histograma |
| `graficar_trayectoria_1d` | Guarda la trayectoria de 10.000 pasos en 1D |
| `graficar_2d` | Guarda la trayectoria y el scatter de posiciones finales en 2D |
| `graficar_3d` | Guarda la trayectoria, el scatter 3D y las proyecciones ortogonales |

### Estructuras de datos

| Estructura | Uso |
|---|---|
| Lista de `float` | los R de una réplica, generados de una vez antes de simularla |
| Tupla de `int` | la posición final de una réplica |
| Listas `MOVIMIENTOS_2D` y `MOVIMIENTOS_3D` | los desplazamientos (dx, dy, dz) posibles; el índice piso(k·R) elige uno |
| Diccionario `FUNCIONES` | relaciona cada dimensión con su función de simulación |
| Lista de tuplas `tabla` | filas del cuadro de eficiencia (dimensión, tiempo, memoria, probabilidad) |

## Eficiencia computacional

- **Tiempo:** cada paso hace un número constante de operaciones, así que el tiempo de
  una réplica crece en proporción a los pasos, O(n). Pasar de 1D a 3D solo agrega sumas
  por coordenada, por lo que el tiempo crece poco con la dimensión.
- **Memoria:** la memoria pico de una réplica la dominan los 1.000.000 de números R que
  se generan antes de simular, O(n). La posición ocupa espacio constante en cualquier
  dimensión.
- El tiempo se mide con `time.perf_counter` sobre las 100 réplicas, y la memoria con
  `tracemalloc` sobre una sola réplica.

Resultados con las semillas de `semillas_caminata.csv`, en el equipo descrito en
*Requisitos*:

| Dimensión | Tiempo de 100 réplicas (s) | Memoria pico de una réplica (MB) | P(retorno en 1000 pasos) |
|---|---|---|---|
| 1D | 44.2 | 69.5 | 0.99 |
| 2D | 53.3 | 69.5 | 0.69 |
| 3D | 55.1 | 69.5 | 0.27 |

La memoria es la misma en las tres dimensiones porque la ocupan los números R, y el
tiempo crece alrededor de un 25 % de 1D a 3D por las coordenadas adicionales.

## Limitaciones

- **Retorno con 100 réplicas:** la probabilidad estimada tiene un error típico cercano a
  0.05, por lo que solo sirve para comparar el orden de magnitud entre dimensiones.
- **Definición de retorno:** se cuenta si la rana pasa por el origen en algún paso de
  los primeros 1.000, no si está en el origen exactamente en el paso 1.000.
- **Validación parcial:** las pruebas del punto 3 se aplican solo a los números de la
  primera réplica, y no incluyen una prueba de independencia.
- **Memoria:** generar todos los números antes de simular ocupa memoria proporcional a
  los pasos, mientras que generarlos paso a paso ocuparía memoria constante; se eligió así para reutilizar el generador del punto 3
  sin modificarlo.
- **Rendimiento:** el código está en Python puro; las 300 réplicas de 1.000.000 de pasos
  tardan alrededor de tres minutos.
- **Resolución de los R:** el punto 3 trunca a cinco decimales. Para elegir entre 2, 4 o 6
  direcciones esa resolución es suficiente, porque los cortes 1/4 y 1/2 son exactos y
  1/6 solo desplaza la probabilidad de cada dirección en menos de 10⁻⁵.
