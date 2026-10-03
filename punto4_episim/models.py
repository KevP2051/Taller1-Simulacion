from dataclasses import dataclass
from enum import IntEnum
from typing import Protocol, NamedTuple

RANDOM_PARAMETERS: tuple[str, ...] = (
    "beta",
    "probabilidad_transmision",
    "tasa_vacunacion",
    "efectividad_vacuna",
    "letalidad",
)

FIXED_PARAMETERS: tuple[str, ...] = (
    "poblacion",
    "infectados_iniciales",
    "dias",
    "contactos_maximos_k",
    "umbral_control",
    "seleccion_solo_susceptibles",
    "periodo_incubacion",
    "periodo_infeccioso",
)

Config = dict[str, tuple[float, float]]

class State(IntEnum):
    """Compartimentos del modelo SEIR."""
    S = 0
    E = 1
    I = 2
    R = 3


class UniformSource(Protocol):
    """Contrato mínimo para una fuente de números U[0,1)."""
    state: int
    def next(self) -> float:
        """Devuelve el siguiente U ~ U[0, 1)."""


class DailyRecord(NamedTuple):
    """Estado del sistema al cierre de un día."""
    day: int
    S: int
    E: int
    I: int
    R: int
    F: int


@dataclass(frozen=True)
class ReplicaParams:
    """Parámetros de una réplica."""
    beta: float
    probabilidad_transmision: float
    tasa_vacunacion: float
    efectividad_vacuna: float
    letalidad: float
    poblacion: int
    infectados_iniciales: int
    dias: int
    contactos_maximos_k: int
    umbral_control: int
    seleccion_solo_susceptibles: bool
    incubacion_min: float
    incubacion_max: float
    infeccioso_min: float
    infeccioso_max: float
