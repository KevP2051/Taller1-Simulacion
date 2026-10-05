import csv
import math
from itertools import zip_longest

from matplotlib.figure import Figure

from punto3_generadores_pseudoaleatorios.pruebas import cantidad_de_intervalos_por_defecto


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


def crear_figura_con_paneles(cantidad_de_paneles, titulo):
    columnas = math.ceil(math.sqrt(cantidad_de_paneles))
    filas = math.ceil(cantidad_de_paneles / columnas)
    figura = Figure(figsize=(max(6, 4.8 * columnas), 4 * filas), layout="constrained")
    figura.suptitle(titulo)
    paneles = figura.subplots(filas, columnas, squeeze=False).flatten()
    for panel_sobrante in paneles[cantidad_de_paneles:]:
        panel_sobrante.set_visible(False)
    return figura, paneles[:cantidad_de_paneles]


def crear_histograma_de_secuencia(secuencia):
    distribuciones = [("R_i en [0, 1]", secuencia["numeros_r"], (0, 1))]
    if "numeros_uniformes" in secuencia:
        limite_inferior, limite_superior = secuencia["limites_de_uniforme"]
        distribuciones.append(
            (f"N_i uniforme U({limite_inferior:g}, {limite_superior:g})", secuencia["numeros_uniformes"], (limite_inferior, limite_superior))
        )
    if "numeros_normales" in secuencia:
        distribuciones.append(("Z_i normal estándar N(0, 1)", secuencia["numeros_normales"], None))
    figura, paneles = crear_figura_con_paneles(len(distribuciones), f"Histograma de frecuencias:\n{acortar_etiqueta(secuencia['etiqueta'])}")
    for panel, (nombre_de_la_distribucion, valores, rango) in zip(paneles, distribuciones):
        panel.hist(valores, bins=cantidad_de_intervalos_por_defecto(len(valores)), range=rango, edgecolor="black")
        panel.set_title(nombre_de_la_distribucion)
        panel.set_xlabel("Valor")
        panel.set_ylabel("Frecuencia")
    return figura


def describir_criterio(resultado):
    if resultado["prueba"] in ("Medias", "Varianza"):
        return f"[{resultado['limite_inferior']:.5f}, {resultado['limite_superior']:.5f}]"
    return f"{resultado['valor_critico']:.5f}"


def describir_resultado(resultado):
    decision = "pasa" if resultado["pasa"] else "no pasa"
    return (
        f"{acortar_etiqueta(resultado['etiqueta'])}\n"
        f"Estadístico = {resultado['estadistico']:.5f}, criterio = {describir_criterio(resultado)}: {decision}"
    )


def acortar_etiqueta(etiqueta):
    return etiqueta.replace(" (", "\n(", 1).replace(", a =", ",\na =", 1)


def crear_grafico_de_distribucion_por_bloques(resultados, titulo, nombre_del_estadistico, nombre_del_valor_esperado):
    figura, paneles = crear_figura_con_paneles(len(resultados), titulo)
    for panel, resultado in zip(paneles, resultados):
        valores_por_bloque = resultado["valores_por_bloque"]
        limite_inferior_del_bloque, limite_superior_del_bloque = resultado["limites_por_bloque"]
        bloques_dentro = sum(1 for valor in valores_por_bloque if limite_inferior_del_bloque <= valor <= limite_superior_del_bloque)
        panel.axvspan(
            limite_inferior_del_bloque,
            limite_superior_del_bloque,
            color="tab:green",
            alpha=0.15,
            label=f"Intervalo de aceptación por bloque (95 %): {bloques_dentro} de {len(valores_por_bloque)} bloques dentro",
        )
        panel.hist(
            valores_por_bloque,
            bins=cantidad_de_intervalos_por_defecto(len(valores_por_bloque)),
            edgecolor="black",
            label=f"{nombre_del_estadistico} de {len(valores_por_bloque)} bloques de {resultado['tamano_del_bloque']} números",
        )
        panel.axvline(resultado["valor_esperado"], linestyle="--", color="tab:blue", label=f"{nombre_del_valor_esperado} = {resultado['valor_esperado']:.5f}")
        panel.axvline(
            resultado["estadistico"],
            color="tab:green" if resultado["pasa"] else "tab:red",
            linewidth=2,
            label=f"{nombre_del_estadistico} de la secuencia = {resultado['estadistico']:.5f}",
        )
        panel.set_xlabel(f"{nombre_del_estadistico} por bloque")
        panel.set_ylabel("Frecuencia (bloques)")
        panel.set_ylim(0, panel.get_ylim()[1] * 1.7)
        panel.legend(fontsize=7, loc="upper left")
        panel.set_title(describir_resultado(resultado), fontsize=9)
    return figura


