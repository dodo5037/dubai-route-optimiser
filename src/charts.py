"""Charts: route map for day 0 (all three methods), and the 20-day comparison."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C
from instance import make_day

ROOT = Path(__file__).resolve().parents[1]
T, CH = ROOT / "outputs" / "tables", ROOT / "outputs" / "charts"
CH.mkdir(parents=True, exist_ok=True)
NAVY, TEAL, PINK, GREY, AMBER = "#1f3864", "#10b981", "#f43f5e", "#9aa5b1", "#f59e0b"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})
PALETTE = ["#0f9f74", "#2563eb", "#f59e0b", "#e11d48", "#7c3aed", "#0891b2", "#65a30d", "#db2777", "#ea580c", "#475569"]

day = make_day(1000)
from evaluate import evaluate  # noqa: E402

# heuristics are instant, so recompute them; the optimiser's day-1 plan is read from the experiment run
import heuristics  # noqa: E402
loaded = {
    "Nearest stop\n(ignores delivery windows)": heuristics.nearest_stop(day),
    "Nearest feasible\n(window-aware greedy)": heuristics.nearest_feasible(day),
    "OR-Tools optimiser": json.loads((T / "routes_day0_or-tools.json").read_text()),
}

fig, axes = plt.subplots(1, 3, figsize=(16, 5.6), sharex=True, sharey=True)
for ax, (title, routes) in zip(axes, loaded.items()):
    e = evaluate(day, routes)
    for k, r in enumerate(routes):
        path = [0] + r + [0]
        ax.plot(day.lon[path], day.lat[path], "-", color=PALETTE[k % 10], lw=1.4, alpha=0.9)
    late = set()
    if "ignores" in title:
        t, prev = 0.0, 0
        for r in routes:
            t, prev = 0.0, 0
            for s in r:
                t += day.time_min[prev, s]; t = max(t, day.win_open[s])
                if t > day.win_close[s]:
                    late.add(s)
                t += day.service[s]; prev = s
    ok = [i for i in range(1, day.n) if i not in late]
    ax.scatter(day.lon[ok], day.lat[ok], s=16, color=NAVY, zorder=3)
    if late:
        ax.scatter(day.lon[list(late)], day.lat[list(late)], s=40, color=PINK, marker="x", zorder=4, label="late delivery")
        ax.legend(loc="lower right", frameon=False, fontsize=8)
    ax.scatter([day.lon[0]], [day.lat[0]], s=140, marker="*", color=AMBER, edgecolor="black", zorder=5)
    for name, la, lo, _ in C.NEIGHBOURHOODS:
        ax.text(lo, la + 0.012, name, fontsize=6.5, color=GREY, ha="center")
    ax.set_title(f"{title}\n{e['km']:.0f} km · {e['vans']} vans · {e['on_time_pct']:.0f}% on time", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
fig.suptitle("Same 60 Dubai deliveries, three ways to route them (day 1 of 20; ★ = Al Quoz depot)", fontsize=12)
fig.tight_layout(); fig.savefig(CH / "01_route_maps.png"); plt.close(fig)

# 20-day comparison
s = pd.read_csv(T / "summary_main.csv")
labels = ["Nearest stop\n(ignores windows)", "Nearest feasible\n(window-aware)", "OR-Tools\noptimiser"]
cols = [GREY, AMBER, TEAL]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
for ax, (k, title, fmt) in zip(axes, [("km", "Road km per day", "{:.0f}"), ("vans", "Vans needed", "{:.1f}"), ("on_time_pct", "On-time deliveries (%)", "{:.0f}%")]):
    bars = ax.bar(labels, s[k], yerr=s[k + "_ci"], color=cols, capsize=3)
    for b, v in zip(bars, s[k]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() * 1.02, fmt.format(v), ha="center", fontsize=9)
    ax.set_title(title); ax.tick_params(axis="x", labelsize=8)
fig.suptitle("Average over 20 random days, 60 stops each (95% CI)", fontsize=11)
fig.tight_layout(); fig.savefig(CH / "02_comparison.png"); plt.close(fig)

# Sensitivity: km by stops per day
sens = pd.read_csv(T / "summary_sensitivity.csv")
fig, ax = plt.subplots(figsize=(7, 4.2))
for (m, g), c in zip(sens.groupby("method", sort=False), cols):
    ax.plot(g["stops"], g["km"], marker="o", color=c, label=m, lw=2)
ax.set_xlabel("Stops per day"); ax.set_ylabel("Road km per day"); ax.set_title("Distance as the day gets busier")
ax.legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(CH / "03_sensitivity.png"); plt.close(fig)
print("charts:", sorted(p.name for p in CH.glob("*.png")))
