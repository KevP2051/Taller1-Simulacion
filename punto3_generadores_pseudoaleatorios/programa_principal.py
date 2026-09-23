import tkinter as tk
from itertools import islice
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from punto3_generadores_pseudoaleatorios import generadores, inicializacion, pruebas, reportes

NOMBRES_DE_METODOS = {
    "Cuadrados medios": "cuadrados_medios",
    "Congruencial lineal": "congruencial_lineal",
    "Congruencial multiplicativo": "congruencial_multiplicativo",
}
CAMPOS_DE_GENERACION = (
    ("semilla", "Semilla", "7"),
    ("digitos", "Dígitos", "4"),
    ("a", "a", "1601"),
    ("c", "c", "3701"),
    ("m", "m", "10000"),
    ("cantidad", "Cantidad", "1000"),
)
MAXIMO_DE_FILAS_EN_TABLA = 1000
GRAFICOS_DE_PRUEBAS = {
    "Medias": reportes.crear_grafico_de_medias,
    "Varianza": reportes.crear_grafico_de_varianzas,
    "Chi-cuadrado": reportes.crear_grafico_chi_cuadrado,
    "Kolmogorov-Smirnov": reportes.crear_grafico_kolmogorov_smirnov,
    "Póker": reportes.crear_grafico_de_poker,
    "Rachas": reportes.crear_grafico_de_rachas,
}
PRUEBAS_DISPONIBLES = {
    "Medias": lambda numeros_r, cantidad_de_intervalos: pruebas.prueba_de_medias(numeros_r),
    "Varianza": lambda numeros_r, cantidad_de_intervalos: pruebas.prueba_de_varianza(numeros_r),
    "Chi-cuadrado": lambda numeros_r, cantidad_de_intervalos: pruebas.prueba_chi_cuadrado(numeros_r, cantidad_de_intervalos),
    "Kolmogorov-Smirnov": lambda numeros_r, cantidad_de_intervalos: pruebas.prueba_kolmogorov_smirnov(numeros_r, cantidad_de_intervalos),
    "Póker": lambda numeros_r, cantidad_de_intervalos: pruebas.prueba_de_poker(numeros_r),
    "Rachas": lambda numeros_r, cantidad_de_intervalos: pruebas.prueba_de_rachas(numeros_r),
}

secuencias_generadas = []
componentes = {}


def generar_secuencia_desde_fila(fila):
    if fila["metodo"] == "cuadrados_medios":
        return generadores.generar_cuadrados_medios(fila["semilla"], fila["digitos"], fila["cantidad"])
    if fila["metodo"] == "congruencial_lineal":
        return generadores.generar_congruencial_lineal(fila["semilla"], fila["a"], fila["c"], fila["m"], fila["cantidad"])
    return generadores.generar_congruencial_multiplicativo(fila["semilla"], fila["a"], fila["m"], fila["cantidad"])


def agregar_secuencia(fila, limites_de_uniforme, incluir_normal):
    secuencia = generar_secuencia_desde_fila(fila)
    if limites_de_uniforme is not None:
        secuencia["limites_de_uniforme"] = limites_de_uniforme
        secuencia["numeros_uniformes"] = generadores.transformar_a_uniforme(secuencia["numeros_r"], *limites_de_uniforme)
    if incluir_normal:
        transformacion_normal = generadores.transformar_a_normal_estandar(secuencia["numeros_r"])
        secuencia["numeros_normales"] = transformacion_normal["numeros_normales"]
        secuencia["avisos"].extend(transformacion_normal["avisos"])
    secuencias_generadas.append(secuencia)
    return secuencia


def leer_fila_de_campos():
    fila = {"metodo": NOMBRES_DE_METODOS[componentes["metodo"].get()]}
    for nombre_del_campo, _, _ in CAMPOS_DE_GENERACION:
        fila[nombre_del_campo] = componentes["campos"][nombre_del_campo].get()
    return fila


