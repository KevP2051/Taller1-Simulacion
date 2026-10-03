import math
from bisect import bisect_right
from typing import Iterable, Iterator

from .models import UniformSource


class IndexedPool:
    """Conjunto que permite agregar, quitar y elegir por posición en O(1)."""

    __slots__ = ("_items", "_position")

    def __init__(self, items: Iterable[int] = ()) -> None:
        self._items: list[int] = list(items)
        self._position: dict[int, int] = {
            item: i for i, item in enumerate(self._items)
        }

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[int]:
        return iter(self._items)

    def __contains__(self, item: int) -> bool:
        return item in self._position

    def add(self, item: int) -> None:
        self._position[item] = len(self._items)
        self._items.append(item)

    def remove(self, item: int) -> None:
        index = self._position.pop(item)
        last = self._items.pop()

        if last != item:
            self._items[index] = last
            self._position[last] = index

    def pick(self, u: float) -> int:
        return self._items[int(u * len(self._items))]


def build_contact_cdf(beta: float, k: int) -> list[float]:
    """Construye la CDF de Binomial(k, beta/k)."""
    q = beta / k
    cdf: list[float] = []
    cumulative = 0.0

    for contacts in range(k + 1):
        cumulative += (
            math.comb(k, contacts)
            * q**contacts
            * (1 - q) ** (k - contacts)
        )
        cdf.append(cumulative)

    cdf[-1] = 1.0
    return cdf


def sample_contact_count(gen: UniformSource, cdf: list[float]) -> int:
    """Transformada inversa mediante búsqueda binaria."""
    return bisect_right(cdf, gen.next())
