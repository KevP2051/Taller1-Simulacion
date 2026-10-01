"""
Flujo continuo de números pseudoaleatorios para EpiSim (Punto 4).

Este módulo NO implementa un generador nuevo: es un envoltorio con estado
sobre el generador congruencial lineal (mixto) del Punto 3
(punto3_generadores_pseudoaleatorios.generadores.generar_congruencial_lineal).

Funcionamiento:
    - Se piden números al Punto 3 por bloques (por defecto, 100.000).
    - Cuando un bloque se agota, se pide el siguiente usando como semilla el
      último X del bloque anterior. Como X(n+1) depende solo de X(n), la
      secuencia es exactamente la misma que se obtendría con una sola llamada
      gigante, pero sin guardar millones de números en memoria.
    - Todas las réplicas consumen el mismo flujo, una a continuación de otra,
      de modo que los tramos usados no se solapan mientras el total consumido
      sea menor que el período (m = 2^32 con parámetros que cumplen Hull-Dobell).

Reproducibilidad:
    estado() devuelve el último X consumido. Un FlujoAleatorio creado con
    semilla = estado() produce exactamente los mismos números que el flujo
    original habría producido a partir de ese punto. Ese valor se guarda como
    "semilla" de cada réplica.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from punto3_generadores_pseudoaleatorios import generadores

# Parámetros del generador congruencial mixto (cumplen el teorema de Hull-Dobell)
MULTIPLICADOR_A = 1664525
INCREMENTO_C = 1013904223
MODULO_M = 2 ** 32
TAMANO_BLOQUE = 100_000


class FlujoAleatorio:
    """Entrega números R en [0, 1] uno a uno, a partir del generador del Punto 3."""

    def __init__(self, semilla, multiplicador_a=MULTIPLICADOR_A, incremento_c=INCREMENTO_C,
                 modulo_m=MODULO_M, tamano_bloque=TAMANO_BLOQUE):
        if not 0 <= semilla < modulo_m:
            raise ValueError(f"La semilla debe estar entre 0 y {modulo_m - 1}.")
        verificacion = generadores.verificar_hull_dobell(multiplicador_a, incremento_c, modulo_m)
        if not verificacion["cumple"]:
            raise ValueError("Los parámetros no cumplen Hull-Dobell: el período máximo no está garantizado.")
        self.multiplicador_a = multiplicador_a
        self.incremento_c = incremento_c
        self.modulo_m = modulo_m
        self.tamano_bloque = tamano_bloque
        self.semilla_inicial = semilla
        self._ultimo_x = semilla          # último X consumido (estado del generador)
        self._bloque_x = []               # valores X del bloque actual
        self._bloque_r = []               # números R del bloque actual
        self._posicion = 0                # siguiente posición a consumir en el bloque
        self.numeros_consumidos = 0
        self._cache_binomial = {}

    # ------------------------------------------------------------------
    # Núcleo: pedir bloques al Punto 3 y entregar números uno a uno
    # ------------------------------------------------------------------
    def _pedir_bloque(self):
        """Pide un bloque nuevo al Punto 3, continuando desde el último X consumido."""
        secuencia = generadores.generar_congruencial_lineal(
            self._ultimo_x, self.multiplicador_a, self.incremento_c, self.modulo_m, self.tamano_bloque
        )
        self._bloque_x = secuencia["valores_x"]
        self._bloque_r = secuencia["numeros_r"]
        self._posicion = 0

    def siguiente(self):
        """Devuelve el siguiente número R ~ U(0, 1) del flujo (5 decimales, como en el Punto 3)."""
        if self._posicion >= len(self._bloque_r):
            self._pedir_bloque()
        numero_r = self._bloque_r[self._posicion]
        self._ultimo_x = self._bloque_x[self._posicion]
        self._posicion += 1
        self.numeros_consumidos += 1
        return numero_r

    def estado(self):
        """Último X consumido: sirve como semilla para reproducir el flujo desde este punto."""
        return self._ultimo_x

    def fraccion_del_periodo_usada(self):
        """Proporción del período (m) que se ha consumido; debe mantenerse muy por debajo de 1."""
        return self.numeros_consumidos / self.modulo_m

    def muestra(self, cantidad):
        """Consume y devuelve una lista de 'cantidad' números R (útil para las pruebas del Punto 3)."""
        return [self.siguiente() for _ in range(cantidad)]

    # ------------------------------------------------------------------
    # Transformaciones usadas por EpiSim (cada una consume números del flujo)
    # ------------------------------------------------------------------
    def uniforme(self, limite_inferior, limite_superior):
        """X ~ U(a, b) por transformación inversa: X = a + (b - a)·R (función del Punto 3)."""
        return generadores.transformar_a_uniforme([self.siguiente()], limite_inferior, limite_superior)[0]

    def entero_en(self, cantidad):
        """Índice entero uniforme en {0, ..., cantidad - 1}: piso(R·cantidad).

        Protección: con m par, el Punto 3 normaliza entre m - 1, así que R puede
        valer 1.0 exacto; en ese caso piso(1.0·cantidad) se saldría del rango.
        """
        if cantidad <= 0:
            raise ValueError("La cantidad debe ser mayor que 0.")
        return min(int(self.siguiente() * cantidad), cantidad - 1)

    def entero_entre(self, minimo, maximo):
        """Entero uniforme discreto en {minimo, ..., maximo} (Unidad IV, 4.3.6).

        A diferencia de redondear U(minimo, maximo), aquí todos los valores
        son equiprobables (el redondeo da la mitad de probabilidad a los extremos).
        """
        return minimo + self.entero_en(maximo - minimo + 1)

    def bernoulli(self, probabilidad):
        """True con probabilidad 'probabilidad': se compara R < probabilidad."""
        return self.siguiente() < probabilidad

    def _acumuladas_binomial(self, ensayos, probabilidad):
        """Probabilidades acumuladas F(0), ..., F(n) de una Binomial(n, p), guardadas en caché."""
        clave = (ensayos, probabilidad)
        if clave not in self._cache_binomial:
            acumulada = 0.0
            acumuladas = []
            for exitos in range(ensayos + 1):
                acumulada += math.comb(ensayos, exitos) * probabilidad ** exitos * (1 - probabilidad) ** (ensayos - exitos)
                acumuladas.append(acumulada)
            self._cache_binomial[clave] = acumuladas
        return self._cache_binomial[clave]

    def binomial(self, ensayos, probabilidad):
        """X ~ Binomial(n, p) por transformada inversa con UN solo número R:
        devuelve el menor x tal que R < F(x). Si R = 1.0 exacto, devuelve n.
        """
        numero_r = self.siguiente()
        for exitos, acumulada in enumerate(self._acumuladas_binomial(ensayos, probabilidad)):
            if numero_r < acumulada:
                return exitos
        return ensayos


# ----------------------------------------------------------------------
# Autoprueba: python punto4_episim/flujo_aleatorio.py
# ----------------------------------------------------------------------
def autoprueba(semilla=12345):
    from punto3_generadores_pseudoaleatorios import pruebas

    print("1) Continuidad entre bloques")
    total = 250_000
    flujo = FlujoAleatorio(semilla)
    por_flujo = flujo.muestra(total)
    de_una_vez = generadores.generar_congruencial_lineal(semilla, MULTIPLICADOR_A, INCREMENTO_C, MODULO_M, total)["numeros_r"]
    print("   Idénticos a una sola llamada al Punto 3:", por_flujo == de_una_vez)
    print("   Números consumidos:", flujo.numeros_consumidos, "| fracción del período:", f"{flujo.fraccion_del_periodo_usada():.2e}")

    print("2) Reproducibilidad con estado()")
    flujo = FlujoAleatorio(semilla)
    flujo.muestra(123_456)
    estado = flujo.estado()
    continuacion = flujo.muestra(1000)
    print("   Mismos números desde el estado guardado:", FlujoAleatorio(estado).muestra(1000) == continuacion)

    print("3) Transformaciones (promedios sobre 100.000 sorteos)")
    flujo = FlujoAleatorio(semilla)
    n = 100_000
    beta = 0.3
    contactos = [flujo.binomial(4, beta / 4) for _ in range(n)]
    print(f"   Binomial(4, {beta}/4): media = {sum(contactos) / n:.4f} (esperada {beta}), máximo = {max(contactos)}")
    indices = [flujo.entero_en(10_000) for _ in range(n)]
    print(f"   entero_en(10000): mínimo = {min(indices)}, máximo = {max(indices)} (debe ser <= 9999)")
    dias = [flujo.entero_entre(2, 5) for _ in range(n)]
    print("   entero_entre(2, 5): frecuencias =", {d: round(dias.count(d) / n, 3) for d in range(2, 6)})
    exitos = sum(flujo.bernoulli(0.5 * (1 - 0.875)) for _ in range(n))
    print(f"   bernoulli(0.0625): proporción = {exitos / n:.4f}")
    valores = [flujo.uniforme(0.1, 0.5) for _ in range(10_000)]
    print(f"   uniforme(0.1, 0.5): mínimo = {min(valores)}, máximo = {max(valores)}, media = {sum(valores) / len(valores):.4f}")

    print("4) Las 6 pruebas del Punto 3 sobre 100.000 números del flujo")
    numeros_r = FlujoAleatorio(semilla).muestra(100_000)
    intervalos = pruebas.cantidad_de_intervalos_por_defecto(len(numeros_r))
    resultados = [
        pruebas.prueba_de_medias(numeros_r),
        pruebas.prueba_de_varianza(numeros_r),
        pruebas.prueba_chi_cuadrado(numeros_r, intervalos),
        pruebas.prueba_kolmogorov_smirnov(numeros_r, intervalos),
        pruebas.prueba_de_poker(numeros_r),
        pruebas.prueba_de_rachas(numeros_r),
    ]
    for resultado in resultados:
        print(f"   {resultado['prueba']:<20} {'PASA' if resultado['pasa'] else 'NO PASA'}")


if __name__ == "__main__":
    autoprueba()