def leer_opciones_de_transformacion():
    if not componentes["incluir_uniforme"].get():
        return None, []
    try:
        limite_inferior = float(componentes["limite_inferior"].get())
        limite_superior = float(componentes["limite_superior"].get())
    except ValueError:
        return None, ["Los límites de la uniforme U(a, b) deben ser números."]
    if limite_inferior >= limite_superior:
        return None, ["En la uniforme U(a, b) el límite inferior debe ser menor que el superior."]
    return (limite_inferior, limite_superior), []


def actualizar_campos_habilitados(evento=None):
    campos_del_metodo = inicializacion.CAMPOS_POR_METODO[NOMBRES_DE_METODOS[componentes["metodo"].get()]]
    for nombre_del_campo, campo in componentes["campos"].items():
        campo.state(["!disabled"] if nombre_del_campo in campos_del_metodo else ["disabled"])


def actualizar_lista_de_secuencias(indice_a_elegir=None):
    lista = componentes["lista_de_secuencias"]
    lista.delete(*lista.get_children())
    for indice, secuencia in enumerate(secuencias_generadas):
        lista.insert("", "end", iid=str(indice), values=(secuencia["etiqueta"], len(secuencia["numeros_r"]), len(secuencia["avisos"])))
    secuencias_con_numeros = [secuencia for secuencia in secuencias_generadas if secuencia["numeros_r"]]
    if secuencias_con_numeros:
        cantidad_minima = min(len(secuencia["numeros_r"]) for secuencia in secuencias_con_numeros)
        componentes["cantidad_de_intervalos"].delete(0, "end")
        componentes["cantidad_de_intervalos"].insert(0, str(pruebas.cantidad_de_intervalos_por_defecto(cantidad_minima)))
    if indice_a_elegir is not None and secuencias_generadas:
        lista.selection_set(str(indice_a_elegir))
        lista.see(str(indice_a_elegir))
    else:
        mostrar_secuencia_elegida()


def obtener_indice_elegido():
    seleccion = componentes["lista_de_secuencias"].selection()
    return int(seleccion[0]) if seleccion else None


def mostrar_secuencia_elegida(evento=None):
    tabla = componentes["tabla"]
    tabla.delete(*tabla.get_children())
    indice_elegido = obtener_indice_elegido()
    if indice_elegido is None:
        tabla["columns"] = ()
        componentes["detalle"].set("")
        return
    secuencia = secuencias_generadas[indice_elegido]
    encabezados, filas = reportes.obtener_filas_de_secuencia(secuencia)
    tabla["columns"] = encabezados
    for encabezado in encabezados:
        tabla.heading(encabezado, text=encabezado)
        tabla.column(encabezado, width=90, anchor="e")
    for fila in islice(filas, MAXIMO_DE_FILAS_EN_TABLA):
        tabla.insert("", "end", values=fila)
    detalle = reportes.describir_secuencia(secuencia)
    if len(secuencia["numeros_r"]) > MAXIMO_DE_FILAS_EN_TABLA:
        detalle += f"\nLa tabla muestra las primeras {MAXIMO_DE_FILAS_EN_TABLA} filas; el archivo CSV exportado contiene todas."
    componentes["detalle"].set(detalle)


def generar_desde_campos():
    fila, errores = inicializacion.validar_fila_de_semilla(leer_fila_de_campos())
    limites_de_uniforme, errores_de_uniforme = leer_opciones_de_transformacion()
    errores = errores + errores_de_uniforme
    if errores:
        messagebox.showerror("Datos inválidos", "\n".join(errores))
        return
    agregar_secuencia(fila, limites_de_uniforme, componentes["incluir_normal"].get())
    actualizar_lista_de_secuencias(len(secuencias_generadas) - 1)


