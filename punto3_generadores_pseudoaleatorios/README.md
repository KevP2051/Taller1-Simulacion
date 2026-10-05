# Punto 3: Generadores y validadores de números pseudoaleatorios

Biblioteca en Python, implementada desde cero, con generadores de números
pseudoaleatorios (cuadrados medios, congruenciales, uniforme y normal) y pruebas
estadísticas de validación (medias, varianza, chi-cuadrado, Kolmogorov-Smirnov
y póker). Por indicación del docente no se implementan la prueba de rachas ni el
generador congruencial aditivo. Es la fuente de aleatoriedad de los puntos 2 (caminata aleatoria)
y 4 (EpiSim) del taller.

## Requisitos

- Python 3.10 o superior, con `tkinter` (incluido en el instalador de Python para Windows).
- `matplotlib` 3.5 o superior, solo para los gráficos.

```bash
python -m pip install matplotlib
```

### Equipo de desarrollo y pruebas

| Elemento | Especificación |
|---|---|
| Lenguaje | Python 3.14.0 (matplotlib 3.10.8, Tk 8.6) |
| Sistema operativo | Windows 11 Pro 64 bits (versión 10.0.26200) |
| Procesador | AMD Ryzen 7 5800XT, 8 núcleos y 16 hilos |
| Memoria RAM | 16 GB |

## Uso

El programa se ejecuta desde la carpeta raíz del taller:

```bash
python -m punto3_generadores_pseudoaleatorios.programa_principal
```

Se ejecuta como módulo para que los puntos 2 y 4 importen los generadores del punto 3
sin copiar su código.

### Archivo de semillas

Las semillas pueden ingresarse a mano en la ventana o cargarse desde un archivo `.csv`
o `.txt` separado por comas (o por punto y coma, como lo guarda Excel en español). Cada
fila corresponde a una secuencia; las columnas que no aplican a un método quedan vacías:

```
metodo,semilla,digitos,a,c,m,cantidad
cuadrados_medios,5735,4,,,,1000
congruencial_lineal,7,,1601,3701,10000,1000
congruencial_multiplicativo,7,,129,,2147483647,1000
```

### Ventana

1. Se elige el método, se escriben la semilla y sus parámetros, y se pulsa **Generar**; o
   se pulsa **Cargar archivo de semillas** para generar una secuencia por fila.
2. Opcionalmente se marcan **Uniforme U(a, b)** (con sus límites) y **Normal estándar
   N(0, 1)** antes de generar.
3. Al elegir una secuencia en la lista se muestran su tabla, sus parámetros, la
   verificación de Hull-Dobell y sus avisos. **Histograma** muestra sus histogramas en el
   área de gráficos y **Exportar CSV** guarda la tabla completa.
4. Se marcan las pruebas, se revisa el número de intervalos k y se pulsa **Ejecutar
   pruebas**: el resumen muestra una fila por secuencia y prueba, y a su derecha aparece
   el área de gráficos. La lista **Ver gráfico** permite elegir el histograma o el gráfico
   de cada prueba; al seleccionar una fila del resumen se muestra el gráfico de esa
   prueba. Todo gráfico se guarda como imagen desde su barra de herramientas.

### Uso como biblioteca

```python
from punto3_generadores_pseudoaleatorios import generadores, pruebas

secuencia = generadores.generar_congruencial_lineal(7, 1601, 3701, 10000, 1000)
numeros_uniformes = secuencia["numeros_r"]
resultado = pruebas.prueba_chi_cuadrado(numeros_uniformes, 32)
```

## Funciones

### generadores.py (rutinas de biblioteca)

| Función | Parámetros | Retorno |
|---|---|---|
| `generar_cuadrados_medios` | `semilla`, `cantidad_de_digitos` (par), `cantidad_de_numeros` | secuencia |
| `generar_congruencial_lineal` | `semilla`, `multiplicador_a`, `incremento_c`, `modulo_m`, `cantidad_de_numeros` | secuencia con verificación de Hull-Dobell |
| `generar_congruencial_multiplicativo` | `semilla`, `multiplicador_a`, `modulo_m`, `cantidad_de_numeros` | secuencia |
| `verificar_hull_dobell` | `multiplicador_a`, `incremento_c`, `modulo_m` | diccionario con las tres condiciones y `cumple` |
| `transformar_a_uniforme` | `numeros_r`, `limite_inferior`, `limite_superior` | lista de N_i = a + (b − a)·R_i |
| `transformar_a_normal_estandar` | `numeros_r` | diccionario con `numeros_normales` y `avisos` |
| `normalizar_con_modulo` | `valor_x`, `modulo_m` | R_i según la paridad de m, truncado |
| `truncar_a_cinco_decimales` | `valor` | valor truncado a cinco decimales |

