import csv
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
    figura = Figure(figsize=(max(6, 5 * cantidad_de_paneles), 4.5), layout="constrained")
    figura.suptitle(titulo)
    return figura, figura.subplots(1, cantidad_de_paneles, squeeze=False)[0]


def crear_histograma_de_secuencia(secuencia):
    distribuciones = [("R_i en [0, 1]", secuencia["numeros_r"], (0, 1))]
    if "numeros_uniformes" in secuencia:
        limite_inferior, limite_superior = secuencia["limites_de_uniforme"]
        distribuciones.append(
            (f"N_i uniforme U({limite_inferior:g}, {limite_superior:g})", secuencia["numeros_uniformes"], (limite_inferior, limite_superior))
        )
    if "numeros_normales" in secuencia:
        distribuciones.append(("Z_i normal estándar N(0, 1)", secuencia["numeros_normales"], None))
    figura, paneles = crear_figura_con_paneles(len(distribuciones), f"Histograma de frecuencias: {secuencia['etiqueta']}")
    for panel, (nombre_de_la_distribucion, valores, rango) in zip(paneles, distribuciones):
        panel.hist(valores, bins=cantidad_de_intervalos_por_defecto(len(valores)), range=rango, edgecolor="black")
        panel.set_title(nombre_de_la_distribucion)
        panel.set_xlabel("Valor")
        panel.set_ylabel("Frecuencia")
    return figura


def describir_criterio(resultado):
    if resultado["prueba"] in ("Medias", "Varianza"):
        return f"[{resultado['limite_inferior']:.5f}, {resultado['limite_superior']:.5f}]"
    if resultado["prueba"] == "Rachas":
        return f"±{resultado['valor_critico']:.5f}"
    return f"{resultado['valor_critico']:.5f}"


def describir_resultado(resultado):
    decision = "pasa" if resultado["pasa"] else "no pasa"
    etiqueta_en_dos_lineas = resultado["etiqueta"].replace(" (", "\n(", 1)
    return (
        f"{etiqueta_en_dos_lineas}\n"
        f"Estadístico = {resultado['estadistico']:.5f}, criterio = {describir_criterio(resultado)}: {decision}"
    )


def acortar_etiqueta(etiqueta):
    return etiqueta.replace(" (", "\n(", 1).replace(", a =", ",\na =", 1)


def crear_grafico_de_intervalos(resultados, titulo, nombre_del_estadistico, nombre_del_valor_esperado):
    figura = Figure(figsize=(max(7, 2.8 * len(resultados)), 5.5), layout="constrained")
    figura.suptitle(titulo)
    panel = figura.subplots()
    posiciones = list(range(len(resultados)))
    valor_esperado = resultados[0]["valor_esperado"]
    panel.errorbar(
        posiciones,
        [valor_esperado] * len(resultados),
        yerr=[
            [valor_esperado - resultado["limite_inferior"] for resultado in resultados],
            [resultado["limite_superior"] - valor_esperado for resultado in resultados],
        ],
        fmt="none",
        capsize=10,
        color="gray",
        label="Intervalo de aceptación (95 %)",
    )
    for posicion, resultado in zip(posiciones, resultados):
        panel.scatter(posicion, resultado["estadistico"], s=70, zorder=3, color="tab:green" if resultado["pasa"] else "tab:red")
        panel.annotate(f"{resultado['estadistico']:.5f}", (posicion, resultado["estadistico"]), textcoords="offset points", xytext=(12, 0), va="center")
    panel.axhline(valor_esperado, linestyle="--", color="tab:blue", label=f"{nombre_del_valor_esperado} = {valor_esperado:.5f}")
    panel.scatter([], [], color="tab:green", label=f"{nombre_del_estadistico} (pasa)")
    panel.scatter([], [], color="tab:red", label=f"{nombre_del_estadistico} (no pasa)")
    panel.set_xticks(posiciones, [acortar_etiqueta(resultado["etiqueta"]) for resultado in resultados], fontsize=8)
    panel.set_xlim(-0.6, len(resultados) - 0.4)
    panel.set_ylabel(nombre_del_estadistico)
    panel.legend(fontsize=8)
    return figura


def crear_grafico_de_medias(resultados):
    return crear_grafico_de_intervalos(resultados, "Prueba de medias: media de cada método vs intervalo de aceptación", "Media", "Media teórica")


def crear_grafico_de_varianzas(resultados):
    return crear_grafico_de_intervalos(resultados, "Prueba de varianza: varianza de cada método vs intervalo de aceptación", "Varianza", "Varianza teórica 1/12")


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


def crear_grafico_de_rachas(resultados):
    figura, paneles = crear_figura_con_paneles(len(resultados), "Prueba de rachas: rachas observadas vs esperadas")
    for panel, resultado in zip(paneles, resultados):
        rachas_esperadas = resultado["rachas_esperadas"]
        panel.bar([0], [resultado["rachas_observadas"]], 0.5, label="Observadas")
        panel.bar(
            [1],
            [rachas_esperadas],
            0.5,
            yerr=[[rachas_esperadas - resultado["limite_inferior"]], [resultado["limite_superior"] - rachas_esperadas]],
            capsize=12,
            label=f"Esperadas con intervalo [{resultado['limite_inferior']:.5f}, {resultado['limite_superior']:.5f}]",
        )
        panel.set_xticks([0, 1], ["Observadas", "Esperadas"])
        panel.set_ylabel("Cantidad de rachas")
        panel.set_ylim(0, 1.3 * max(resultado["rachas_observadas"], resultado["limite_superior"]))
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
