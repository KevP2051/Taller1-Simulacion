# Punto 4: EpiSim, simulación Monte Carlo de propagación de enfermedades contagiosas

Simulación Montecarlo de un modelo SEIR modificado con vacunación sobre una población
de 10.000 individuos, durante 365 días y con 1.000 réplicas por escenario. Toda la
aleatoriedad proviene del generador congruencial lineal del punto 3
(`punto3_generadores_pseudoaleatorios`); no se usa `random` ni `numpy.random` para
generar resultados.

## Requisitos

- Python 3.10 o superior.
- El paquete del punto 3 debe estar disponible desde la raíz del repositorio.
- El análisis (`analisis_episim.py`) usa `numpy`, `pandas` y `matplotlib`. No requiere
  `scipy`: la correlación de Spearman se calcula directamente sobre los rangos.

```bash
python -m pip install numpy pandas matplotlib
```

## Uso

Los comandos recomendados se ejecutan desde la raíz del repositorio, siempre en este orden:

```bash
python -m punto4_episim.execute_episim  # simula y guarda los CSV
python -m punto4_episim.analisis_episim # genera gráficos y tablas
```

El segundo paso no simula: solo lee los archivos del primero, por lo que puede repetirse
sin volver a correr la simulación.

También es posible ejecutar el análisis directamente desde `punto4_episim`:

```bash
python analisis_episim.py
```

### Argumentos de `execute_episim.py`

| Argumento | Valor por defecto | Significado |
|---|---|---|
| `--replicas` | 1000 | réplicas por escenario |
| `--semilla` | 555555555 | semilla base del generador |
| `--rep-sensibilidad` | 100 | réplicas por cada caso del análisis de sensibilidad |

Prueba rápida (menos de un minuto):

```bash
python -m punto4_episim.execute_episim --replicas 20 --rep-sensibilidad 5
python -m punto4_episim.analisis_episim
```

## Archivos

| Archivo | Papel |
|---|---|
| `execute_episim.py` | programa principal: corre escenarios, sensibilidad, validación del generador y medición de tiempos |
| `analisis_episim.py` | genera las figuras, correlaciones y tabla de estadísticas a partir de los CSV |
| `main.py` | fachada pública de la API del paquete |
| `config.py` | lectura de configuraciones y muestreo de parámetros |
| `models.py` | tipos, estados y estructuras de datos del modelo |
| `random.py` | adaptador del generador congruencial lineal y muestreo uniforme |
| `runner.py` | ejecución de réplicas y cálculo de sus métricas |
| `simulation.py` | implementación del modelo SEIR y sus transiciones |
| `structures.py` | piscina indexada y muestreo de contactos |
| `configuracion/` | un archivo CSV de parámetros por escenario |
| `resultados/` | salidas de la simulación (se crea al ejecutar) |
| `graficos/` | figuras generadas por el análisis |

## Configuración de escenarios

Cada escenario es un archivo CSV con las columnas `parametro,min,max`. Un parámetro fijo
se escribe con `min` igual a `max`. Para crear un escenario nuevo basta copiar un archivo,
cambiar sus valores y registrarlo en el diccionario `ESCENARIOS` de `execute_episim.py`;
no hay que modificar el motor.

| Parámetro | Valor | Momento del sorteo |
|---|---|---|
| `poblacion` | 10000 | fijo |
| `infectados_iniciales` | 10 | fijo |
| `dias` | 365 | fijo |
| `contactos_maximos_k` | 4 | fijo |
| `umbral_control` | 10 | fijo |
| `seleccion_solo_susceptibles` | 1 o 0 | fijo |
| `beta` | U(0.3, 0.5) | una vez por réplica |
| `probabilidad_transmision` | U(0.4, 0.6) | una vez por réplica |
| `tasa_vacunacion` | U(0.3, 0.7), o 0 sin vacunación | una vez por réplica |
| `efectividad_vacuna` | U(0.80, 0.95) | una vez por réplica |
| `letalidad` | U(0.005, 0.02) | una vez por réplica |
| `periodo_incubacion` | U(2, 5) días, redondeado | por individuo, al exponerse |
| `periodo_infeccioso` | U(7, 14) días, redondeado | por individuo, al exponerse |

Escenarios incluidos:

| Escenario | Archivo | Vacunación | Selección del contacto |
|---|---|---|---|
| `sin_vacunacion` | `config_sin_vacunacion.csv` | no | solo susceptibles |
| `con_vacunacion` | `config_con_vacunacion.csv` | sí | solo susceptibles |
| `sin_vacunacion_homogenea` | `config_sin_vacunacion_homogenea.csv` | no | toda la población |
| `con_vacunacion_homogenea` | `config_con_vacunacion_homogenea.csv` | sí | toda la población |

## Mecanismo estocástico

### Generador