Una secuencia es un diccionario con `metodo`, `etiqueta`, `parametros`, `valores_x`
(X_i), `numeros_r` (R_i), `periodo` (posición en que un congruencial vuelve a la
semilla), `hull_dobell` y `avisos` (colapso a cero, ciclo, período o pares omitidos).

### pruebas.py (rutinas de biblioteca)

| Función | Parámetros | Retorno |
|---|---|---|
| `prueba_de_medias` | `numeros_r` | resultado con la media, el intervalo 0.5 ± Z·√(1/12)/√n y las medias por bloque |
| `prueba_de_varianza` | `numeros_r` | resultado con la varianza muestral (n − 1), su intervalo de aceptación y las varianzas por bloque |
| `prueba_chi_cuadrado` | `numeros_r`, `cantidad_de_intervalos` | resultado con frecuencias observadas por intervalo y frecuencia esperada |
| `prueba_kolmogorov_smirnov` | `numeros_r`, `cantidad_de_intervalos` | resultado con S(x), F(x), diferencias, DMAX y DMAXP |
| `prueba_de_poker` | `numeros_r` | resultado con frecuencias observadas y esperadas por mano |
| `valor_critico_kolmogorov_smirnov` | `cantidad_de_numeros` | DMAXP de la tabla de Kolmogorov-Smirnov (α = 0.05): valor tabulado si n ≤ 50, 1.36/√n si n > 50 |
| `valor_critico_chi_cuadrado` | `probabilidad_acumulada`, `grados_de_libertad` | valor crítico chi-cuadrado truncado |
| `probabilidad_acumulada_chi_cuadrado` | `valor_x`, `grados_de_libertad` | P(χ² ≤ x), mediante la función gamma incompleta regularizada |
| `cantidad_de_intervalos_por_defecto` | `cantidad_de_numeros` | k = √n redondeado (mínimo 2) |
| `dividir_en_bloques` | `numeros_r` | lista de bloques consecutivos de igual tamaño |
| `calcular_limites_de_medias` | `cantidad_de_numeros` | (LI, LS) de la prueba de medias |
| `calcular_varianza` | `numeros_r` | varianza muestral con n − 1 |
| `calcular_limites_de_varianza` | `cantidad_de_numeros` | (χ² inferior, χ² superior, LI, LS) de la prueba de varianza |

Un resultado es un diccionario con `prueba`, `estadistico`, `valor_critico`, `pasa`,
`avisos` y los datos de su gráfico.

### inicializacion.py (rutina de inicialización)

| Función | Parámetros | Retorno |
|---|---|---|
| `validar_fila_de_semilla` | diccionario con `metodo`, `semilla`, `digitos`, `a`, `c`, `m`, `cantidad` | (fila con enteros, lista de errores) |
| `leer_archivo_de_semillas` | `ruta_del_archivo` (.csv o .txt, separado por comas o punto y coma) | (filas válidas, errores con número de fila) |

### reportes.py (generador de reportes)

| Función | Parámetros | Retorno |
|---|---|---|
| `crear_histograma_de_secuencia` | `secuencia` | figura con un histograma por distribución (R_i, U(a, b), normal) |
| `crear_grafico_de_medias` | lista de resultados | histograma de las medias por bloque con su intervalo de aceptación, la media teórica y la media de la secuencia, un panel por método |
| `crear_grafico_de_varianzas` | lista de resultados | histograma de las varianzas por bloque con su intervalo de aceptación, la varianza teórica y la varianza de la secuencia, un panel por método |
| `crear_grafico_chi_cuadrado` | lista de resultados | figura de barras observadas vs esperadas, un panel por método |
| `crear_grafico_kolmogorov_smirnov` | lista de resultados | figura de S(x) empírica vs F(x) = x con DMAX resaltado, un panel por método |
| `crear_grafico_de_poker` | lista de resultados | figura de manos observadas vs esperadas, un panel por método |
| `exportar_secuencia_a_csv` | `secuencia`, `ruta_del_archivo` | archivo con las columnas i, X_i, R_i, N_i y Z_i |
| `describir_secuencia` | `secuencia` | texto con parámetros, Hull-Dobell y avisos |

Las figuras son objetos `matplotlib.figure.Figure`; fuera de la ventana se guardan con
`figura.savefig("archivo.png")`.

### programa_principal.py (programa principal)

Construye la ventana y coordina la inicialización, las rutinas de biblioteca y el
generador de reportes.

## Decisiones de diseño

