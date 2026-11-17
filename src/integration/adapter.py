"""Arkadaşınızın fizik/koordinat motorunu 7.3 hedefleme ve görselleştirmeye bağlayan adaptör."""

import math
from typing import Any, Callable, Optional
from src.integration.demo_provider import build_demo_scenario
from src.targeting import ForwardDropResult, adapt_friend_simulator, solve_release_point
from src.visualization.geometry import (
    build_uav_track,
    compute_vacuum_trajectory,
    heading_basis,
    wind_from_to_vector,
)
from src.visualization.schemas import (
    DropScenarioView,
    Point3D,
    ReleaseSolutionView,
    SimulationInputs,
    TrajectorySeries,
)

ScenarioSolver = Callable[[SimulationInputs], DropScenarioView]


def _derive_time_and_speed(
    res: ForwardDropResult,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """`simulationResult` yalnızca konum dizisi döndürdüğünde zaman ve hız büyüklüğünü türetir."""
    n = len(res.x)
    if n == 0:
        return (), ()
    if res.t and res.speed and len(res.t) == n and len(res.speed) == n:
        return res.t, res.speed

    t_total = max(res.flight_time, 1e-6)
    if n == 1:
        return (t_total,), (0.0,)

    ts = tuple(t_total * i / (n - 1) for i in range(n))
    speeds: list[float] = []
    for i in range(n):
        i0 = max(0, i - 1)
        i1 = min(n - 1, i + 1)
        dt = max(ts[i1] - ts[i0], 1e-9)
        vx = (res.x[i1] - res.x[i0]) / dt
        vy = (res.y[i1] - res.y[i0]) / dt
        vz = (res.z[i1] - res.z[i0]) / dt
        speeds.append(math.sqrt(vx * vx + vy * vy + vz * vz))
    return ts, tuple(speeds)


def build_scenario_from_friend_physics(
    inputs: SimulationInputs,
    friend_simulate_fn: Callable[[Any, Any, Any], Any],
    uav_template: Any,
    payload: Any,
    environment: Any,
) -> DropScenarioView:
    """Arkadaşınızın 7.1+7.2 ileri fizik motorunu 7.3 hedefleme ve görselleştirmeye bağlar."""
    forward_fn = adapt_friend_simulator(friend_simulate_fn, uav_template, payload, environment)

    gamma_deg = float(getattr(uav_template, "flight_path_angle", 0.0))
    gravity = float(getattr(environment, "g", inputs.gravity_mps2))

    solution, forward_res = solve_release_point(
        simulate_fn=forward_fn,
        target_point=(inputs.target_x_m, inputs.target_y_m, 0.0),
        release_altitude_m=inputs.release_altitude_m,
        uav_speed_mps=inputs.uav_speed_mps,
        uav_heading_deg=inputs.uav_heading_deg,
        flight_path_angle_deg=gamma_deg,
        gravity_mps2=gravity,
    )

    release_point = Point3D(*solution.release_point)
    target_point = Point3D(*solution.target_point)
    actual_impact = Point3D(*forward_res.impact_point)
    ts, speeds = _derive_time_and_speed(forward_res)

    xs = forward_res.x or (release_point.x, actual_impact.x)
    ys = forward_res.y or (release_point.y, actual_impact.y)
    zs = forward_res.z or (release_point.z, actual_impact.z)
    if len(ts) != len(xs):
        ts = (0.0, forward_res.flight_time)
        speeds = (inputs.uav_speed_mps, inputs.uav_speed_mps)

    actual_series = TrajectorySeries(
        label="Gerçekçi (Cd + Rüzgar)",
        x=xs,
        y=ys,
        z=zs,
        t=ts,
        speed=speeds,
        impact_point=actual_impact,
        flight_time=forward_res.flight_time,
        horizontal_range=math.hypot(actual_impact.x - release_point.x, actual_impact.y - release_point.y),
        is_reference=False,
    )

    (hx, hy), _ = heading_basis(inputs.uav_heading_deg)
    gamma_rad = math.radians(gamma_deg)
    vh0 = inputs.uav_speed_mps * math.cos(gamma_rad)
    vz0 = inputs.uav_speed_mps * math.sin(gamma_rad)
    vacuum_series = compute_vacuum_trajectory(
        release=release_point,
        vx0=vh0 * hx,
        vy0=vh0 * hy,
        gravity=gravity,
        vz0=vz0,
    )

    wx, wy = wind_from_to_vector(inputs.wind_speed_mps, inputs.wind_from_deg)
    drift_from_vacuum_m = math.hypot(
        actual_impact.x - vacuum_series.impact_point.x,
        actual_impact.y - vacuum_series.impact_point.y,
    )
    uav_track = build_uav_track(
        release_point=release_point,
        heading_deg=inputs.uav_heading_deg,
        lead_distance_m=solution.lead_distance_m,
        vacuum_range_m=vacuum_series.horizontal_range,
    )

    return DropScenarioView(
        inputs=inputs,
        vacuum_trajectory=vacuum_series,
        actual_trajectory=actual_series,
        uav_track=uav_track,
        wind_vector_mps=(wx, wy),
        release_solution=ReleaseSolutionView(
            release_point=release_point,
            target_point=target_point,
            lead_distance_m=solution.lead_distance_m,
            lateral_offset_m=solution.lateral_offset_m,
            predicted_error_m=solution.predicted_error_m,
            vacuum_lead_distance_m=solution.vacuum_lead_distance_m,
            fixed_track_lead_m=solution.fixed_track_lead_m,
            fixed_track_miss_m=solution.fixed_track_miss_m,
            solver_iterations=solution.iterations,
            solver_converged=solution.converged,
            solver_method=solution.method,
        ),
        drift_from_vacuum_m=drift_from_vacuum_m,
        is_demo_mode=False,
    )


def load_scenario(
    inputs: SimulationInputs,
    solver: Optional[ScenarioSolver] = None,
) -> DropScenarioView:
    """Harici bir çözücü verilmişse onu, verilmemişse geçici demo sağlayıcıyı çalıştırır."""
    if solver is not None:
        return solver(inputs)
    return build_demo_scenario(inputs)