Congruencial lineal mixto del punto 3, X(i+1) = (a·X(i) + c) mod m, con a = 1664525,
c = 1013904223 y m = 2³². Los parámetros cumplen el teorema de Hull-Dobell, de modo que
el período es 2³². Como m es par, el punto 3 normaliza R(i) = X(i) / (m − 1) y trunca a
cinco decimales. La clase `PseudorandomGenerator` pide los números al punto 3 en bloques
de 256 y los entrega uno a uno; cada bloque continúa desde el último X consumido, así que
la secuencia es la misma que se obtendría con una sola llamada.

### Uso de los números en una réplica

1. **Parámetros de la réplica.** Cinco números, en este orden: `beta`,
   `probabilidad_transmision`, `tasa_vacunacion`, `efectividad_vacuna` y `letalidad`,
   cada uno con la transformación X = a + (b − a)·R.
2. **Población inicial.** Se vacunan exactamente round(tasa·N) individuos, elegidos con
   un barajado parcial (un número por vacunado). Los 10 casos índice se eligen con el
   índice piso(R·N). A cada caso índice se le sortean su período infeccioso y si fallece.
3. **Cada día**, para cada infectado activo:
   - **Paso 1, contactos.** Un número R se compara con las probabilidades acumuladas de
     una Binomial(k, β/k) (transformada inversa). El resultado es el número de contactos,
     entre 0 y k, con media β.
   - **Paso 2, selección.** Por cada contacto, un número R elige al individuo: índice
     piso(R·|S|) sobre la lista de susceptibles, o piso(R·N) sobre toda la población en
     los escenarios de mezcla homogénea (si el elegido no es susceptible, el contacto no
     produce contagio).
   - **Paso 3, transmisión.** Un número R se compara con p_efectiva = p × factor, donde
     factor = 1 − efectividad si el individuo está vacunado y 1 en caso contrario. Si
     R < p_efectiva, el individuo pasa a E.
4. **Al exponerse**, tres números: período de incubación, período infeccioso y si
   fallecerá al salir de I (R < letalidad).

La progresión E → I e I → R es determinística: queda agendada en el día que resulta de
los períodos sorteados. Cada día se aplican primero las transiciones agendadas y después
los contagios.

### Independencia y reproducibilidad

Todas las réplicas de un escenario consumen una única secuencia continua: cada una empieza
donde terminó la anterior, por lo que los tramos no se solapan. El estado del generador al
iniciar cada réplica se guarda en la columna `semilla_inicial`; un generador creado con
esa semilla reproduce la réplica de forma exacta. Una réplica consume del orden de 10⁵
números, de modo que 1.000 réplicas usan menos del 5 % del período.

Con la semilla por defecto, los resultados son idénticos en cualquier equipo. Valores de
control con 1.000 réplicas: pico medio sin vacunación 5517.98; total medio de infectados
con vacunación 3282.24.

## Salidas

### `resultados/`

| Archivo | Contenido |
|---|---|
| `<escenario>_resumen.csv` | una fila por réplica: semilla, parámetros sorteados, pico, día del pico, total de infectados, tasa de ataque, muertes y día de control |
| `<escenario>_series.csv` | una fila por réplica y día: S, E, I, R y F (fallecidos acumulados, incluidos en R) |
| `sensibilidad.csv` | caso base y cada parámetro en su mínimo y su máximo |
| `tiempos.csv` | segundos por escenario y por réplica |
| `validacion_generador.csv` | media, varianza y chi-cuadrado de 100.000 números del generador |
| `estadisticas_descriptivas.csv` | media, desviación, IC 95 %, mínimo, cuartiles y máximo por escenario (lo crea el análisis) |
| `correlaciones_spearman.csv` | correlación de cada parámetro con el total de infectados y con el pico (lo crea el análisis, sin `scipy`) |

### `graficos/`

| Archivo | Contenido |
|---|---|
| `fig01_curva_epidemica_sin_vacunacion.png` | curvas S, E, I, R: media, IC 95 % de la media y percentiles 2.5–97.5 |
| `fig02_curva_epidemica_con_vacunacion.png` | lo mismo para el escenario con vacunación |
| `fig03_histogramas_resultados.png` | histogramas de pico, día del pico, total de infectados, muertes y días hasta el control |
| `fig04_comparacion_escenarios.png` | I(t) y S(t) con y sin vacunación |
| `fig05_sensibilidad_tornado.png` | tornado del total de infectados y del pico |
| `fig06_correlaciones_spearman.png` | correlación de Spearman de cada parámetro con los resultados |
| `fig07_extension_mezcla_homogenea.png` | total de infectados según la regla de selección del contacto |

## Funciones

### Módulos de simulación