### Precisión

Todos los números se trabajan con cinco posiciones decimales, por truncamiento
(0.834219 → 0.83421). Antes de truncar un valor decimal se redondea a diez decimales para
eliminar el error de representación de la coma flotante (por ejemplo, 0.22 − 0.20 da
0.019999999999999997 y debe truncarse como 0.02000).

### Normalización de los generadores

- Congruenciales lineal y multiplicativo, según el módulo m:
  - m impar: R_i = X_i / m, rango [0, 1).
  - m par: R_i = X_i / (m − 1).
- Cuadrados medios: R_i = X_i / 10^d, con d el número de dígitos de la semilla.
  Por ejemplo, con semilla 5735: 5735² = 32890225, dígitos centrales 8902 y
  R_1 = 8902 / 10⁴ = 0.89020. La regla de m par o impar no aplica porque el método no
  tiene módulo.

### Distribución uniforme U(a, b)

N_i = a + (b − a)·R_i convierte cada R_i en un valor entre a y b repartido de forma
pareja. Por ejemplo, para U(2, 5) y R_i = 0.50: N_i = 2 + 3·0.50 = 3.5.

### Distribución normal

A diferencia de la uniforme, la normal no tiene mínimo ni máximo: los valores se
concentran alrededor de un centro (media) con una dispersión (desviación). Se genera la
normal estándar N(0, 1) mediante Box-Muller, que transforma dos uniformes R₁ y R₂ en dos
normales:

Z₁ = √(−2·ln R₁)·cos(2π·R₂), Z₂ = √(−2·ln R₁)·sin(2π·R₂)

Como ln 0 no está definido, si R₁ = 0 se omite ese par y el sistema lo advierte.

La transformación de Box-Muller cumple el requisito del enunciado de generar la
distribución normal; los puntos 2 y 4 solo utilizan la uniforme.

### Secuencias que se validan

Las cinco pruebas se aplican a las secuencias R_i en [0, 1), cuyas propiedades esperadas
son:

- Media: E[R_i] = 0.5
- Varianza: Var(R_i) = 1/12 ≈ 0.08333
- Distribución: uniforme en [0, 1)

Las secuencias U(a, b) y normales solo se presentan con su histograma, porque las
pruebas comparan contra la uniforme en [0, 1).

### Comparación entre métodos

Cada prueba presenta un gráfico con un panel por método generado.

### Distribución de medias y varianzas por bloques

La prueba de medias y la de varianza producen un solo estadístico por secuencia. Para
mostrar la distribución de las medias y de las varianzas, el gráfico divide la secuencia
en bloques consecutivos de igual tamaño, calcula la media y la varianza de cada bloque y
las presenta en un histograma junto con:

- el intervalo de aceptación al 95 % para un bloque de ese tamaño, con las mismas fórmulas
  de la prueba y n igual al tamaño del bloque;
- el valor teórico (0.5 o 1/12) y el estadístico de la secuencia completa;
- cuántos bloques quedan dentro del intervalo (se espera cerca del 95 %).

El número de bloques es √n redondeado, el mismo criterio de los intervalos de
chi-cuadrado, y cada bloque tiene al menos dos números. Con n = 1000 se forman 32 bloques
de 31 números; los números que sobran al final no entran en ningún bloque. La decisión de
la prueba no cambia: se toma con el estadístico de la secuencia completa.

### Nivel de significancia

Todas las pruebas trabajan con α = 0.05 (95 % de aceptación).

### Criterios de decisión

| Prueba | Estadístico | Pasa si |
|---|---|---|
| Medias | media de los R_i | LI ≤ media ≤ LS, con LI y LS = 0.5 ± Z·√(1/12)/√n |
| Varianza | s² con n − 1 | LI ≤ s² ≤ LS, con LI = χ²(0.025, n − 1)/(12(n − 1)) y LS = χ²(0.975, n − 1)/(12(n − 1)) |
| Chi-cuadrado | Σ(O − E)²/E | estadístico < χ²(0.95, k − 1) |
| Kolmogorov-Smirnov | DMAX | DMAX < DMAXP |
| Póker | Σ(O − E)²/E | estadístico < χ²(0.95, 6) |

Z_c = 1.95996 es el valor exacto de la normal estándar para 0.975, obtenido con
`statistics.NormalDist().inv_cdf(0.975)` y truncado a cinco decimales. En la prueba de
varianza, χ²(0.025, 49) = 31.5549 y χ²(0.975, 49) = 70.2224 corresponden a
`CHISQ.INV.RT(0.975; 49)` y `CHISQ.INV.RT(0.025; 49)` de Excel; para n = 50 dan
LI = 0.05366 y LS = 0.11942.

