import math
from statistics import NormalDist

from punto3_generadores_pseudoaleatorios.generadores import truncar_a_cinco_decimales

NIVEL_DE_SIGNIFICANCIA = 0.05
VALOR_Z = truncar_a_cinco_decimales(NormalDist().inv_cdf(1 - NIVEL_DE_SIGNIFICANCIA / 2))
PROBABILIDADES_DE_POKER = {
    "Todos diferentes": 0.3024,
    "Un par": 0.5040,
    "Dos pares": 0.1080,
    "Tercia": 0.0720,
    "Full": 0.0090,
    "Póker": 0.0045,
    "Quintilla": 0.0001,
}
CATEGORIA_POR_REPETICIONES = {
    (1, 1, 1, 1, 1): "Todos diferentes",
    (2, 1, 1, 1): "Un par",
    (2, 2, 1): "Dos pares",
    (3, 1, 1): "Tercia",
    (3, 2): "Full",
    (4, 1): "Póker",
    (5,): "Quintilla",
}


def probabilidad_acumulada_chi_cuadrado(valor_x, grados_de_libertad):
    if valor_x <= 0:
        return 0.0
    parametro_de_forma = grados_de_libertad / 2
    mitad_de_x = valor_x / 2
    logaritmo_del_factor_comun = -mitad_de_x + parametro_de_forma * math.log(mitad_de_x) - math.lgamma(parametro_de_forma)
    if mitad_de_x < parametro_de_forma + 1:
        termino_de_la_serie = 1 / parametro_de_forma
        suma_de_la_serie = termino_de_la_serie
        denominador = parametro_de_forma
        while termino_de_la_serie > suma_de_la_serie * 1e-15:
            denominador += 1
            termino_de_la_serie *= mitad_de_x / denominador
            suma_de_la_serie += termino_de_la_serie
        return suma_de_la_serie * math.exp(logaritmo_del_factor_comun)
    coeficiente_b = mitad_de_x + 1 - parametro_de_forma
    coeficiente_c = 1e300
    coeficiente_d = 1 / coeficiente_b
    fraccion_continua = coeficiente_d
    numero_de_termino = 1
    while True:
        coeficiente_a = -numero_de_termino * (numero_de_termino - parametro_de_forma)
        coeficiente_b += 2
        coeficiente_d = 1 / (coeficiente_a * coeficiente_d + coeficiente_b)
        coeficiente_c = coeficiente_b + coeficiente_a / coeficiente_c
        factor_de_ajuste = coeficiente_d * coeficiente_c
        fraccion_continua *= factor_de_ajuste
        if abs(factor_de_ajuste - 1) < 1e-15:
            break
        numero_de_termino += 1
    return 1 - math.exp(logaritmo_del_factor_comun) * fraccion_continua


def valor_critico_chi_cuadrado(probabilidad_acumulada, grados_de_libertad):
    limite_inferior = 0.0
    limite_superior = grados_de_libertad + 10 * math.sqrt(2 * grados_de_libertad) + 10
    for _ in range(100):
        punto_medio = (limite_inferior + limite_superior) / 2
        if probabilidad_acumulada_chi_cuadrado(punto_medio, grados_de_libertad) < probabilidad_acumulada:
            limite_inferior = punto_medio
        else:
            limite_superior = punto_medio
    return truncar_a_cinco_decimales((limite_inferior + limite_superior) / 2)


def cantidad_de_intervalos_por_defecto(cantidad_de_numeros):
    return max(2, round(math.sqrt(cantidad_de_numeros)))


def calcular_estadistico_chi_cuadrado(frecuencias_observadas, frecuencias_esperadas):
    return truncar_a_cinco_decimales(
        sum(
            (frecuencia_observada - frecuencia_esperada) ** 2 / frecuencia_esperada
            for frecuencia_observada, frecuencia_esperada in zip(frecuencias_observadas, frecuencias_esperadas)
        )
    )


def contar_frecuencias_por_intervalo(numeros_r, cantidad_de_intervalos):
    frecuencias_observadas = [0] * cantidad_de_intervalos
    for numero_r in numeros_r:
        indice_del_intervalo = round(numero_r * 100000) * cantidad_de_intervalos // 100000
        frecuencias_observadas[min(indice_del_intervalo, cantidad_de_intervalos - 1)] += 1
    return frecuencias_observadas


def obtener_limites_de_intervalos(cantidad_de_intervalos):
    return [
        (truncar_a_cinco_decimales(indice / cantidad_de_intervalos), truncar_a_cinco_decimales((indice + 1) / cantidad_de_intervalos))
        for indice in range(cantidad_de_intervalos)
    ]


