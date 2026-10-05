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
cuadrados_medios,10000007,8,,,,1000
congruencial_lineal,7,,1601,3701,10000,1000
congruencial_multiplicativo,12345,,16807,,2147483647,1000
congruencial_lineal,555555555,,1664525,1013904223,4294967296,1000
```

El archivo de ejemplo [`semillas_ejemplo.csv`](semillas_ejemplo.csv) contiene estas filas.
Son los cuatro generadores evaluados en el informe: G1 (cuadrados medios), G2 (ejemplo
de congruencial lineal), G3 (generador del punto 2) y G4 (generador del punto 4).

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

## Archivos

| Archivo | Contenido |
|---|---|
| `generadores.py` | métodos de generación y transformaciones a uniforme y normal |
| `pruebas.py` | pruebas estadísticas de validación |
| `inicializacion.py` | lectura y validación del archivo de semillas |
| `reportes.py` | tablas, exportación a CSV y gráficos |
| `programa_principal.py` | ventana del programa |
| `semillas_ejemplo.csv` | archivo de ejemplo con semillas para la carga externa |

## Funciones

### generadores.py (rutinas de biblioteca)

| Función | Descripción | Parámetros | Retorno |
|---|---|---|---|
| `generar_cuadrados_medios` | Genera números con el método de cuadrados medios | `semilla`, `cantidad_de_digitos` (par), `cantidad_de_numeros` | secuencia |
| `generar_congruencial_lineal` | Genera números con X(i+1) = (a·X(i) + c) mod m | `semilla`, `multiplicador_a`, `incremento_c`, `modulo_m`, `cantidad_de_numeros` | secuencia con verificación de Hull-Dobell |
| `generar_congruencial_multiplicativo` | Genera números con X(i+1) = (a·X(i)) mod m | `semilla`, `multiplicador_a`, `modulo_m`, `cantidad_de_numeros` | secuencia |
| `generar_congruencial` | Base común de los dos métodos congruenciales | `metodo`, `etiqueta`, `semilla`, `multiplicador_a`, `incremento_c`, `modulo_m`, `cantidad_de_numeros` | secuencia |
| `verificar_hull_dobell` | Revisa las tres condiciones de Hull-Dobell para período completo | `multiplicador_a`, `incremento_c`, `modulo_m` | diccionario con las tres condiciones y `cumple` |
| `obtener_factores_primos` | Devuelve los factores primos distintos de un número | `numero` | lista de factores primos |
| `transformar_a_uniforme` | Pasa los R_i a una uniforme entre a y b | `numeros_r`, `limite_inferior`, `limite_superior` | lista de N_i = a + (b − a)·R_i |
| `transformar_a_normal_estandar` | Pasa los R_i a una normal estándar con Box-Muller | `numeros_r` | diccionario con `numeros_normales` y `avisos` |
| `normalizar_con_modulo` | Convierte X_i en R_i entre 0 y 1 | `valor_x`, `modulo_m` | R_i según la paridad de m, truncado |
| `truncar_a_cinco_decimales` | Corta un número a cinco decimales sin redondear | `valor` | valor truncado |
| `truncar_cociente_a_cinco_decimales` | Divide dos enteros y corta el resultado a cinco decimales | `numerador`, `denominador` | cociente truncado |

Una secuencia es un diccionario con `metodo`, `etiqueta`, `parametros`, `valores_x`
(X_i), `numeros_r` (R_i), `periodo` (posición en que un congruencial vuelve a la
semilla), `hull_dobell` y `avisos` (colapso a cero, ciclo, período o pares omitidos).

### pruebas.py (rutinas de biblioteca)

| Función | Descripción | Parámetros | Retorno |
|---|---|---|---|
| `prueba_de_medias` | Prueba de medias | `numeros_r` | resultado con la media, el intervalo 0.5 ± Z·√(1/12)/√n y las medias por bloque |
| `prueba_de_varianza` | Prueba de varianza | `numeros_r` | resultado con la varianza muestral (n − 1), su intervalo de aceptación y las varianzas por bloque |
| `prueba_chi_cuadrado` | Prueba chi-cuadrado de uniformidad | `numeros_r`, `cantidad_de_intervalos` | resultado con frecuencias observadas por intervalo y frecuencia esperada |
| `prueba_kolmogorov_smirnov` | Prueba de Kolmogorov-Smirnov | `numeros_r`, `cantidad_de_intervalos` | resultado con S(x), F(x), diferencias, DMAX y DMAXP |
| `prueba_de_poker` | Prueba de póker | `numeros_r` | resultado con frecuencias observadas y esperadas por mano |
| `clasificar_mano_de_poker` | Dice qué mano forman los cinco decimales de un número | `numero_r` | símbolo de la mano (D, O, T, K, F, P o Q) |
| `valor_critico_kolmogorov_smirnov` | Calcula DMAXP para α = 0.05 | `cantidad_de_numeros` | valor tabulado si n ≤ 50, 1.36/√n si n > 50 |
| `valor_critico_chi_cuadrado` | Calcula el valor crítico chi-cuadrado | `probabilidad_acumulada`, `grados_de_libertad` | valor crítico truncado |
| `probabilidad_acumulada_chi_cuadrado` | Calcula P(χ² ≤ x) con la función gamma incompleta regularizada | `valor_x`, `grados_de_libertad` | probabilidad |
| `calcular_estadistico_chi_cuadrado` | Calcula Σ(O − E)²/E | `frecuencias_observadas`, `frecuencias_esperadas` | estadístico truncado |
| `contar_frecuencias_por_intervalo` | Cuenta cuántos números caen en cada intervalo de [0, 1) | `numeros_r`, `cantidad_de_intervalos` | lista de frecuencias |
| `obtener_limites_de_intervalos` | Devuelve los límites de cada intervalo | `cantidad_de_intervalos` | lista de pares (inicio, fin) |
| `cantidad_de_intervalos_por_defecto` | Calcula cuántos intervalos usar por defecto | `cantidad_de_numeros` | k = √n redondeado (mínimo 2) |
| `dividir_en_bloques` | Parte la secuencia en bloques consecutivos | `numeros_r` | lista de bloques de igual tamaño |
| `calcular_limites_de_medias` | Calcula los límites de aceptación de la media | `cantidad_de_numeros` | (LI, LS) |
| `calcular_varianza` | Calcula la varianza muestral | `numeros_r` | varianza con n − 1 |
| `calcular_limites_de_varianza` | Calcula los límites de aceptación de la varianza | `cantidad_de_numeros` | (χ² inferior, χ² superior, LI, LS) |

Un resultado es un diccionario con `prueba`, `estadistico`, `valor_critico`, `pasa`,
`avisos` y los datos de su gráfico.

### inicializacion.py (rutina de inicialización)

| Función | Descripción | Parámetros | Retorno |
|---|---|---|---|
| `leer_archivo_de_semillas` | Lee las semillas desde un archivo .txt o .csv | `ruta_del_archivo` (separado por comas o punto y coma) | (filas válidas, errores con número de fila) |
| `validar_fila_de_semilla` | Revisa que una fila tenga los datos que pide su método | diccionario con `metodo`, `semilla`, `digitos`, `a`, `c`, `m`, `cantidad` | (fila con enteros, lista de errores) |
| `convertir_campos_a_enteros` | Convierte a entero los campos de una fila | `fila`, `campos` | (fila convertida, lista de errores) |

### reportes.py (generador de reportes)

| Función | Descripción | Parámetros | Retorno |
|---|---|---|---|
| `crear_histograma_de_secuencia` | Crea el histograma de frecuencias de una secuencia | `secuencia` | figura con un histograma por distribución (R_i, U(a, b), normal) |
| `crear_grafico_de_medias` | Crea el gráfico de la prueba de medias | lista de resultados | histograma de las medias por bloque con su intervalo de aceptación, la media teórica y la media de la secuencia, un panel por método |
| `crear_grafico_de_varianzas` | Crea el gráfico de la prueba de varianza | lista de resultados | histograma de las varianzas por bloque con su intervalo de aceptación, la varianza teórica y la varianza de la secuencia, un panel por método |
| `crear_grafico_de_distribucion_por_bloques` | Base común de los gráficos de medias y varianzas | `resultados`, `titulo`, `nombre_del_estadistico`, `nombre_del_valor_esperado` | figura |
| `crear_grafico_chi_cuadrado` | Crea el gráfico de la prueba chi-cuadrado | lista de resultados | figura de barras observadas vs esperadas, un panel por método |
| `crear_grafico_kolmogorov_smirnov` | Crea el gráfico de la prueba de Kolmogorov-Smirnov | lista de resultados | figura de S(x) empírica vs F(x) = x con DMAX resaltado, un panel por método |
| `crear_grafico_de_poker` | Crea el gráfico de la prueba de póker | lista de resultados | figura de manos observadas vs esperadas, un panel por método |
| `dibujar_barras_observadas_contra_esperadas` | Dibuja barras de frecuencias observadas y esperadas en un panel | `panel`, `nombres_de_las_barras`, `frecuencias_observadas`, `frecuencias_esperadas` | ninguno |
| `crear_figura_con_paneles` | Crea una figura con varios paneles en cuadrícula | `cantidad_de_paneles`, `titulo` | (figura, paneles) |
| `exportar_secuencia_a_csv` | Guarda una secuencia en un archivo CSV | `secuencia`, `ruta_del_archivo` | archivo con las columnas i, X_i, R_i, N_i y Z_i |
| `describir_secuencia` | Escribe un resumen de la secuencia | `secuencia` | texto con parámetros, Hull-Dobell y avisos |
| `describir_resultado` | Escribe el resultado de una prueba | `resultado` | texto con estadístico, criterio y decisión |
| `describir_criterio` | Escribe el criterio de aceptación de una prueba | `resultado` | intervalo o valor crítico como texto |
| `obtener_columnas_de_secuencia` | Arma las columnas de la tabla de una secuencia | `secuencia` | diccionario {columna: valores} |
| `obtener_filas_de_secuencia` | Arma las filas de la tabla de una secuencia | `secuencia` | (encabezados, filas) |
| `formatear_valor` | Escribe un valor con cinco decimales si es decimal | `valor` | texto |
| `acortar_etiqueta` | Parte una etiqueta larga en varias líneas | `etiqueta` | texto |

Las figuras son objetos `matplotlib.figure.Figure`; fuera de la ventana se guardan con
`figura.savefig("archivo.png")`.

### programa_principal.py (programa principal)

Construye la ventana y coordina la inicialización, las rutinas de biblioteca y el
generador de reportes.

| Función | Descripción |
|---|---|
| `iniciar_programa` | Abre el programa |
| `crear_ventana_principal` | Crea la ventana principal |
| `crear_marco_de_generacion` | Crea la parte de la ventana para elegir el método y generar |
| `crear_marco_de_secuencias` | Crea la parte de la ventana con la lista de secuencias |
| `crear_marco_de_tabla` | Crea la parte de la ventana con la tabla de la secuencia |
| `crear_marco_de_pruebas` | Crea la parte de la ventana para elegir y ejecutar las pruebas |
| `generar_desde_campos` | Genera una secuencia con los datos escritos a mano |
| `cargar_archivo_de_semillas` | Carga un archivo de semillas y genera sus secuencias |
| `generar_secuencia_desde_fila` | Genera la secuencia que pide una fila |
| `agregar_secuencia` | Genera una secuencia, le aplica las transformaciones y la guarda en la lista |
| `leer_fila_de_campos` | Lee los datos escritos en la ventana |
| `leer_opciones_de_transformacion` | Lee qué transformaciones (uniforme, normal) se eligieron |
| `leer_cantidad_de_intervalos` | Lee la cantidad de intervalos escrita |
| `actualizar_campos_habilitados` | Activa solo los campos del método elegido |
| `actualizar_lista_de_secuencias` | Refresca la lista de secuencias generadas |
| `obtener_indice_elegido` | Devuelve la secuencia elegida en la lista |
| `mostrar_secuencia_elegida` | Muestra la tabla y el resumen de la secuencia elegida |
| `exportar_secuencia_elegida` | Guarda la secuencia elegida en un archivo CSV |
| `quitar_secuencia_elegida` | Borra la secuencia elegida de la lista |
| `ejecutar_pruebas_elegidas` | Corre las pruebas elegidas sobre las secuencias |
| `ejecutar_y_graficar_pruebas` | Corre las pruebas elegidas y muestra sus gráficos |
| `mostrar_histograma_elegido` | Muestra el histograma de la secuencia elegida |
| `mostrar_grafico_elegido` | Dibuja en la ventana el gráfico elegido |
| `mostrar_grafico_de_la_fila_elegida` | Muestra el gráfico de la prueba elegida en el resumen |
| `publicar_graficos` | Agrega gráficos nuevos a la lista y muestra uno |

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

## Limitaciones

- **Cuadrados medios:** el método degenera con facilidad. Muchas semillas colapsan a cero
  o entran en un ciclo corto; en ese caso la generación se detiene y la secuencia queda
  con menos números de los pedidos (el sistema lo advierte).
- **Período de los congruenciales:** ningún congruencial supera m números distintos. En
  el lineal, el período completo solo está garantizado si se cumple Hull-Dobell; en el
  multiplicativo el período máximo es m − 1. El período se detecta únicamente cuando la
  secuencia vuelve a la semilla.
- **Resolución de cinco decimales:** al truncar, los R_i solo pueden tomar 100.000
  valores distintos, aunque m sea mucho mayor. Con m par, R_i = X_i / (m − 1) puede valer
  1.0.
- **Sin prueba de independencia:** las cinco pruebas evalúan uniformidad, media y
  varianza. Al no implementarse la prueba de rachas, una secuencia con dependencia entre
  números consecutivos (por ejemplo, ordenada de forma creciente) puede aprobarlas.
- **Kolmogorov-Smirnov por intervalos:** la prueba compara las frecuencias acumuladas de
  los k intervalos y no cada número por separado, por lo que pierde sensibilidad frente
  a desviaciones dentro de un intervalo.
- **Validez de chi-cuadrado y póker:** con pocos números la frecuencia esperada de un
  intervalo o de una mano puede ser menor que 5. El sistema lo advierte, pero igual
  entrega la decisión.
- **Nivel de significancia fijo:** todas las pruebas usan α = 0.05; no se puede cambiar
  desde la ventana.
- **Solo se validan los R_i:** las secuencias U(a, b) y normales no pasan por las
  pruebas, solo se muestran en su histograma.
- **Normal estándar únicamente:** se genera N(0, 1); para otra media μ y desviación σ se
  debe aplicar μ + σ·Z fuera del módulo. Box-Muller omite los pares con R₁ = 0 y el último
  número cuando la cantidad es impar.
- **Bloques de medias y varianzas:** los números que sobran al dividir la secuencia en
  bloques no entran en el gráfico de distribución.
- **Rendimiento:** todo está escrito en Python puro y las secuencias se guardan completas
  en listas, por lo que secuencias de millones de números tardan varios segundos y
  ocupan memoria proporcional a su tamaño.