def cargar_archivo_de_semillas():
    ruta_del_archivo = filedialog.askopenfilename(
        title="Cargar archivo de semillas",
        filetypes=[("Archivo de semillas", "*.csv *.txt")],
    )
    if not ruta_del_archivo:
        return
    limites_de_uniforme, errores_de_uniforme = leer_opciones_de_transformacion()
    if errores_de_uniforme:
        messagebox.showerror("Datos inválidos", "\n".join(errores_de_uniforme))
        return
    filas_validas, errores = inicializacion.leer_archivo_de_semillas(ruta_del_archivo)
    secuencias_cargadas = [agregar_secuencia(fila, limites_de_uniforme, componentes["incluir_normal"].get()) for fila in filas_validas]
    if secuencias_cargadas:
        actualizar_lista_de_secuencias(len(secuencias_generadas) - 1)
    lineas = [f"Secuencias generadas desde el archivo: {len(secuencias_cargadas)}"]
    lineas.extend(f"- {secuencia['etiqueta']}" for secuencia in secuencias_cargadas)
    if errores:
        lineas.append("")
        lineas.append("Filas con errores:")
        lineas.extend(errores)
    messagebox.showinfo("Cargar archivo de semillas", "\n".join(lineas))


def exportar_secuencia_elegida():
    indice_elegido = obtener_indice_elegido()
    if indice_elegido is None:
        messagebox.showinfo("Exportar CSV", "Elija una secuencia de la lista.")
        return
    ruta_del_archivo = filedialog.asksaveasfilename(
        title="Exportar secuencia",
        defaultextension=".csv",
        filetypes=[("Archivo CSV", "*.csv")],
    )
    if ruta_del_archivo:
        reportes.exportar_secuencia_a_csv(secuencias_generadas[indice_elegido], ruta_del_archivo)
        messagebox.showinfo("Exportar CSV", f"Secuencia exportada en:\n{ruta_del_archivo}")


def quitar_secuencia_elegida():
    indice_elegido = obtener_indice_elegido()
    if indice_elegido is not None:
        del secuencias_generadas[indice_elegido]
        actualizar_lista_de_secuencias()


def mostrar_figura_en_ventana(figura, titulo):
    ventana_del_grafico = tk.Toplevel(componentes["ventana"])
    ventana_del_grafico.title(titulo)
    lienzo = FigureCanvasTkAgg(figura, master=ventana_del_grafico)
    NavigationToolbar2Tk(lienzo, ventana_del_grafico)
    lienzo.get_tk_widget().pack(fill="both", expand=True)
    lienzo.draw()


def mostrar_histograma_elegido():
    indice_elegido = obtener_indice_elegido()
    if indice_elegido is None:
        messagebox.showinfo("Histograma", "Elija una secuencia de la lista.")
        return
    secuencia = secuencias_generadas[indice_elegido]
    mostrar_figura_en_ventana(reportes.crear_histograma_de_secuencia(secuencia), f"Histograma: {secuencia['etiqueta']}")


def ejecutar_y_graficar_pruebas():
    resultados_por_prueba = ejecutar_pruebas_elegidas()
    if resultados_por_prueba:
        for nombre_de_la_prueba, resultados in resultados_por_prueba.items():
            mostrar_figura_en_ventana(GRAFICOS_DE_PRUEBAS[nombre_de_la_prueba](resultados), f"Prueba {nombre_de_la_prueba}")


def leer_cantidad_de_intervalos():
    try:
        cantidad_de_intervalos = int(componentes["cantidad_de_intervalos"].get())
    except ValueError:
        return None
    return cantidad_de_intervalos if cantidad_de_intervalos >= 2 else None


def ejecutar_pruebas_elegidas():
    pruebas_elegidas = [nombre for nombre, elegida in componentes["pruebas_elegidas"].items() if elegida.get()]
    secuencias_con_numeros = [secuencia for secuencia in secuencias_generadas if len(secuencia["numeros_r"]) >= 2]
    if not pruebas_elegidas or not secuencias_con_numeros:
        messagebox.showinfo("Ejecutar pruebas", "Genere al menos una secuencia de dos o más números y marque al menos una prueba.")
        return None
    cantidad_de_intervalos = leer_cantidad_de_intervalos()
    if cantidad_de_intervalos is None:
        messagebox.showerror("Datos inválidos", "El número de intervalos k debe ser un entero mayor o igual a 2.")
        return None
    resumen = componentes["resumen"]
    resumen.delete(*resumen.get_children())
    resultados_por_prueba = {}
    for nombre_de_la_prueba in pruebas_elegidas:
        resultados_por_prueba[nombre_de_la_prueba] = []
        for secuencia in secuencias_con_numeros:
            resultado = PRUEBAS_DISPONIBLES[nombre_de_la_prueba](secuencia["numeros_r"], cantidad_de_intervalos)
            resultado["etiqueta"] = secuencia["etiqueta"]
            resultados_por_prueba[nombre_de_la_prueba].append(resultado)
            resumen.insert("", "end", values=(
                resultado["etiqueta"],
                resultado["prueba"],
                f"{resultado['estadistico']:.5f}",
                reportes.describir_criterio(resultado),
                "Pasa" if resultado["pasa"] else "No pasa",
                " ".join(resultado["avisos"]),
            ))
    return resultados_por_prueba