def prueba_de_medias(numeros_r):
    cantidad_de_numeros = len(numeros_r)
    media = truncar_a_cinco_decimales(sum(numeros_r) / cantidad_de_numeros)
    margen_de_aceptacion = VALOR_Z * math.sqrt(1 / 12) / math.sqrt(cantidad_de_numeros)
    limite_inferior = truncar_a_cinco_decimales(0.5 - margen_de_aceptacion)
    limite_superior = truncar_a_cinco_decimales(0.5 + margen_de_aceptacion)
    return {
        "prueba": "Medias",
        "estadistico": media,
        "valor_critico": VALOR_Z,
        "pasa": limite_inferior <= media <= limite_superior,
        "avisos": [],
        "limite_inferior": limite_inferior,
        "limite_superior": limite_superior,
        "valor_esperado": 0.5,
    }


def prueba_de_varianza(numeros_r):
    cantidad_de_numeros = len(numeros_r)
    grados_de_libertad = cantidad_de_numeros - 1
    media = sum(numeros_r) / cantidad_de_numeros
    varianza = truncar_a_cinco_decimales(sum((numero_r - media) ** 2 for numero_r in numeros_r) / grados_de_libertad)
    chi_cuadrado_inferior = valor_critico_chi_cuadrado(NIVEL_DE_SIGNIFICANCIA / 2, grados_de_libertad)
    chi_cuadrado_superior = valor_critico_chi_cuadrado(1 - NIVEL_DE_SIGNIFICANCIA / 2, grados_de_libertad)
    limite_inferior = truncar_a_cinco_decimales(chi_cuadrado_inferior / (12 * grados_de_libertad))
    limite_superior = truncar_a_cinco_decimales(chi_cuadrado_superior / (12 * grados_de_libertad))
    return {
        "prueba": "Varianza",
        "estadistico": varianza,
        "valor_critico": chi_cuadrado_superior,
        "pasa": limite_inferior <= varianza <= limite_superior,
        "avisos": [],
        "chi_cuadrado_inferior": chi_cuadrado_inferior,
        "chi_cuadrado_superior": chi_cuadrado_superior,
        "limite_inferior": limite_inferior,
        "limite_superior": limite_superior,
        "valor_esperado": truncar_a_cinco_decimales(1 / 12),
    }


def valor_critico_kolmogorov_smirnov(cantidad_de_numeros):
    raiz_de_n = math.sqrt(cantidad_de_numeros)
    if cantidad_de_numeros <= 50:
        coeficiente_de_la_tabla = math.sqrt(-math.log(NIVEL_DE_SIGNIFICANCIA / 2) / 2)
        return truncar_a_cinco_decimales(coeficiente_de_la_tabla / (raiz_de_n + 0.12 + 0.11 / raiz_de_n))
    return truncar_a_cinco_decimales(1.36 / raiz_de_n)


def prueba_kolmogorov_smirnov(numeros_r, cantidad_de_intervalos):
    cantidad_de_numeros = len(numeros_r)
    frecuencias_observadas = contar_frecuencias_por_intervalo(numeros_r, cantidad_de_intervalos)
    frecuencias_obtenidas_acumuladas = []
    frecuencia_acumulada = 0
    for frecuencia_observada in frecuencias_observadas:
        frecuencia_acumulada += frecuencia_observada
        frecuencias_obtenidas_acumuladas.append(frecuencia_acumulada)
    s_x = [truncar_a_cinco_decimales(acumulada / cantidad_de_numeros) for acumulada in frecuencias_obtenidas_acumuladas]
    f_x = [truncar_a_cinco_decimales((indice + 1) / cantidad_de_intervalos) for indice in range(cantidad_de_intervalos)]
    diferencias = [truncar_a_cinco_decimales(abs(esperada - obtenida)) for esperada, obtenida in zip(f_x, s_x)]
    diferencia_maxima = max(diferencias)
    diferencia_maxima_permitida = valor_critico_kolmogorov_smirnov(cantidad_de_numeros)
    return {
        "prueba": "Kolmogorov-Smirnov",
        "estadistico": diferencia_maxima,
        "valor_critico": diferencia_maxima_permitida,
        "pasa": diferencia_maxima < diferencia_maxima_permitida,
        "avisos": [],
        "intervalos": obtener_limites_de_intervalos(cantidad_de_intervalos),
        "frecuencias_observadas": frecuencias_observadas,
        "s_x": s_x,
        "f_x": f_x,
        "diferencias": diferencias,
    }


