"""Vehicle routing with capacity and time windows (CVRPTW), solved with Google OR-Tools.

Objective: minimise total road distance, plus a fixed cost per van used so the solver
also tries to use fewer vans. Hard constraints: van capacity, delivery windows, back at the
depot by end of shift. If a customer truly cannot fit, the solver may drop them at a very
high penalty (reported as 'missed'; in practice none are dropped).

Times are rounded UP to whole minutes for the solver, so a plan the solver thinks is on time
is also on time when the evaluator drives it with exact times.
"""
from __future__ import annotations
import math
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from instance import Day
import config as C

VAN_FIXED_COST_M = 30_000      # one van costs as much as 30 km of driving in the objective (assumption)
DROP_PENALTY_M = 10_000_000


def solve(day: Day, seconds: int = C.SOLVER_SECONDS, max_vans: int = C.MAX_VANS) -> list[list[int]]:
    n = day.n
    manager = pywrapcp.RoutingIndexManager(n, max_vans, 0)
    routing = pywrapcp.RoutingModel(manager)

    dist_m = [[int(round(day.dist_km[i, j] * 1000)) for j in range(n)] for i in range(n)]
    travel = [[int(math.ceil(day.time_min[i, j])) for j in range(n)] for i in range(n)]
    service = [int(math.ceil(s)) for s in day.service]

    def dist_cb(i, j):
        return dist_m[manager.IndexToNode(i)][manager.IndexToNode(j)]
    dist_idx = routing.RegisterTransitCallback(dist_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(dist_idx)
    routing.SetFixedCostOfAllVehicles(VAN_FIXED_COST_M)

    def demand_cb(i):
        return int(day.parcels[manager.IndexToNode(i)])
    dem_idx = routing.RegisterUnaryTransitCallback(demand_cb)
    routing.AddDimensionWithVehicleCapacity(dem_idx, 0, [C.VAN_CAPACITY] * max_vans, True, "Load")

    def time_cb(i, j):
        a, b = manager.IndexToNode(i), manager.IndexToNode(j)
        return service[a] + travel[a][b]          # serve at i, then drive to j
    time_idx = routing.RegisterTransitCallback(time_cb)
    routing.AddDimension(time_idx, C.SHIFT_END_MIN, C.SHIFT_END_MIN, False, "Time")
    tdim = routing.GetDimensionOrDie("Time")
    for node in range(1, n):
        idx = manager.NodeToIndex(node)
        tdim.CumulVar(idx).SetRange(int(day.win_open[node]), int(day.win_close[node]))
        routing.AddDisjunction([idx], DROP_PENALTY_M)
    for v in range(max_vans):
        tdim.CumulVar(routing.Start(v)).SetRange(0, 0)
        tdim.CumulVar(routing.End(v)).SetRange(0, C.SHIFT_END_MIN)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = seconds
    sol = routing.SolveWithParameters(params)
    if sol is None:
        raise RuntimeError("No solution found")

    routes = []
    for v in range(max_vans):
        idx = routing.Start(v)
        r = []
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            if node != 0:
                r.append(node)
            idx = sol.Value(routing.NextVar(idx))
        if r:
            routes.append(r)
    return routes
