"""Checks that every plan is valid and that the evaluator itself is correct."""
import sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import config as C  # noqa: E402
from instance import make_day, haversine_km  # noqa: E402
from heuristics import nearest_stop, nearest_feasible  # noqa: E402
from optimise import solve  # noqa: E402
from evaluate import evaluate  # noqa: E402

DAY = make_day(1000)


def test_haversine_known_distance():
    # Dubai Marina to Deira is roughly 27-28 km in a straight line
    d = haversine_km(25.0805, 55.1403, 25.2710, 55.3070)
    assert 26 < d < 29


def test_matrices_are_symmetric_and_zero_on_diagonal():
    assert np.allclose(DAY.dist_km, DAY.dist_km.T)
    assert np.allclose(np.diag(DAY.dist_km), 0)


def test_same_seed_same_day():
    a, b = make_day(7), make_day(7)
    assert np.array_equal(a.lat, b.lat) and np.array_equal(a.win_open, b.win_open)


def test_evaluator_by_hand():
    """One van, one stop: distance = there and back; on time if within window."""
    r = evaluate(DAY, [[1]])
    assert r["km"] == pytest.approx(DAY.dist_km[0, 1] + DAY.dist_km[1, 0])
    assert r["stops_served"] == 1 and r["missed"] == DAY.n - 2


@pytest.mark.parametrize("method", [nearest_stop, nearest_feasible, lambda d: solve(d, 5)],
                         ids=["nearest", "feasible", "ortools"])
def test_every_stop_served_once_within_capacity_and_shift(method):
    r = evaluate(DAY, method(DAY))
    assert r["missed"] == 0
    assert r["duplicates"] == 0
    assert r["vans_over_capacity"] == 0
    assert r["vans_back_late"] == 0


@pytest.mark.parametrize("method", [nearest_feasible, lambda d: solve(d, 5)], ids=["feasible", "ortools"])
def test_window_aware_methods_are_always_on_time(method):
    assert evaluate(DAY, method(DAY))["on_time_pct"] == pytest.approx(100.0)


def test_optimiser_beats_window_aware_greedy_on_distance():
    assert evaluate(DAY, solve(DAY, 5))["km"] < evaluate(DAY, nearest_feasible(DAY))["km"]


def test_optimiser_uses_no_more_vans_than_needed_by_capacity():
    min_vans = int(np.ceil(DAY.parcels.sum() / C.VAN_CAPACITY))
    assert evaluate(DAY, solve(DAY, 5))["vans"] >= min_vans