def prueba_de_rachas(numeros_r):
    cantidad_de_numeros = len(numeros_r)
    signos = ["+" if actual > anterior else "-" for anterior, actual in zip(numeros_r, numeros_r[1:])]
    rachas_observadas = 1 + sum(1 for signo_anterior, signo_actual in zip(signos, signos[1:]) if signo_actual != signo_anterior)
    rachas_esperadas = (2 * cantidad_de_numeros - 1) / 3
    desviacion_de_rachas = math.sqrt((16 * cantidad_de_numeros - 29) / 90)
    estadistico_z = truncar_a_cinco_decimales((rachas_observadas - rachas_esperadas) / desviacion_de_rachas)
    return {
        "prueba": "Rachas",
        "estadistico": estadistico_z,
        "valor_critico": VALOR_Z,
        "pasa": -VALOR_Z <= estadistico_z <= VALOR_Z,
        "avisos": [],
        "rachas_observadas": rachas_observadas,
        "rachas_esperadas": truncar_a_cinco_decimales(rachas_esperadas),
        "limite_inferior": truncar_a_cinco_decimales(rachas_esperadas - VALOR_Z * desviacion_de_rachas),
        "limite_superior": truncar_a_cinco_decimales(rachas_esperadas + VALOR_Z * desviacion_de_rachas),
    }


def prueba_chi_cuadrado(numeros_r, cantidad_de_intervalos):
    cantidad_de_numeros = len(numeros_r)
    frecuencias_observadas = contar_frecuencias_por_intervalo(numeros_r, cantidad_de_intervalos)
    frecuencia_esperada = truncar_a_cinco_decimales(cantidad_de_numeros / cantidad_de_intervalos)
    estadistico = calcular_estadistico_chi_cuadrado(frecuencias_observadas, [cantidad_de_numeros / cantidad_de_intervalos] * cantidad_de_intervalos)
    valor_critico = valor_critico_chi_cuadrado(1 - NIVEL_DE_SIGNIFICANCIA, cantidad_de_intervalos - 1)
    avisos = []
    if frecuencia_esperada < 5:
        avisos.append(f"La frecuencia esperada por intervalo ({frecuencia_esperada:.5f}) es menor que 5; la prueba pierde validez.")
    return {
        "prueba": "Chi-cuadrado",
        "estadistico": estadistico,
        "valor_critico": valor_critico,
        "pasa": estadistico < valor_critico,
        "avisos": avisos,
        "intervalos": obtener_limites_de_intervalos(cantidad_de_intervalos),
        "frecuencias_observadas": frecuencias_observadas,
        "frecuencia_esperada": frecuencia_esperada,
    }


def clasificar_mano_de_poker(numero_r):
    cinco_digitos = f"{numero_r:.5f}".split(".")[1]
    repeticiones = tuple(sorted((cinco_digitos.count(digito) for digito in set(cinco_digitos)), reverse=True))
    return CATEGORIA_POR_REPETICIONES[repeticiones]


def prueba_de_poker(numeros_r):
    cantidad_de_numeros = len(numeros_r)
    frecuencias_por_categoria = {categoria: 0 for categoria in PROBABILIDADES_DE_POKER}
    for numero_r in numeros_r:
        frecuencias_por_categoria[clasificar_mano_de_poker(numero_r)] += 1
    frecuencias_esperadas_sin_truncar = [cantidad_de_numeros * probabilidad for probabilidad in PROBABILIDADES_DE_POKER.values()]
    frecuencias_esperadas = [truncar_a_cinco_decimales(frecuencia) for frecuencia in frecuencias_esperadas_sin_truncar]
    estadistico = calcular_estadistico_chi_cuadrado(frecuencias_por_categoria.values(), frecuencias_esperadas_sin_truncar)
    valor_critico = valor_critico_chi_cuadrado(1 - NIVEL_DE_SIGNIFICANCIA, len(PROBABILIDADES_DE_POKER) - 1)
    categorias_con_pocas_esperadas = [
        categoria for categoria, frecuencia in zip(PROBABILIDADES_DE_POKER, frecuencias_esperadas) if frecuencia < 5
    ]
    avisos = []
    if categorias_con_pocas_esperadas:
        avisos.append("Frecuencia esperada menor que 5 en: " + ", ".join(categorias_con_pocas_esperadas) + ".")
    return {
        "prueba": "Póker",
        "estadistico": estadistico,
        "valor_critico": valor_critico,
        "pasa": estadistico < valor_critico,
        "avisos": avisos,
        "categorias": list(PROBABILIDADES_DE_POKER),
        "frecuencias_observadas": list(frecuencias_por_categoria.values()),
        "frecuencias_esperadas": frecuencias_esperadas,
    }