| Función | Parámetros | Retorno |
|---|---|---|
| `PseudorandomGenerator` (`random.py`) | `seed`, `a`, `c`, `m` | objeto con `next()` y `state` |
| `read_config` (`config.py`) | `path` | diccionario `{parametro: (min, max)}` |
| `sample_params` (`config.py`) | `config`, `gen` | `ReplicaParams` |
| `build_contact_cdf` (`structures.py`) | `beta`, `k` | CDF de Binomial(k, β/k) |
| `sample_contact_count` (`structures.py`) | `gen`, `cdf` | número de contactos |
| `simulate_epidemic` (`simulation.py`) | `params`, `gen` | lista de `DailyRecord` |
| `EpidemicSimulation.run` (`simulation.py`) | — | serie diaria S, E, I, R y F |
| `summarize_replica` (`runner.py`) | `records`, `params`, `initial_seed` | métricas de una réplica |
| `run_scenario` (`runner.py`) | `config`, `semilla_base`, `n_replicas`, `gen`, `overwrite`, `verbose` | resúmenes, series y segundos |

### execute_episim.py (programa principal)

| Función | Papel |
|---|---|
| `validate_generator` | media, varianza y chi-cuadrado (10 intervalos) de 100.000 números |
| `sensitivity_analysis` | corre el caso base y los ocho casos mínimo/máximo, usando una secuencia continua del generador |
| `save_summary`, `save_series` | escriben los CSV de cada escenario |
| `peak_memory_mb` | memoria pico del proceso (solo disponible en Linux) |
| `main` | lee los argumentos y coordina todo |

### analisis_episim.py (generador de reportes)

| Función | Salida |
|---|---|
| `plot_curves` | fig01 y fig02 |
| `plot_histograms` | fig03 |
| `plot_comparison` | fig04 |
| `plot_tornado` | fig05 |
| `plot_correlations` | fig06 y `correlaciones_spearman.csv`, calculadas sobre rangos |
| `plot_homogeneous_comparison` | fig07 |
| `build_statistics_table` | `estadisticas_descriptivas.csv` |

## Decisiones de diseño

### Número de contactos

El enunciado propone contactos = piso(r × β_máximo). Como r < 1 y β ≤ 0.5, esa expresión
siempre da cero y la enfermedad no se propagaría. Se reemplazó por una Binomial(k, β/k)
con k = 4, generada por transformada inversa con un solo número: conserva β como promedio
de contactos por infectado y por día, y limita el máximo a k.

### Parámetros añadidos

El enunciado no los define y el modelo los necesita: `contactos_maximos_k` (para generar
contactos), `letalidad` (para estimar muertes) y `umbral_control` (para fijar cuándo la
epidemia se considera controlada). Sus valores son supuestos del grupo.

### Períodos en días

U(min, max) se redondea al entero más cercano. Con este redondeo los valores extremos
(2 y 5, 7 y 14) tienen la mitad de probabilidad que los intermedios; la media se conserva.

### Selección del contacto

Con `seleccion_solo_susceptibles = 1` se sigue el enunciado: cada contacto recae siempre
sobre un susceptible. En consecuencia, el contagio no se frena al agotarse los
susceptibles y, sin vacunación, se infecta toda la población. Con el valor 0 el contacto
se elige entre toda la población (mezcla homogénea) y solo contagia si el elegido es
susceptible. Los dos escenarios `_homogenea` permiten comparar ambas reglas.

### Vacunación

Los vacunados siguen siendo susceptibles; la vacuna reduce su probabilidad de contagio
por contacto en el factor 1 − efectividad.

### Métricas

- **Pico y día del pico:** máximo de infectados activos y primer día en que ocurre.
- **Total de infectados:** N − S final; incluye los casos índice.
- **Muertes:** fallecidos acumulados al día 365; se cuentan al pasar de I a R.
- **Día de control:** primer día posterior al pico con I ≤ `umbral_control`. Queda vacío
  si no se alcanza en 365 días; esas réplicas se excluyen de las estadísticas de control y
  se reportan como porcentaje aparte.
- **Brote mayor:** réplica con tasa de ataque de al menos 5 % de la población.

### Verificación

En cada día de cada réplica se comprueba que S + E + I + R = N; si no se cumple, la
ejecución se detiene.

### Análisis de sensibilidad

- **Tornado:** sobre el escenario con vacunación, cada parámetro (β, p, tasa de
  vacunación, efectividad) se lleva a su mínimo y a su máximo con los demás fijos en el
  punto medio de su rango.
- **Spearman:** correlación por rangos entre cada parámetro sorteado y el resultado, con
  las réplicas disponibles del escenario con vacunación. Se calcula usando `rank()` de
  pandas, por lo que no se necesita `scipy`.

### Intervalos de confianza

Las curvas muestran dos bandas: el IC 95 % de la media (media ± 1.96·s/√n) y los
percentiles 2.5 y 97.5 de las réplicas, que describen la variación entre réplicas.

## Limitaciones conocidas

- `memoria_pico_MB` en `tiempos.csv` vale 0.0 en Windows, porque el módulo `resource`
  solo existe en Linux.
- Con m par, R puede valer exactamente 1.0 cuando X = m − 1; el motor no protege los
  índices piso(R·n) frente a ese caso. Con la semilla por defecto no se alcanza ese valor.
- `validate_generator` es una comprobación rápida del generador. Las pruebas completas
  del generador se mantienen en `punto3_generadores_pseudoaleatorios`.
