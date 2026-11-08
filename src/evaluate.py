"""One independent evaluator for every method, so all plans are scored the same way.

A plan is a list of routes; each route is a list of stop indices (depot = 0 is implied
at the start and end). The evaluator drives each route: van leaves at 09:00, waits if it
arrives before a customer's window opens, serves, and records lateness if it arrives after
the window closes.
"""
from __future__ import annotations
import numpy as np
from instance import Day
import config as C


def evaluate(day: Day, routes: list[list[int]]) -> dict:
    km = drive = wait = 0.0
    late_stops = 0
    late_min = 0.0
    served = []
    loads = []
    over_capacity = 0
    back_late = 0
    for r in routes:
        if not r:
            continue
        t, prev, load = 0.0, 0, 0
        for s in r:
            km += day.dist_km[prev, s]
            drive += day.time_min[prev, s]
            t += day.time_min[prev, s]
            if t < day.win_open[s]:
                wait += day.win_open[s] - t
                t = day.win_open[s]
            if t > day.win_close[s] + 1e-9:
                late_stops += 1
                late_min += t - day.win_close[s]
            t += day.service[s]
            load += int(day.parcels[s])
            served.append(s)
            prev = s
        km += day.dist_km[prev, 0]
        drive += day.time_min[prev, 0]
        t += day.time_min[prev, 0]
        if t > C.SHIFT_END_MIN + 1e-9:
            back_late += 1
        loads.append(load)
        if load > C.VAN_CAPACITY:
            over_capacity += 1
    stops = day.n - 1
    return {
        "vans": sum(1 for r in routes if r),
        "km": km,
        "drive_h": drive / 60,
        "wait_h": wait / 60,
        "stops_served": len(set(served)),
        "duplicates": len(served) - len(set(served)),
        "missed": stops - len(set(served)),
        "late_stops": late_stops,
        "on_time_pct": 100 * (len(set(served)) - late_stops) / stops,
        "late_min_total": late_min,
        "vans_back_late": back_late,
        "vans_over_capacity": over_capacity,
        "avg_load_pct": 100 * np.mean(loads) / C.VAN_CAPACITY if loads else 0.0,
    }
