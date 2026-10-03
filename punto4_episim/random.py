from typing import Iterator
from .models import UniformSource
from punto3_generadores_pseudoaleatorios.generadores import generar_congruencial_lineal


class PseudorandomGenerator:
    """Adaptador del generador congruencial lineal del Punto 3."""

    def __init__(
        self,
        seed: int,
        a: int = 1664525,
        c: int = 1013904223,
        m: int = 2**32,
        batch_size: int = 256,
    ) -> None:
        self.state = seed % m
        self.a, self.c, self.m = a, c, m
        self._batch_size = batch_size
        self._buffer: Iterator[tuple[int, float]] = iter(())

    def _refill(self) -> None:
        sequence = generar_congruencial_lineal(
            self.state, self.a, self.c, self.m, self._batch_size
        )
        self._buffer = zip(sequence["valores_x"], sequence["numeros_r"])

    def next(self) -> float:
        """Devuelve el siguiente U ~ U[0,1)"""
        try:
            self.state, number = next(self._buffer)
        except StopIteration:
            self._refill()
            self.state, number = next(self._buffer)
        return number


def uniform(gen: UniformSource, low: float, high: float) -> float:
    """Transformación lineal de U[0,1) al intervalo indicado."""
    return low + (high - low) * gen.next()


def sample_duration(gen: UniformSource, low: float, high: float) -> int:
    """Muestra una duración y la redondea al entero más cercano."""
    return int(uniform(gen, low, high) + 0.5)
