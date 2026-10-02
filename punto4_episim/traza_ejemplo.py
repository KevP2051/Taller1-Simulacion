# =====================================================================
# traza_ejemplo.py - Ejemplo trabajado de UN dia de simulacion
# Muestra, numero por numero, como se generan y usan los U(0,1) del
# generador propio en cada paso del contagio (evidencia para la rubrica:
# "demostracion clara de como se generan y utilizan numeros
# pseudoaleatorios en cada paso del proceso de contagio").
# Usa las MISMAS funciones del motor; solo agrega impresion.
# Uso: python traza_ejemplo.py [semilla]
# =====================================================================
import sys
from motor_episim import (PseudorandomGenerator, build_contact_cdf,
                          sample_contact_count, select_susceptible,
                          evaluate_transmission, sample_duration, uniform)

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 555555555


class TracedGenerator(PseudorandomGenerator):
    """Igual al generador del motor, pero recuerda el ultimo U entregado."""
    ultimo = None

    def next(self):
        self.ultimo = super().next()
        return self.ultimo


gen = TracedGenerator(seed)
print(f"Seed X0 = {seed}  |  X(n+1) = (1664525*X(n) + 1013904223) mod 2^32,  U = X/2^32\n")

print("== Replica parameters (transformation X = a + (b-a)*U) ==")
beta = uniform(gen, 0.3, 0.5);   print(f"U={gen.ultimo:.6f} -> beta  = 0.3 + 0.2*U   = {beta:.4f}")
p = uniform(gen, 0.4, 0.6);      print(f"U={gen.ultimo:.6f} -> p     = 0.4 + 0.2*U   = {p:.4f}")
efect = uniform(gen, 0.80, 0.95); print(f"U={gen.ultimo:.6f} -> efect = 0.80 + 0.15*U = {efect:.4f}")

k = 4
tabla = build_contact_cdf(beta, k)
print(f"\n== Contact probability table (k={k}, Binomial({k}, beta/k={beta / k:.4f})) ==")
print("Equivalent to the class Excel 'r range -> event' table")
previous_limit = 0.0
for contact_count, limit in enumerate(tabla):
    print(f"  {previous_limit:.5f} <= r < {limit:.5f}  ->  {contact_count} contact(s)")
    previous_limit = limit

print("\n== Day 1 with 10 index cases; 20 fictional susceptibles (ids 100..119); even ids vaccinated ==")
susceptible_list = list(range(100, 120))
is_vaccinated = lambda i: i % 2 == 0
incubation_period = None
for infected_number in range(1, 11):
    contact_count = sample_contact_count(gen, tabla)
    print(f"\nInfected {infected_number}: contact_random = {gen.ultimo:.6f} -> {contact_count} contact(s)")
    if contact_count == 0:
        continue
    for contact_index in range(contact_count):
        target = select_susceptible(gen, susceptible_list)
        print(f"   Contact {contact_index + 1}: selection_random = {gen.ultimo:.6f} -> floor(r*{len(susceptible_list)}) = "
              f"{int(gen.ultimo * len(susceptible_list))} -> individual {target} "
              f"({'vaccinated' if is_vaccinated(target) else 'unvaccinated'})")
        vaccination_factor = (1 - efect) if is_vaccinated(target) else 1.0
        infection = evaluate_transmission(gen, p, is_vaccinated(target), efect)
        print(f"      transmission_random = {gen.ultimo:.6f}  vs  effective_p = {p:.4f} x {vaccination_factor:.4f} = {p * vaccination_factor:.4f}"
              f"  ->  {'INFECTION (S -> E)' if infection else 'no infection'}")
        if infection:
            incubation = sample_duration(gen, 2, 5); incubation_random = gen.ultimo
            infectious = sample_duration(gen, 7, 14); infectious_random = gen.ultimo
            print(f"      incubation: U={incubation_random:.6f} -> {incubation} days | infectious: U={infectious_random:.6f} -> {infectious} days")
