# Punto 3: Generadores y validadores de números pseudoaleatorios

Biblioteca en Python, implementada desde cero, con generadores de números
pseudoaleatorios (cuadrados medios, congruenciales, uniforme y normal) y pruebas
estadísticas de validación (medias, varianza, chi-cuadrado, Kolmogorov-Smirnov,
póker y rachas). Es la fuente de aleatoriedad de los puntos 2 (caminata aleatoria)
y 4 (EpiSim) del taller.

## Uso

El programa se ejecuta desde la carpeta raíz del taller:

```bash
python -m punto3_generadores_pseudoaleatorios.programa_principal
```

Se ejecuta como módulo para que los puntos 2 y 4 importen los generadores del punto 3
sin copiar su código.

### Archivo de semillas

Las semillas pueden ingresarse a mano en la ventana o cargarse desde un archivo `.csv`
o `.txt` separado por comas. Cada fila corresponde a una secuencia; las columnas que no
aplican a un método quedan vacías:

```
metodo,semilla,digitos,a,c,m,cantidad
cuadrados_medios,5735,4,,,,1000
congruencial_lineal,7,,1601,3701,10000,1000
congruencial_multiplicativo,7,,129,,2147483647,1000
```

_La descripción de cada función se documentará al implementar el módulo._

## Decisiones de diseño

### Precisión

Todos los números se trabajan con cinco posiciones decimales, por truncamiento
(0.834219 → 0.83421).

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

Las seis pruebas se aplican a las secuencias R_i en [0, 1), cuyas propiedades esperadas
son:

- Media: E[R_i] = 0.5
- Varianza: Var(R_i) = 1/12 ≈ 0.08333
- Distribución: uniforme en [0, 1)

Las secuencias U(a, b) y normales solo se presentan con su histograma, porque las
pruebas comparan contra la uniforme en [0, 1).

### Comparación entre métodos

Las pruebas de medias y de varianza calculan una media y una varianza por cada método
generado y las muestran en un mismo gráfico, con su intervalo de aceptación y el valor
teórico esperado. Las demás pruebas presentan una ventana por prueba, con un panel por
método.

### Nivel de significancia

Todas las pruebas trabajan con α = 0.05 (95 % de aceptación).

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

### Grados de libertad y valor crítico chi-cuadrado

Los grados de libertad dependen de cada prueba, según gl = (Nc − 1)(Nf − 1), con
Nf = 2 filas (frecuencias observadas y esperadas):

| Prueba | Grados de libertad |
|---|---|
| Chi-cuadrado | k − 1 (con 8 intervalos: 7 gl, valor crítico 14.06714) |
| Póker | 7 manos − 1 = 6 (valor crítico 12.59159) |
| Varianza | n − 1 |

En póker, conocidas las cantidades de seis manos, la séptima queda determinada por el
total n; por eso solo seis valores varían libremente.

Como los grados de libertad cambian con k y con n, el valor crítico chi-cuadrado se
calcula para cualquier número de grados de libertad en lugar de tomarse de una tabla
impresa, cuyos valores reproduce.

### Prueba de Kolmogorov-Smirnov

La prueba se aplica sobre los k intervalos:

1. Frecuencia obtenida por intervalo y frecuencia obtenida acumulada.
2. S(x) = frecuencia obtenida acumulada / n.
3. Frecuencia esperada acumulada: n / k sumada intervalo a intervalo.
4. F(x) = frecuencia esperada acumulada / n.
5. Dif = |F(x) − S(x)| por intervalo; DMAX es la mayor diferencia.
6. DMAXP, el error máximo permitido, sigue la tabla de Kolmogorov-Smirnov con α = 0.05:
   - n ≤ 50: DMAXP = c / (√n + 0.12 + 0.11/√n), con c = √(−ln(α/2) / 2) = 1.35810.
     Esta expresión reproduce los valores de la tabla (para n = 50, DMAXP = 0.18845).
   - n > 50: DMAXP = 1.36 / √n, fórmula para n grande indicada por la tabla
     (para n = 1000, DMAXP = 0.04300).
7. La secuencia pasa la prueba si DMAX < DMAXP.
