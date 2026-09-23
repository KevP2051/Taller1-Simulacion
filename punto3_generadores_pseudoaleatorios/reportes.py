import csv
from itertools import zip_longest


def formatear_valor(valor):
    if isinstance(valor, float):
        return f"{valor:.5f}"
    return str(valor)


def obtener_columnas_de_secuencia(secuencia):
    columnas = {
        "i": list(range(1, len(secuencia["numeros_r"]) + 1)),
        "X_i": secuencia["valores_x"],
        "R_i": secuencia["numeros_r"],
    }
    if "numeros_uniformes" in secuencia:
        columnas["N_i"] = secuencia["numeros_uniformes"]
    if "numeros_normales" in secuencia:
        columnas["Z_i"] = secuencia["numeros_normales"]
    return columnas


def obtener_filas_de_secuencia(secuencia):
    columnas = obtener_columnas_de_secuencia(secuencia)
    filas = zip_longest(*columnas.values(), fillvalue="")
    return list(columnas.keys()), ([formatear_valor(valor) for valor in fila] for fila in filas)


def describir_secuencia(secuencia):
    lineas = [
        secuencia["etiqueta"],
        "Parámetros: " + ", ".join(f"{nombre} = {valor}" for nombre, valor in secuencia["parametros"].items()),
        f"Números generados: {len(secuencia['numeros_r'])}",
    ]
    if secuencia["hull_dobell"] is not None:
        hull_dobell = secuencia["hull_dobell"]
        lineas.append(
            "Hull-Dobell: "
            f"c y m primos entre sí: {'sí' if hull_dobell['condicion_c_y_m_primos_entre_si'] else 'no'}; "
            f"a − 1 divisible por los factores primos de m: {'sí' if hull_dobell['condicion_factores_primos_de_m'] else 'no'}; "
            f"a − 1 múltiplo de 4 si m lo es: {'sí' if hull_dobell['condicion_multiplo_de_4'] else 'no'}; "
            f"{'cumple' if hull_dobell['cumple'] else 'no cumple'}"
        )
    if "limites_de_uniforme" in secuencia:
        limite_inferior, limite_superior = secuencia["limites_de_uniforme"]
        lineas.append(f"Uniforme U({limite_inferior:g}, {limite_superior:g}): N_i = a + (b − a)·R_i")
    if "numeros_normales" in secuencia:
        lineas.append(f"Normal estándar N(0, 1) por Box-Muller: {len(secuencia['numeros_normales'])} números")
    lineas.extend(f"Aviso: {aviso}" for aviso in secuencia["avisos"])
    return "\n".join(lineas)


def exportar_secuencia_a_csv(secuencia, ruta_del_archivo):
    encabezados, filas = obtener_filas_de_secuencia(secuencia)
    with open(ruta_del_archivo, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(encabezados)
        escritor.writerows(filas)