def crear_marco_de_generacion(ventana):
    marco = ttk.LabelFrame(ventana, text="Generación", padding=8)
    ttk.Label(marco, text="Método").grid(row=0, column=0, sticky="w")
    componentes["metodo"] = ttk.Combobox(marco, values=list(NOMBRES_DE_METODOS), state="readonly", width=28)
    componentes["metodo"].set("Congruencial lineal")
    componentes["metodo"].grid(row=0, column=1, columnspan=3, sticky="w", pady=2)
    componentes["metodo"].bind("<<ComboboxSelected>>", actualizar_campos_habilitados)
    componentes["campos"] = {}
    for columna, (nombre_del_campo, texto, valor_inicial) in enumerate(CAMPOS_DE_GENERACION):
        ttk.Label(marco, text=texto).grid(row=1, column=2 * columna, sticky="e", padx=(8, 2))
        campo = ttk.Entry(marco, width=12)
        campo.insert(0, valor_inicial)
        campo.grid(row=1, column=2 * columna + 1, sticky="w", pady=2)
        componentes["campos"][nombre_del_campo] = campo
    componentes["incluir_uniforme"] = tk.BooleanVar(value=False)
    ttk.Checkbutton(marco, text="Uniforme U(a, b)", variable=componentes["incluir_uniforme"]).grid(row=2, column=0, columnspan=2, sticky="w")
    ttk.Label(marco, text="Límite inferior").grid(row=2, column=2, sticky="e", padx=(8, 2))
    componentes["limite_inferior"] = ttk.Entry(marco, width=12)
    componentes["limite_inferior"].insert(0, "2")
    componentes["limite_inferior"].grid(row=2, column=3, sticky="w")
    ttk.Label(marco, text="Límite superior").grid(row=2, column=4, sticky="e", padx=(8, 2))
    componentes["limite_superior"] = ttk.Entry(marco, width=12)
    componentes["limite_superior"].insert(0, "5")
    componentes["limite_superior"].grid(row=2, column=5, sticky="w")
    componentes["incluir_normal"] = tk.BooleanVar(value=False)
    ttk.Checkbutton(marco, text="Normal estándar N(0, 1)", variable=componentes["incluir_normal"]).grid(row=2, column=6, columnspan=3, sticky="w", padx=(8, 0))
    componentes["marco_de_botones_de_generacion"] = ttk.Frame(marco)
    componentes["marco_de_botones_de_generacion"].grid(row=3, column=0, columnspan=12, sticky="w", pady=(6, 0))
    ttk.Button(componentes["marco_de_botones_de_generacion"], text="Generar", command=generar_desde_campos).pack(side="left")
    ttk.Button(componentes["marco_de_botones_de_generacion"], text="Cargar archivo de semillas", command=cargar_archivo_de_semillas).pack(side="left", padx=4)
    return marco


