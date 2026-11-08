"""Two simple 'dispatcher' baselines to compare the optimiser against.

1. nearest_stop: fill one van at a time; always drive to the closest unvisited customer that
   still fits in the van and leaves time to get back by end of shift. Ignores delivery windows.
   This is what a busy dispatcher (or a driver choosing their own order) tends to do.
2. nearest_feasible: same, but only picks a customer it can still reach before their window
   closes (waiting if early). On time by construction, but greedy, so it wastes kilometres.
"""
from __future__ import annotations
import numpy as np
from instance import Day
import config as C


def _greedy(day: Day, respect_windows: bool) -> list[list[int]]:
    left = set(range(1, day.n))
    routes = []
    while left and len(routes) < 50:
        route, t, prev, load = [], 0.0, 0, 0
        while True:
            best, best_d = None, np.inf
            for s in left:
                if load + day.parcels[s] > C.VAN_CAPACITY:
                    continue
                arrive = t + day.time_min[prev, s]
                start = max(arrive, day.win_open[s])  # early vans wait for the window either way
                if respect_windows and start > day.win_close[s]:
                    continue
                finish = start + day.service[s]
                if finish + day.time_min[s, 0] > C.SHIFT_END_MIN:
                    continue
                d = day.dist_km[prev, s]
                if d < best_d:
                    best, best_d = s, d
            if best is None:
                break
            arrive = t + day.time_min[prev, best]
            t = max(arrive, day.win_open[best])
            t += day.service[best]
            load += int(day.parcels[best])
            route.append(best)
            left.remove(best)
            prev = best
        if not route:
            break  # nothing fits a fresh van: remaining customers can't be served
        routes.append(route)
    return routes


def nearest_stop(day: Day) -> list[list[int]]:
    return _greedy(day, respect_windows=False)


def nearest_feasible(day: Day) -> list[list[int]]:
    return _greedy(day, respect_windows=True)
