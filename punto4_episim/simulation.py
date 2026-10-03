from collections import defaultdict

from .models import DailyRecord, ReplicaParams, State, UniformSource
from .random import sample_duration
from .structures import IndexedPool, build_contact_cdf, sample_contact_count


class EpidemicSimulation:

    def __init__(self, params: ReplicaParams, gen: UniformSource) -> None:
        self.params = params
        self.gen = gen
        n = params.poblacion

        self.vaccinated: list[bool] = self._draw_vaccinated()
        index_cases = self._draw_index_cases()

        self.state: list[State] = [State.S] * n
        for person in index_cases:
            self.state[person] = State.I

        self.susceptible = IndexedPool(
            i for i in range(n) if self.state[i] is State.S
        )
        self.infectious = IndexedPool(index_cases)

        self.to_infectious: defaultdict[int, list[int]] = defaultdict(list)
        self.to_removed: defaultdict[int, list[int]] = defaultdict(list)
        self.will_die: dict[int, bool] = {}

        self.exposed = 0
        self.removed = 0
        self.deaths = 0

        self.contact_cdf = build_contact_cdf(
            params.beta, params.contactos_maximos_k
        )
        self.p_unvaccinated = params.probabilidad_transmision
        self.p_vaccinated = (
            params.probabilidad_transmision
            * (1.0 - params.efectividad_vacuna)
        )

        for person in index_cases:
            self._schedule_index_case(person)

    def _draw_vaccinated(self) -> list[bool]:
        n = self.params.poblacion
        count = int(round(self.params.tasa_vacunacion * n))
        ids = list(range(n))
        vaccinated = [False] * n

        for i in range(count):
            j = i + int(self.gen.next() * (n - i))
            ids[i], ids[j] = ids[j], ids[i]
            vaccinated[ids[i]] = True

        return vaccinated

    def _draw_index_cases(self) -> list[int]:
        n = self.params.poblacion
        cases: set[int] = set()

        while len(cases) < self.params.infectados_iniciales:
            cases.add(int(self.gen.next() * n))

        return sorted(cases)

    def _schedule_index_case(self, person: int) -> None:
        p = self.params
        recovery_day = sample_duration(
            self.gen, p.infeccioso_min, p.infeccioso_max
        )
        self.will_die[person] = self.gen.next() < p.letalidad
        self.to_removed[recovery_day].append(person)

    def _apply_scheduled_transitions(self, day: int) -> None:
        for person in self.to_removed.pop(day, ()):
            self.infectious.remove(person)
            self.state[person] = State.R
            self.removed += 1

            if self.will_die[person]:
                self.deaths += 1

        for person in self.to_infectious.pop(day, ()):
            self.state[person] = State.I
            self.infectious.add(person)
            self.exposed -= 1

    def _pick_target(self) -> int | None:
        if self.params.seleccion_solo_susceptibles:
            if not self.susceptible:
                return None
            return self.susceptible.pick(self.gen.next())

        person = int(self.gen.next() * self.params.poblacion)
        return person if self.state[person] is State.S else None

    def _transmits(self, target: int) -> bool:
        p_effective = (
            self.p_vaccinated
            if self.vaccinated[target]
            else self.p_unvaccinated
        )
        return self.gen.next() < p_effective

    def _expose(self, person: int, day: int) -> None:
        p = self.params

        self.susceptible.remove(person)
        self.state[person] = State.E
        self.exposed += 1

        incubation = sample_duration(
            self.gen, p.incubacion_min, p.incubacion_max
        )
        infectious_period = sample_duration(
            self.gen, p.infeccioso_min, p.infeccioso_max
        )
        self.will_die[person] = self.gen.next() < p.letalidad

        becomes_infectious = day + incubation
        becomes_removed = becomes_infectious + infectious_period

        if becomes_infectious <= p.dias:
            self.to_infectious[becomes_infectious].append(person)

        if becomes_removed <= p.dias:
            self.to_removed[becomes_removed].append(person)

    def _simulate_contacts(self, day: int) -> None:
        for _infected in self.infectious:
            for _ in range(
                sample_contact_count(self.gen, self.contact_cdf)
            ):
                target = self._pick_target()

                if target is not None and self._transmits(target):
                    self._expose(target, day)

    def _snapshot(self, day: int) -> DailyRecord:
        record = DailyRecord(
            day,
            len(self.susceptible),
            self.exposed,
            len(self.infectious),
            self.removed,
            self.deaths,
        )

        if record.S + record.E + record.I + record.R != self.params.poblacion:
            raise RuntimeError(
                f"Conservación violada en el día {day}: {record}"
            )

        return record

    def run(self) -> list[DailyRecord]:
        horizon = self.params.dias
        records = [self._snapshot(0)]

        for day in range(1, horizon + 1):
            self._apply_scheduled_transitions(day)
            self._simulate_contacts(day)

            record = self._snapshot(day)
            records.append(record)

            if record.E == 0 and record.I == 0:
                records.extend(
                    record._replace(day=d)
                    for d in range(day + 1, horizon + 1)
                )
                break

        return records


def simulate_epidemic(
    params: ReplicaParams,
    gen: UniformSource,
) -> list[DailyRecord]:
    return EpidemicSimulation(params, gen).run()
