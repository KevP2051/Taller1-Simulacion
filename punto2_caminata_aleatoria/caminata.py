from punto3_generadores_pseudoaleatorios import generadores

MULTIPLICADOR = 16807
MODULO = 2147483647
PASOS_RETORNO = 1000

MOVIMIENTOS_2D = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]
MOVIMIENTOS_3D = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]


def generar_numeros(semilla, cantidad):
    secuencia = generadores.generar_congruencial_multiplicativo(semilla, MULTIPLICADOR, MODULO, cantidad)
    return secuencia["numeros_r"]


def caminata_1d(semilla, pasos):
    numeros = generar_numeros(semilla, pasos)
    x = 0
    retorno = False
    for paso, r in enumerate(numeros, start=1):
        if r < 0.5:
            x += 1
        else:
            x -= 1
        if paso <= PASOS_RETORNO and x == 0:
            retorno = True
    return (x,), retorno


def caminata_2d(semilla, pasos):
    numeros = generar_numeros(semilla, pasos)
    x = 0
    y = 0
    retorno = False
    for paso, r in enumerate(numeros, start=1):
        dx, dy, dz = MOVIMIENTOS_2D[int(r * 4)]
        x += dx
        y += dy
        if paso <= PASOS_RETORNO and x == 0 and y == 0:
            retorno = True
    return (x, y), retorno


def caminata_3d(semilla, pasos):
    numeros = generar_numeros(semilla, pasos)
    x = 0
    y = 0
    z = 0
    retorno = False
    for paso, r in enumerate(numeros, start=1):
        dx, dy, dz = MOVIMIENTOS_3D[int(r * 6)]
        x += dx
        y += dy
        z += dz
        if paso <= PASOS_RETORNO and x == 0 and y == 0 and z == 0:
            retorno = True
    return (x, y, z), retorno


def trayectoria(dimension, semilla, pasos):
    """Devuelve las listas x, y, z de una caminata corta (para graficarla)."""
    numeros = generar_numeros(semilla, pasos)
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
    """P(S_n = 0) en 1D: C(n, n/2) / 2^n si n es par, 0 si es impar."""
    from math import comb
    if n % 2 == 1:
        return 0.0
    return comb(n, n // 2) / 2 ** n