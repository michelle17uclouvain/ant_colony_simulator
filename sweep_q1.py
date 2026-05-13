"""
Q1 — Nombre de fourmis
Lance RUNS runs pour chaque valeur de nb_ants (1 à 200, pas de 20)
sur 05_square_four_food_spots et génère 2 graphiques séparés.
Objectif : env.is_complete() — 75% retirée ET 50% rapportée à la colonie.
"""

import time
import statistics
import matplotlib.pyplot as plt

from utils import create_environment, add_ants

ENV_FILE   = "envs/05_square_four_food_spots.txt"
RUNS       = 10
ANT_COUNTS = list(range(1, 201, 20))


def run_once(ant_count: int):
    env = create_environment(ENV_FILE, 0, 0, verbose=False)
    add_ants(env, "smart", None, ant_count, verbose=False)

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
    results_steps, results_time = [], []

    for n in ANT_COUNTS:
        print(f"  nb_ants={n:3d} ...", end=" ", flush=True)
        steps_list, time_list = [], []

        for _ in range(RUNS):
            s, t = run_once(n)
            if s is not None:
                steps_list.append(s)
                time_list.append(t)

        m_s  = statistics.mean(steps_list)  if steps_list else float("nan")
        sd_s = statistics.stdev(steps_list) if len(steps_list) > 1 else 0
        m_t  = statistics.mean(time_list)   if time_list  else float("nan")
        sd_t = statistics.stdev(time_list)  if len(time_list) > 1 else 0

        results_steps.append((m_s, sd_s))
        results_time.append((m_t, sd_t))
        print(f"steps={m_s:.0f} ± {sd_s:.0f}  |  time={m_t:.2f}s ± {sd_t:.2f}s  ({len(steps_list)}/{RUNS} réussis)")

    return results_steps, results_time


def plot(ant_counts, results_steps, results_time):
    SUBTITLE = "(75% collectée, 33% rapportée à la colonie)"

    # Figure 1 — Steps
    fig1, ax1 = plt.subplots(figsize=(8, 5))
    means = [r[0] for r in results_steps]
    stds  = [r[1] for r in results_steps]
    ax1.errorbar(ant_counts, means, yerr=stds, fmt="o-", capsize=4, color="steelblue")
    ax1.set_xlabel("Nombre de fourmis")
    ax1.set_ylabel("Steps moyens")
    ax1.set_title(f"Steps pour atteindre l'objectif {SUBTITLE}\nen fonction du nombre de fourmis (moyenne ± écart-type)")
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()
    fig1.savefig("figures/q1_steps.pdf", bbox_inches="tight")
    fig1.savefig("figures/q1_steps.png", bbox_inches="tight", dpi=150)
    print("Sauvegardé dans figures/q1_steps.pdf/.png")

    # Figure 2 — Temps
    fig2, ax2 = plt.subplots(figsize=(8, 5))
    means = [r[0] for r in results_time]
    stds  = [r[1] for r in results_time]
    ax2.errorbar(ant_counts, means, yerr=stds, fmt="o-", capsize=4, color="darkorange")
    ax2.set_xlabel("Nombre de fourmis")
    ax2.set_ylabel("Temps moyen (s)")
    ax2.set_title(f"Temps d'exécution moyen (secondes)\nen fonction du nombre de fourmis (moyenne ± écart-type)")
    ax2.grid(True, alpha=0.3)
    fig2.tight_layout()
    fig2.savefig("figures/q1_time.pdf", bbox_inches="tight")
    fig2.savefig("figures/q1_time.png", bbox_inches="tight", dpi=150)
    print("Sauvegardé dans figures/q1_time.pdf/.png")

    plt.show()


if __name__ == "__main__":
    import os
    os.makedirs("figures", exist_ok=True)
    print(f"Q1 — Sweep nb_ants ({len(ANT_COUNTS)} valeurs, {RUNS} runs chacune)")
    print("=" * 60)
    results_steps, results_time = sweep()
    plot(ANT_COUNTS, results_steps, results_time)