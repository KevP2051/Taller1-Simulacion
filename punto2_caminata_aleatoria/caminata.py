from punto3_generadores_pseudoaleatorios import generadores

# Generador congruencial multiplicativo: X(i+1) = (16807 * X(i)) mod (2^31 - 1)
MULTIPLICADOR = 16807
MODULO = 2147483647
# Hay retorno si la rana pasa por el origen en algún paso <= 1000
PASOS_RETORNO = 1000

# Desplazamientos (dx, dy, dz) con igual probabilidad; en 2D dz es siempre 0
MOVIMIENTOS_2D = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
MOVIMIENTOS_3D = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]


def generar_numeros(semilla, cantidad):
    # Genera una secuencia pseudoaleatoria normalizada en el intervalo [0, 1).
    # La semilla determina el estado inicial y cantidad define la longitud.
    # Números R_i en [0, 1) del generador del Punto 3 (solo se usa numeros_r)
    secuencia = generadores.generar_congruencial_multiplicativo(semilla, MULTIPLICADOR, MODULO, cantidad)
    return secuencia["numeros_r"]


def caminata_1d(semilla, pasos):
    # Simula una caminata aleatoria unidimensional desde el origen.
    # Retorna la posición final y un indicador de retorno durante los primeros pasos.
    numeros = generar_numeros(semilla, pasos)
    x = 0
    retorno = False
    for paso, r in enumerate(numeros, start=1):
        # R < 0.5 -> +1, en otro caso -> -1 (probabilidad 1/2 cada uno)
        if r < 0.5:
            x += 1
        else:
            x -= 1
        # Retorno acumulado: basta con que ocurra una vez en los primeros 1000 pasos
        if paso <= PASOS_RETORNO and x == 0:
            retorno = True
    return (x,), retorno


def caminata_2d(semilla, pasos):
    # Simula una caminata aleatoria bidimensional con movimientos cardinales.
    # Cada número aleatorio se transforma en una dirección del plano.
    numeros = generar_numeros(semilla, pasos)
    x = 0
    y = 0
    retorno = False
    for paso, r in enumerate(numeros, start=1):
        # int(r * 4) elige una de las 4 direcciones
        dx, dy, dz = MOVIMIENTOS_2D[int(r * 4)]
        x += dx
        y += dy
        if paso <= PASOS_RETORNO and x == 0 and y == 0:
            retorno = True
    return (x, y), retorno


def caminata_3d(semilla, pasos):
    # Simula una caminata aleatoria tridimensional sobre los ejes cartesianos.
    # Cada número aleatorio se transforma en una de las seis direcciones posibles.
    numeros = generar_numeros(semilla, pasos)
    x = 0
    y = 0
    z = 0
    retorno = False
    for paso, r in enumerate(numeros, start=1):
        # int(r * 6) elige una de las 6 direcciones
        dx, dy, dz = MOVIMIENTOS_3D[int(r * 6)]
        x += dx
        y += dy
        z += dz
        if paso <= PASOS_RETORNO and x == 0 and y == 0 and z == 0:
            retorno = True
    return (x, y, z), retorno


def trayectoria(dimension, semilla, pasos):
    # Construye las coordenadas acumuladas de la caminata para su representación gráfica.
    # La salida siempre contiene listas para x, y y z, incluso en una dimensión.
    numeros = generar_numeros(semilla, pasos)
    # En 1D, y y z se devuelven como ceros para graficar con el mismo código
    if dimension == 1:
        lista_x = [0]
        for r in numeros:
            lista_x.append(lista_x[-1] + (1 if r < 0.5 else -1))
        return lista_x, [0] * len(lista_x), [0] * len(lista_x)
    # Se guarda todo el recorrido (usar solo con pocos pasos)
    movimientos = MOVIMIENTOS_2D if dimension == 2 else MOVIMIENTOS_3D
    x, y, z = 0, 0, 0
    lista_x, lista_y, lista_z = [0], [0], [0]
    for r in numeros:
        dx, dy, dz = movimientos[int(r * len(movimientos))]
        x += dx
        y += dy
        z += dz
        lista_x.append(x)
        lista_y.append(y)
        lista_z.append(z)
    return lista_x, lista_y, lista_z


def probabilidad_exacta_retorno(n):
    # Calcula la probabilidad exacta de que una caminata 1D termine en el origen.
    # Para n impar, la paridad hace imposible que la posición final sea cero.
    from math import comb
    # Con n impar el retorno exacto es imposible
    if n % 2 == 1:
        return 0.0
    return comb(n, n // 2) / 2 ** n


def encadenar_semillas(semilla_inicial, cantidad_de_semillas, pasos):
    # Construye una semilla para cada réplica a partir del estado final anterior.
    # El avance de pasos estados evita reutilizar bloques de números aleatorios.
    semillas = [semilla_inicial]
    x = semilla_inicial
    for _ in range(cantidad_de_semillas - 1):
        # Avanza el generador `pasos` veces: la semilla siguiente es el estado final de la réplica
        for _ in range(pasos):
            x = (MULTIPLICADOR * x) % MODULO
        semillas.append(x)
    return semillas