### Número de intervalos (chi-cuadrado y Kolmogorov-Smirnov)

El número de intervalos no es fijo. Por defecto se usa k = √n redondeado al entero más
cercano, donde n es la cantidad de números de la secuencia, y el valor puede cambiarse
en la ventana antes de ejecutar las pruebas.

Un número fijo de intervalos no sirve para todos los tamaños de secuencia del taller:

| Cantidad de números | Con 10 intervalos fijos | Con k = √n |
|---|---|---|
| 20 | 2 esperados por intervalo (chi-cuadrado no válida) | 4 intervalos, 5 esperados |
| 50 | 5 esperados por intervalo | 7 intervalos, 7.14 esperados |
| 64 | 6.4 esperados por intervalo | 8 intervalos, 8 esperados (7 gl) |
| 1.000.000 | 100.000 esperados por intervalo | 1.000 intervalos, 1.000 esperados |

Si la frecuencia esperada por intervalo es menor que 5, el sistema lo advierte junto al
resultado de la prueba.

### Rango de los intervalos

Los k intervalos cubren siempre [0, 1) con ancho 1/k, y no el rango entre el mínimo y el
máximo de los datos. La hipótesis es que los R_i son uniformes en [0, 1); si los
intervalos se ajustaran al mínimo y al máximo observados, una secuencia concentrada en
una parte del rango podría aprobar. Por ejemplo, 15 números repartidos de forma pareja
entre 0.40 y 0.60 aprobarían con intervalos de 0.40 a 0.60, pero con intervalos en
[0, 1) los intervalos de los extremos quedan vacíos y la prueba los rechaza
correctamente.

Un número igual a 1.0 (posible cuando m es par, pues R_i = X_i / (m − 1)) se cuenta en
el último intervalo.

### Grados de libertad y valor crítico chi-cuadrado

Los grados de libertad dependen de cada prueba, según gl = (Nc − 1)(Nf − 1), con
Nf = 2 filas (frecuencias observadas y esperadas):

| Prueba | Grados de libertad |
|---|---|
| Chi-cuadrado | k − 1 (con 8 intervalos: 7 gl, valor crítico 14.06714) |
| Póker | 7 manos − 1 = 6 (valor crítico 12.59158) |
| Varianza | n − 1 |

En póker, conocidas las cantidades de seis manos, la séptima queda determinada por el
total n; por eso solo seis valores varían libremente.

Como los grados de libertad cambian con k y con n, el valor crítico chi-cuadrado se
calcula para cualquier número de grados de libertad en lugar de tomarse de una tabla
impresa, cuyos valores reproduce.

### Prueba de póker

Cada R_i se toma con sus cinco decimales como una mano de cinco dígitos y se clasifica
en uno de los siete patrones:

| Patrón | Símbolo | Descripción | Ejemplo | Probabilidad |
|---|---|---|---|---|
| Todos distintos | D | Los 5 dígitos son diferentes | 12345 | 0.3024 |
| Un par | O | Un dígito aparece 2 veces | 11234 | 0.5040 |
| Dos pares | T | Dos dígitos aparecen 2 veces | 11223 | 0.1080 |
| Tercia | K | Un dígito aparece 3 veces | 11123 | 0.0720 |
| Full | F | Un dígito 3 veces + otro 2 | 11122 | 0.0090 |
| Cuatro | P | Un dígito aparece 4 veces | 11112 | 0.0045 |
| Cinco | Q | Un dígito aparece 5 veces | 11111 | 0.0001 |

La frecuencia esperada de cada patrón es n · probabilidad.

### Prueba de Kolmogorov-Smirnov

La prueba se aplica sobre los k intervalos:

1. Frecuencia obtenida por intervalo y frecuencia obtenida acumulada.
2. S(x) = frecuencia obtenida acumulada / n.
3. Frecuencia esperada acumulada: n / k sumada intervalo a intervalo.
4. F(x) = frecuencia esperada acumulada / n.
5. Dif = |F(x) − S(x)| por intervalo; DMAX es la mayor diferencia.
6. DMAXP, el error máximo permitido, se toma de la tabla de Kolmogorov-Smirnov indicada
   por el docente (columna α = 0.05), con n la cantidad de números de la secuencia:
   - n ≤ 50: valor tabulado (por ejemplo, n = 20 → 0.29408 y n = 50 → 0.18841).
   - n > 50: DMAXP = 1.36 / √n (por ejemplo, n = 1000 → 0.04300).
7. La secuencia pasa la prueba si DMAX < DMAXP.
