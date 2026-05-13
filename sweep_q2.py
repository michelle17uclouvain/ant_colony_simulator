"""
Q2 — Taux d'évaporation des phéromones
Lance RUNS runs pour chaque taux (0.500 à 0.999, 20 points)
sur 05_square_four_food_spots avec 70 fourmis.
Objectif : env.is_complete() — 75% retirée ET 50% rapportée à la colonie.
"""

import time
import statistics
import numpy as np
import matplotlib.pyplot as plt

from utils import create_environment, add_ants

ENV_FILE   = "envs/05_square_four_food_spots.txt"
NB_ANTS    = 70
RUNS       = 10
EVAP_RATES = list(np.linspace(0.500, 0.999, 20))


def run_once(evap_rate: float):
    env = create_environment(ENV_FILE, 0, 0, verbose=False)
    env.home_pheromones.evaporation_rate = evap_rate
    env.food_pheromones.evaporation_rate = evap_rate
    add_ants(env, "smart", None, NB_ANTS, verbose=False)

    start      = time.time()
    step       = 0
    max_steps  = env.max_steps or 10_000
    time_limit = env.time_limit or 300

    while step < max_steps and (time.time() - start) < time_limit:
        env.update()
        step += 1
        if env.is_complete():
            return step, time.time() - start

    return None, None


def sweep():
    results = []

    for rate in EVAP_RATES:
        print(f"  evap={rate:.3f} ...", end=" ", flush=True)
        steps_list = []

        for _ in range(RUNS):
            s, _ = run_once(rate)
            if s is not None:
                steps_list.append(s)

        m  = statistics.mean(steps_list)  if steps_list else float("nan")
        sd = statistics.stdev(steps_list) if len(steps_list) > 1 else 0
        results.append((m, sd))
        print(f"steps={m:.0f} ± {sd:.0f}  ({len(steps_list)}/{RUNS} réussis)")

    return results


def plot(evap_rates, results):
    means = [r[0] for r in results]
    stds  = [r[1] for r in results]

    plt.figure(figsize=(10, 5))
    plt.errorbar(evap_rates, means, yerr=stds, fmt="o-", capsize=4, color="mediumseagreen")
    plt.xlabel("Taux d'évaporation")
    plt.ylabel("Steps moyens")
    plt.title("Steps pour atteindre l'objectif (75% collectée, 33% rapportée à la colonie)\nen fonction du taux d'évaporation (moyenne ± écart-type)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("figures/q2_evaporation.pdf", bbox_inches="tight")
    plt.savefig("figures/q2_evaporation.png", bbox_inches="tight", dpi=150)
    print("Sauvegardé dans figures/q2_evaporation.pdf/.png")
    plt.show()


if __name__ == "__main__":
    import os
    os.makedirs("figures", exist_ok=True)
    print(f"Q2 — Sweep évaporation ({len(EVAP_RATES)} valeurs, {RUNS} runs, {NB_ANTS} fourmis)")
    print("=" * 60)
    results = sweep()
    plot(EVAP_RATES, results)