import csv

from .models import Config, RANDOM_PARAMETERS, ReplicaParams, UniformSource
from .random import uniform


def read_config(path: str) -> Config:
    config: Config = {}

    with open(path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            config[row["parametro"].strip()] = (
                float(row["min"]),
                float(row["max"]),
            )

    required = (*RANDOM_PARAMETERS, "poblacion", "infectados_iniciales",
                "dias", "contactos_maximos_k", "umbral_control",
                "seleccion_solo_susceptibles", "periodo_incubacion",
                "periodo_infeccioso")

    missing = [name for name in required if name not in config]
    if missing:
        raise ValueError(f"Faltan parámetros en {path}: {', '.join(missing)}")

    return config


def sample_params(config: Config, gen: UniformSource) -> ReplicaParams:
    """Sortea los parámetros aleatorios y construye una réplica."""
    drawn = {
        name: uniform(gen, *config[name])
        for name in RANDOM_PARAMETERS
    }

    return ReplicaParams(
        **drawn,
        poblacion=int(config["poblacion"][0]),
        infectados_iniciales=int(config["infectados_iniciales"][0]),
        dias=int(config["dias"][0]),
        contactos_maximos_k=int(config["contactos_maximos_k"][0]),
        umbral_control=int(config["umbral_control"][0]),
        seleccion_solo_susceptibles=int(
            config["seleccion_solo_susceptibles"][0]
        ) == 1,
        incubacion_min=config["periodo_incubacion"][0],
        incubacion_max=config["periodo_incubacion"][1],
        infeccioso_min=config["periodo_infeccioso"][0],
        infeccioso_max=config["periodo_infeccioso"][1],
    )
