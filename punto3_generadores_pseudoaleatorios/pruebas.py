import math

from punto3_generadores_pseudoaleatorios.generadores import truncar_a_cinco_decimales

NIVEL_DE_SIGNIFICANCIA = 0.05
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


def prueba_chi_cuadrado(numeros_r, cantidad_de_intervalos):
    cantidad_de_numeros = len(numeros_r)
    frecuencias_observadas = [0] * cantidad_de_intervalos
    for numero_r in numeros_r:
        indice_del_intervalo = round(numero_r * 100000) * cantidad_de_intervalos // 100000
        frecuencias_observadas[min(indice_del_intervalo, cantidad_de_intervalos - 1)] += 1
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
        "intervalos": [
            (truncar_a_cinco_decimales(indice / cantidad_de_intervalos), truncar_a_cinco_decimales((indice + 1) / cantidad_de_intervalos))
            for indice in range(cantidad_de_intervalos)
        ],
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
