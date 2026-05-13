"""
Q3 — Pourcentage de cheaters
Lance RUNS runs pour chaque % de cheaters (0% à 100%, pas de 10%)
sur 05_square_four_food_spots avec 70 fourmis au total.
Les fourmis non-cheaters utilisent la stratégie smart.
Génère 3 graphiques : steps, temps réel, throughput.
"""

import time
import statistics
import math
import random
import matplotlib.pyplot as plt

from utils import create_environment
from ant import Ant
from common import Direction
from strategies.smart import SmartStrategy
from strategies.cheater import CheaterStrategy

ENV_FILE     = "envs/05_square_four_food_spots.txt"
TOTAL_ANTS   = 70
RUNS         = 1
CHEATER_PCTS = list(range(0, 101, 10))   # 0, 10, 20, ..., 100


def add_mixed_ants(env, n_cheaters: int, n_smart: int) -> None:
    if not env.colony_positions:
        raise ValueError("No colony positions in environment")

    # Shared strategy instances
    cheater_strat = CheaterStrategy()
    cheater_strat.set_environment(env)
    smart_strat = SmartStrategy()

    total = n_cheaters + n_smart
    for i in range(total):
        colony_pos = env.colony_positions[i % len(env.colony_positions)]
        x, y = colony_pos
        direction = random.choice(list(Direction))
        strat = cheater_strat if i < n_cheaters else smart_strat
        ant = Ant(x, y, direction, strat, ant_id=env.next_ant_id)
        env.next_ant_id += 1
        env.add_ant(ant)


def run_once(pct_cheaters: int):
    env = create_environment(ENV_FILE, 0, 0, verbose=False)

    n_cheaters = round(TOTAL_ANTS * pct_cheaters / 100)
    n_smart    = TOTAL_ANTS - n_cheaters
    add_mixed_ants(env, n_cheaters, n_smart)

    start      = time.time()
    step       = 0
    max_steps  = env.max_steps or 10_000
    time_limit = env.time_limit or 300

    while step < max_steps and (time.time() - start) < time_limit:
        env.update()
        step += 1
        if env.is_complete():
            elapsed = time.time() - start
            throughput = step / elapsed if elapsed > 0 else float("nan")
            return step, elapsed, throughput

    return None, None, None


def sweep():
    results = []   # list of (mean_steps, sd_steps, mean_time, sd_time, mean_tp, sd_tp)

    for pct in CHEATER_PCTS:
        print(f"  cheaters={pct:3d}% ...", end=" ", flush=True)
        steps_list, time_list, tp_list = [], [], []

        for _ in range(RUNS):
            s, t, tp = run_once(pct)
            if s is not None:
                steps_list.append(s)
                time_list.append(t)
                tp_list.append(tp)

        m_s  = statistics.mean(steps_list)  if steps_list else float("nan")
        sd_s = statistics.stdev(steps_list) if len(steps_list) > 1 else 0
        m_t  = statistics.mean(time_list)   if time_list  else float("nan")
        sd_t = statistics.stdev(time_list)  if len(time_list)  > 1 else 0
        m_tp = statistics.mean(tp_list)     if tp_list    else float("nan")
        sd_tp= statistics.stdev(tp_list)    if len(tp_list)   > 1 else 0

        results.append((m_s, sd_s, m_t, sd_t, m_tp, sd_tp))
        ok = len(steps_list)
        print(f"steps={m_s:.0f}±{sd_s:.0f}  time={m_t:.2f}s±{sd_t:.2f}s  "
              f"tp={m_tp:.1f}±{sd_tp:.1f} steps/s  ({ok}/{RUNS} réussis)")

    return results


def plot(pcts, results):
    SUBTITLE = "(75% collectée, 33% rapportée à la colonie)"

    def _vals(idx):
        return [r[idx] for r in results], [r[idx + 1] for r in results]

    # Figure 4 — Steps
    fig4, ax4 = plt.subplots(figsize=(9, 5))
    m, s = _vals(0)
    ax4.errorbar(pcts, m, yerr=s, fmt="o-", capsize=4, color="steelblue")
    ax4.set_xlabel("% de cheaters")
    ax4.set_ylabel("Steps moyens")
    ax4.set_title(f"Steps pour atteindre l'objectif {SUBTITLE}\n"
                  f"en fonction du % de cheaters (moyenne ± écart-type)")
    ax4.grid(True, alpha=0.3)
    fig4.tight_layout()
    fig4.savefig("figures/q3_steps.pdf", bbox_inches="tight")
    fig4.savefig("figures/q3_steps.png", bbox_inches="tight", dpi=150)
    print("Sauvegardé dans figures/q3_steps.pdf/.png")

    # Figure 5 — Temps réel
    fig5, ax5 = plt.subplots(figsize=(9, 5))
    m, s = _vals(2)
    ax5.errorbar(pcts, m, yerr=s, fmt="o-", capsize=4, color="darkorange")
    ax5.set_xlabel("% de cheaters")
    ax5.set_ylabel("Temps réel moyen (s)")
    ax5.set_title(f"Temps d'exécution réel (secondes) pour atteindre l'objectif {SUBTITLE}\n"
                  f"en fonction du % de cheaters (moyenne ± écart-type)")
    ax5.grid(True, alpha=0.3)
    fig5.tight_layout()
    fig5.savefig("figures/q3_time.pdf", bbox_inches="tight")
    fig5.savefig("figures/q3_time.png", bbox_inches="tight", dpi=150)
    print("Sauvegardé dans figures/q3_time.pdf/.png")

    # Figure 6 — Throughput
    fig6, ax6 = plt.subplots(figsize=(9, 5))
    m, s = _vals(4)
    ax6.errorbar(pcts, m, yerr=s, fmt="o-", capsize=4, color="mediumseagreen")
    ax6.set_xlabel("% de cheaters")
    ax6.set_ylabel("Throughput (steps/s)")
    ax6.set_title(f"Throughput (steps/seconde)\n"
                  f"en fonction du % de cheaters (moyenne ± écart-type)")
    ax6.grid(True, alpha=0.3)
    fig6.tight_layout()
    fig6.savefig("figures/q3_throughput.pdf", bbox_inches="tight")
    fig6.savefig("figures/q3_throughput.png", bbox_inches="tight", dpi=150)
    print("Sauvegardé dans figures/q3_throughput.pdf/.png")

    plt.show()


if __name__ == "__main__":
    import os
    os.makedirs("figures", exist_ok=True)
    print(f"Q3 — Sweep cheaters ({len(CHEATER_PCTS)} valeurs, {RUNS} runs, {TOTAL_ANTS} fourmis)")
    print("=" * 60)
    results = sweep()
    plot(CHEATER_PCTS, results)
