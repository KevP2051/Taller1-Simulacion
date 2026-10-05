import math
from decimal import Decimal, ROUND_DOWN


def truncar_a_cinco_decimales(valor):
    return float(Decimal(repr(round(valor, 10))).quantize(Decimal("0.00001"), rounding=ROUND_DOWN))


def truncar_cociente_a_cinco_decimales(numerador, denominador):
    return (numerador * 100000) // denominador / 100000


def normalizar_con_modulo(valor_x, modulo_m):
    divisor = modulo_m if modulo_m % 2 == 1 else modulo_m - 1
    return truncar_cociente_a_cinco_decimales(valor_x, divisor)


def generar_cuadrados_medios(semilla, cantidad_de_digitos, cantidad_de_numeros):
    valores_x = []
    numeros_r = []
    avisos = []
    valores_vistos = {semilla}
    posicion_inicial = cantidad_de_digitos // 2
    semilla_actual = semilla
    while len(valores_x) < cantidad_de_numeros:
        cuadrado_con_ceros = str(semilla_actual * semilla_actual).zfill(2 * cantidad_de_digitos)
        siguiente_semilla = int(cuadrado_con_ceros[posicion_inicial:posicion_inicial + cantidad_de_digitos])
        posicion = len(valores_x) + 1
        if siguiente_semilla == 0:
            avisos.append(f"La secuencia colapsó a cero en la posición {posicion}; se detuvo la generación.")
            break
        if siguiente_semilla in valores_vistos:
            avisos.append(f"La secuencia entró en un ciclo en la posición {posicion}; se detuvo la generación.")
            break
        valores_vistos.add(siguiente_semilla)
        valores_x.append(siguiente_semilla)
        numeros_r.append(truncar_cociente_a_cinco_decimales(siguiente_semilla, 10 ** cantidad_de_digitos))
        semilla_actual = siguiente_semilla
    return {
        "metodo": "cuadrados_medios",
        "etiqueta": f"Cuadrados medios (X0 = {semilla}, {cantidad_de_digitos} dígitos)",
        "parametros": {"semilla": semilla, "digitos": cantidad_de_digitos, "cantidad": cantidad_de_numeros},
        "valores_x": valores_x,
        "numeros_r": numeros_r,
        "periodo": None,
        "hull_dobell": None,
        "avisos": avisos,
    }


def obtener_factores_primos(numero):
    factores_primos = []
    divisor = 2
    while divisor * divisor <= numero:
        if numero % divisor == 0:
            factores_primos.append(divisor)
            while numero % divisor == 0:
                numero //= divisor
        divisor += 1
    if numero > 1:
        factores_primos.append(numero)
    return factores_primos


def verificar_hull_dobell(multiplicador_a, incremento_c, modulo_m):
    condicion_c_y_m_primos_entre_si = math.gcd(incremento_c, modulo_m) == 1
    condicion_factores_primos_de_m = all(
        (multiplicador_a - 1) % factor_primo == 0 for factor_primo in obtener_factores_primos(modulo_m)
    )
    condicion_multiplo_de_4 = modulo_m % 4 != 0 or (multiplicador_a - 1) % 4 == 0
    return {
        "condicion_c_y_m_primos_entre_si": condicion_c_y_m_primos_entre_si,
        "condicion_factores_primos_de_m": condicion_factores_primos_de_m,
        "condicion_multiplo_de_4": condicion_multiplo_de_4,
        "cumple": condicion_c_y_m_primos_entre_si and condicion_factores_primos_de_m and condicion_multiplo_de_4,
    }


def generar_congruencial(metodo, etiqueta, semilla, multiplicador_a, incremento_c, modulo_m, cantidad_de_numeros):
    valores_x = []
    numeros_r = []
    avisos = []
    periodo = None
    semilla_actual = semilla
    for posicion in range(1, cantidad_de_numeros + 1):
        semilla_actual = (multiplicador_a * semilla_actual + incremento_c) % modulo_m
        valores_x.append(semilla_actual)
        numeros_r.append(normalizar_con_modulo(semilla_actual, modulo_m))
        if periodo is None and semilla_actual == semilla:
            periodo = posicion
    if periodo is not None:
        avisos.append(f"La secuencia volvió a la semilla en la posición {periodo}: período {periodo}; desde ahí los números se repiten.")
    return {
        "metodo": metodo,
        "etiqueta": etiqueta,
        "parametros": {"semilla": semilla, "a": multiplicador_a, "c": incremento_c, "m": modulo_m, "cantidad": cantidad_de_numeros},
        "valores_x": valores_x,
        "numeros_r": numeros_r,
        "periodo": periodo,
        "hull_dobell": None,
        "avisos": avisos,
    }


def generar_congruencial_lineal(semilla, multiplicador_a, incremento_c, modulo_m, cantidad_de_numeros):
    secuencia = generar_congruencial(
        "congruencial_lineal",
        f"Congruencial lineal (X0 = {semilla}, a = {multiplicador_a}, c = {incremento_c}, m = {modulo_m})",
        semilla,
        multiplicador_a,
        incremento_c,
        modulo_m,
        cantidad_de_numeros,
    )
    secuencia["hull_dobell"] = verificar_hull_dobell(multiplicador_a, incremento_c, modulo_m)
    if not secuencia["hull_dobell"]["cumple"]:
        secuencia["avisos"].append("Los parámetros no cumplen el teorema de Hull-Dobell: el período máximo no está garantizado.")
    return secuencia


def generar_congruencial_multiplicativo(semilla, multiplicador_a, modulo_m, cantidad_de_numeros):
    secuencia = generar_congruencial(
        "congruencial_multiplicativo",
        f"Congruencial multiplicativo (X0 = {semilla}, a = {multiplicador_a}, m = {modulo_m})",
        semilla,
        multiplicador_a,
        0,
        modulo_m,
        cantidad_de_numeros,
    )
    del secuencia["parametros"]["c"]
    return secuencia


def transformar_a_uniforme(numeros_r, limite_inferior, limite_superior):
    return [
        truncar_a_cinco_decimales(limite_inferior + (limite_superior - limite_inferior) * numero_r)
        for numero_r in numeros_r
    ]


def transformar_a_normal_estandar(numeros_r):
    numeros_normales = []
    avisos = []
    for posicion in range(0, len(numeros_r) - 1, 2):
        primer_numero_r = numeros_r[posicion]
        segundo_numero_r = numeros_r[posicion + 1]
        if primer_numero_r == 0:
            avisos.append(f"Se omitió el par de las posiciones {posicion + 1} y {posicion + 2} porque R = 0 (ln 0 no existe).")
            continue
        radio = math.sqrt(-2 * math.log(primer_numero_r))
        angulo = 2 * math.pi * segundo_numero_r
        numeros_normales.append(truncar_a_cinco_decimales(radio * math.cos(angulo)))
        numeros_normales.append(truncar_a_cinco_decimales(radio * math.sin(angulo)))
    if len(numeros_r) % 2 == 1:
        avisos.append(f"La cantidad de números es impar; el número de la posición {len(numeros_r)} no forma par y no se usó.")
    return {"numeros_normales": numeros_normales, "avisos": avisos}
