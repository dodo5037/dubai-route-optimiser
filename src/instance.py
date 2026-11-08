"""Generate one synthetic delivery day and its distance / time matrices."""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
import config as C


@dataclass
class Day:
    names: list[str]            # index 0 = depot
    lat: np.ndarray
    lon: np.ndarray
    parcels: np.ndarray         # 0 for depot
    win_open: np.ndarray        # minutes after 09:00
    win_close: np.ndarray
    service: np.ndarray         # minutes per stop
    dist_km: np.ndarray         # road km (estimated)
    time_min: np.ndarray        # driving minutes

    @property
    def n(self) -> int:
        return len(self.names)


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dl = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def make_day(seed: int, stops: int = C.STOPS_PER_DAY) -> Day:
    rng = np.random.default_rng(seed)
    w = np.array([h[3] for h in C.NEIGHBOURHOODS], dtype=float)
    hood = rng.choice(len(C.NEIGHBOURHOODS), size=stops, p=w / w.sum())
    km_per_deg_lat = 111.0
    lat = np.empty(stops); lon = np.empty(stops); names = []
    for i, h in enumerate(hood):
        name, la, lo, _ = C.NEIGHBOURHOODS[h]
        dy, dx = rng.normal(0, C.SCATTER_KM, 2)
        lat[i] = la + dy / km_per_deg_lat
        lon[i] = lo + dx / (km_per_deg_lat * math.cos(math.radians(la)))
        names.append(f"{name} #{i + 1}")
    parcels = rng.integers(C.PARCELS_PER_STOP[0], C.PARCELS_PER_STOP[1] + 1, size=stops)
    win_open = np.zeros(stops); win_close = np.full(stops, float(C.WINDOWS[-1][1]))
    has_window = rng.random(stops) < C.SHARE_WITH_WINDOW
    pick = rng.integers(0, len(C.WINDOWS), size=stops)
    for i in range(stops):
        if has_window[i]:
            win_open[i], win_close[i] = C.WINDOWS[pick[i]]

    all_lat = np.concatenate([[C.DEPOT[1]], lat]); all_lon = np.concatenate([[C.DEPOT[2]], lon])
    d = haversine_km(all_lat[:, None], all_lon[:, None], all_lat[None, :], all_lon[None, :]) * C.CIRCUITY
    t = d / C.SPEED_KMH * 60
    service = np.concatenate([[0.0], C.SERVICE_MIN_PER_STOP + C.SERVICE_MIN_PER_PARCEL * parcels])
    return Day(
        names=[C.DEPOT[0]] + names, lat=all_lat, lon=all_lon,
        parcels=np.concatenate([[0], parcels]),
        win_open=np.concatenate([[0.0], win_open]), win_close=np.concatenate([[float(C.SHIFT_END_MIN)], win_close]),
        service=service, dist_km=d, time_min=t,
    )