def crear_grafico_de_medias(resultados):
    return crear_grafico_de_distribucion_por_bloques(
        resultados, "Prueba de medias: distribución de las medias por bloque", "Media", "Media teórica"
    )


def crear_grafico_de_varianzas(resultados):
    return crear_grafico_de_distribucion_por_bloques(
        resultados, "Prueba de varianza: distribución de las varianzas por bloque", "Varianza", "Varianza teórica 1/12"
    )


def crear_grafico_kolmogorov_smirnov(resultados):
    figura, paneles = crear_figura_con_paneles(len(resultados), "Prueba de Kolmogorov-Smirnov: S(x) empírica vs F(x) teórica")
    for panel, resultado in zip(paneles, resultados):
        limites_superiores = [0.0] + resultado["f_x"]
        panel.plot(limites_superiores, [0.0] + resultado["s_x"], drawstyle="steps-post", label="S(x) empírica acumulada")
        panel.plot([0, 1], [0, 1], linestyle="--", label="F(x) = x teórica")
        indice_maximo = resultado["diferencias"].index(resultado["estadistico"])
        posicion_x = resultado["f_x"][indice_maximo]
        valores_en_x = (resultado["s_x"][indice_maximo], resultado["f_x"][indice_maximo])
        panel.vlines(posicion_x, min(valores_en_x), max(valores_en_x), color="tab:red", linewidth=3, label=f"DMAX = {resultado['estadistico']:.5f}")
        panel.set_xlabel("x")
        panel.set_ylabel("Probabilidad acumulada")
        panel.legend(fontsize=8, loc="upper left")
        panel.set_title(describir_resultado(resultado), fontsize=9)
    return figura


def dibujar_barras_observadas_contra_esperadas(panel, nombres_de_las_barras, frecuencias_observadas, frecuencias_esperadas):
    posiciones = range(len(nombres_de_las_barras))
    ancho_de_barra = 0.4
    panel.bar([posicion - ancho_de_barra / 2 for posicion in posiciones], frecuencias_observadas, ancho_de_barra, label="Observadas")
    panel.bar([posicion + ancho_de_barra / 2 for posicion in posiciones], frecuencias_esperadas, ancho_de_barra, label="Esperadas")
    panel.set_xticks(list(posiciones), nombres_de_las_barras)
    panel.set_ylabel("Frecuencia")
    panel.legend(loc="upper right", fontsize=8)


def crear_grafico_chi_cuadrado(resultados):
    figura, paneles = crear_figura_con_paneles(len(resultados), "Prueba chi-cuadrado: frecuencias observadas vs esperadas")
    for panel, resultado in zip(paneles, resultados):
        cantidad_de_intervalos = len(resultado["frecuencias_observadas"])
        dibujar_barras_observadas_contra_esperadas(
            panel,
            [str(numero) for numero in range(1, cantidad_de_intervalos + 1)],
            resultado["frecuencias_observadas"],
            [resultado["frecuencia_esperada"]] * cantidad_de_intervalos,
        )
        if cantidad_de_intervalos > 20:
            panel.set_xticks([])
        panel.set_xlabel(f"Intervalo (k = {cantidad_de_intervalos})")
        panel.set_title(describir_resultado(resultado), fontsize=9)
    return figura


def crear_grafico_de_poker(resultados):
    figura, paneles = crear_figura_con_paneles(len(resultados), "Prueba de póker: manos observadas vs esperadas")
    for panel, resultado in zip(paneles, resultados):
        dibujar_barras_observadas_contra_esperadas(
            panel,
            resultado["categorias"],
            resultado["frecuencias_observadas"],
            resultado["frecuencias_esperadas"],
        )
        panel.tick_params(axis="x", labelrotation=45)
        panel.set_xlabel("Mano")
        panel.set_title(describir_resultado(resultado), fontsize=9)
    return figura