def crear_marco_de_secuencias(ventana):
    marco = ttk.LabelFrame(ventana, text="Secuencias generadas", padding=8)
    lista = ttk.Treeview(marco, columns=("secuencia", "numeros", "avisos"), show="headings", selectmode="browse", height=8)
    for columna, texto, ancho in (("secuencia", "Secuencia", 260), ("numeros", "Números", 80), ("avisos", "Avisos", 60)):
        lista.heading(columna, text=texto)
        lista.column(columna, width=ancho)
    lista.bind("<<TreeviewSelect>>", mostrar_secuencia_elegida)
    lista.pack(fill="both", expand=True)
    componentes["lista_de_secuencias"] = lista
    componentes["marco_de_botones_de_secuencias"] = ttk.Frame(marco)
    componentes["marco_de_botones_de_secuencias"].pack(fill="x", pady=(6, 0))
    ttk.Button(componentes["marco_de_botones_de_secuencias"], text="Histograma", command=mostrar_histograma_elegido).pack(side="left")
    ttk.Button(componentes["marco_de_botones_de_secuencias"], text="Exportar CSV", command=exportar_secuencia_elegida).pack(side="left", padx=4)
    ttk.Button(componentes["marco_de_botones_de_secuencias"], text="Quitar", command=quitar_secuencia_elegida).pack(side="left")
    componentes["detalle"] = tk.StringVar()
    ttk.Label(marco, textvariable=componentes["detalle"], wraplength=420, justify="left").pack(fill="x", pady=(6, 0))
    return marco


def crear_marco_de_tabla(ventana):
    marco = ttk.LabelFrame(ventana, text="Tabla de la secuencia elegida", padding=8)
    tabla = ttk.Treeview(marco, show="headings")
    barra_de_desplazamiento = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=barra_de_desplazamiento.set)
    tabla.pack(side="left", fill="both", expand=True)
    barra_de_desplazamiento.pack(side="right", fill="y")
    componentes["tabla"] = tabla
    return marco


def crear_marco_de_pruebas(ventana):
    marco = ttk.LabelFrame(ventana, text="Pruebas de validación (α = 0.05)", padding=8)
    opciones = ttk.Frame(marco)
    opciones.pack(fill="x")
    componentes["pruebas_elegidas"] = {}
    for nombre_de_la_prueba in PRUEBAS_DISPONIBLES:
        componentes["pruebas_elegidas"][nombre_de_la_prueba] = tk.BooleanVar(value=True)
        ttk.Checkbutton(opciones, text=nombre_de_la_prueba, variable=componentes["pruebas_elegidas"][nombre_de_la_prueba]).pack(side="left", padx=(0, 8))
    ttk.Label(opciones, text="Intervalos k").pack(side="left", padx=(16, 2))
    componentes["cantidad_de_intervalos"] = ttk.Entry(opciones, width=8)
    componentes["cantidad_de_intervalos"].pack(side="left")
    ttk.Label(opciones, text="(por defecto √n de la secuencia más corta)").pack(side="left", padx=(4, 16))
    componentes["boton_de_pruebas"] = ttk.Button(opciones, text="Ejecutar pruebas", command=ejecutar_y_graficar_pruebas)
    componentes["boton_de_pruebas"].pack(side="left")
    columnas = (
        ("secuencia", "Secuencia", 240),
        ("prueba", "Prueba", 100),
        ("estadistico", "Estadístico", 110),
        ("criterio", "Valor crítico o intervalo", 170),
        ("resultado", "Resultado", 80),
        ("avisos", "Avisos", 380),
    )
    resumen = ttk.Treeview(marco, columns=[columna for columna, _, _ in columnas], show="headings", height=6)
    for columna, texto, ancho in columnas:
        resumen.heading(columna, text=texto)
        resumen.column(columna, width=ancho)
    resumen.pack(fill="both", expand=True, pady=(6, 0))
    componentes["resumen"] = resumen
    return marco


def crear_ventana_principal():
    ventana = tk.Tk()
    ventana.title("Generadores y validadores de números pseudoaleatorios")
    ventana.geometry("1150x900")
    componentes["ventana"] = ventana
    crear_marco_de_generacion(ventana).grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
    crear_marco_de_secuencias(ventana).grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
    crear_marco_de_tabla(ventana).grid(row=1, column=1, sticky="nsew", padx=8, pady=4)
    crear_marco_de_pruebas(ventana).grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=4)
    ventana.columnconfigure(0, weight=1)
    ventana.columnconfigure(1, weight=1)
    ventana.rowconfigure(1, weight=1)
    actualizar_campos_habilitados()
    return ventana


def iniciar_programa():
    crear_ventana_principal().mainloop()


if __name__ == "__main__":
    iniciar_programa()
