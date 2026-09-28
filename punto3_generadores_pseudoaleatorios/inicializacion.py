import csv
from pathlib import Path

CAMPOS_POR_METODO = {
    "cuadrados_medios": ("semilla", "digitos", "cantidad"),
    "congruencial_lineal": ("semilla", "a", "c", "m", "cantidad"),
    "congruencial_multiplicativo": ("semilla", "a", "m", "cantidad"),
}


def convertir_campos_a_enteros(fila, campos):
    fila_convertida = {"metodo": fila["metodo"]}
    errores = []
    for campo in campos:
        valor = fila.get(campo)
        texto = "" if valor is None else str(valor).strip()
        try:
            fila_convertida[campo] = int(texto)
        except ValueError:
            errores.append(f"El campo '{campo}' debe ser un número entero (se recibió '{texto}').")
    return fila_convertida, errores


def validar_fila_de_semilla(fila):
    metodo = str(fila.get("metodo") or "").strip()
    if metodo not in CAMPOS_POR_METODO:
        return None, [f"Método desconocido: '{metodo}'. Use cuadrados_medios, congruencial_lineal o congruencial_multiplicativo."]
    fila_convertida, errores = convertir_campos_a_enteros({**fila, "metodo": metodo}, CAMPOS_POR_METODO[metodo])
    if errores:
        return None, errores
    if fila_convertida["cantidad"] <= 0:
        errores.append("La cantidad de números debe ser mayor que 0.")
    if fila_convertida["semilla"] < 0:
        errores.append("La semilla no puede ser negativa.")
    if metodo == "cuadrados_medios":
        cantidad_de_digitos = fila_convertida["digitos"]
        if cantidad_de_digitos < 2 or cantidad_de_digitos % 2 == 1:
            errores.append("El número de dígitos debe ser par y mayor o igual a 2.")
        elif fila_convertida["semilla"] >= 10 ** cantidad_de_digitos:
            errores.append(f"La semilla debe tener como máximo {cantidad_de_digitos} dígitos.")
    else:
        if fila_convertida["a"] <= 0:
            errores.append("El multiplicador a debe ser mayor que 0.")
        if fila_convertida["m"] <= fila_convertida["semilla"]:
            errores.append("El módulo m debe ser mayor que la semilla.")
    if metodo == "congruencial_lineal" and fila_convertida["c"] < 0:
        errores.append("El incremento c no puede ser negativo.")
    if metodo == "congruencial_multiplicativo" and fila_convertida["semilla"] == 0:
        errores.append("En el congruencial multiplicativo la semilla debe ser mayor que 0.")
    if errores:
        return None, errores
    return fila_convertida, []


def leer_archivo_de_semillas(ruta_del_archivo):
    ruta = Path(ruta_del_archivo)
    if ruta.suffix.lower() not in (".csv", ".txt"):
        return [], ["El archivo de semillas debe tener extensión .csv o .txt."]
    try:
        lineas = ruta.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        return [], [f"No se pudo leer el archivo: {error}"]
    if len(lineas) < 2:
        return [], ["El archivo no tiene filas de semillas debajo del encabezado."]
    separador = ";" if ";" in lineas[0] and "," not in lineas[0] else ","
    filas_validas = []
    errores = []
    for numero_de_fila, fila in enumerate(csv.DictReader(lineas, delimiter=separador), start=2):
        fila_convertida, errores_de_la_fila = validar_fila_de_semilla(fila)
        if errores_de_la_fila:
            errores.append(f"Fila {numero_de_fila}: " + " ".join(errores_de_la_fila))
        else:
            filas_validas.append(fila_convertida)
    return filas_validas, errores
