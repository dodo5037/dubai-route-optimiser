"""Compare the two dispatcher baselines with the OR-Tools optimiser over 20 random days,
then check how the result changes with 40 and 80 stops per day.

Every plan is scored by the same evaluator (evaluate.py). Means are reported with a 95%
confidence interval across days.
"""
from pathlib import Path
import json
import time
import numpy as np
import pandas as pd
import config as C
from instance import make_day
from heuristics import nearest_stop, nearest_feasible
from optimise import solve
from evaluate import evaluate

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "outputs" / "tables"
T.mkdir(parents=True, exist_ok=True)
METHODS = {"Nearest stop (ignores windows)": nearest_stop,
           "Nearest feasible (window-aware greedy)": nearest_feasible,
           "OR-Tools optimiser": solve}
T95 = {20: 2.093, 5: 2.776}  # two-sided t values for n-1 degrees of freedom


def run(stops, days, tag, seed0):
    rows = []
    for d in range(days):
        day = make_day(seed0 + d, stops)
        for name, f in METHODS.items():
            t0 = time.time()
            routes = f(day)
            r = evaluate(day, routes)
            r.update(method=name, day=d, stops=stops, seconds=time.time() - t0)
            rows.append(r)
            if tag == "main" and d == 0 and name.startswith("OR-Tools"):
                (T / "routes_day0_or-tools.json").write_text(json.dumps(routes))
        print(f"  {tag}: day {d + 1}/{days} done", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(T / f"days_{tag}.csv", index=False)
    return df


def summarise(df):
    n = df["day"].nunique()
    t = T95.get(n, 2.0)
    out = []
    for name, g in df.groupby("method", sort=False):
        row = {"method": name}
        for k in ["vans", "km", "drive_h", "wait_h", "on_time_pct", "late_stops", "missed", "avg_load_pct", "seconds"]:
            row[k] = g[k].mean()
            row[k + "_ci"] = t * g[k].std(ddof=1) / np.sqrt(n)
        out.append(row)
    return pd.DataFrame(out)


if __name__ == "__main__":
    main = run(C.STOPS_PER_DAY, C.DAYS, "main", 1000)
    s = summarise(main)
    s.to_csv(T / "summary_main.csv", index=False)
    # paired savings of the optimiser vs each baseline, per day
    piv = main.pivot(index="day", columns="method", values="km")
    sav = []
    for base in list(METHODS)[:2]:
        pct = 100 * (piv[base] - piv["OR-Tools optimiser"]) / piv[base]
        sav.append({"vs": base, "km_saving_pct_mean": pct.mean(), "km_saving_pct_ci": T95[C.DAYS] * pct.std(ddof=1) / np.sqrt(len(pct)),
                    "min": pct.min(), "max": pct.max()})
    pd.DataFrame(sav).to_csv(T / "savings_main.csv", index=False)

    sens = []
    for stops in C.SENSITIVITY_STOPS:
        df = run(stops, C.SENSITIVITY_DAYS, f"sens{stops}", 5000 + stops)
        sm = summarise(df); sm.insert(0, "stops", stops); sens.append(sm)
    ms = s.copy(); ms.insert(0, "stops", C.STOPS_PER_DAY)
    pd.concat([sens[0], ms, sens[1]]).to_csv(T / "summary_sensitivity.csv", index=False)

    pd.set_option("display.width", 200)
    cols = ["method", "vans", "km", "drive_h", "on_time_pct", "late_stops", "missed", "avg_load_pct", "seconds"]
    print("\nMAIN (60 stops, 20 days):")
    print(s[cols].round(2).to_string(index=False))
    print("\nKm saving of the optimiser (paired by day):")
    print(pd.DataFrame(sav).round(2).to_string(index=False))
    print("\nSENSITIVITY:")
    print(pd.concat([sens[0], ms, sens[1]])[["stops"] + cols].round(2).to_string(index=False))
