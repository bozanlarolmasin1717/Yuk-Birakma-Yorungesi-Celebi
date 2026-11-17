"""Arkadaşınızın fizik/koordinat motorunu 7.1, 7.2 ve 7.3 modüllerine bağlayan adaptör."""

import math
from typing import Any, Callable, Optional
import numpy as np
from balistik_motor import compute_vacum_ballistics, simulate_trajectory
from koordinatsistemi import UavState, environmentParameters, payloadParameters
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


def _to_friend_models(
    inputs: SimulationInputs,
    release_x: float = 0.0,
    release_y: float = 0.0,
) -> tuple[UavState, payloadParameters, environmentParameters]:
    """UI girdilerini arkadaşınızın `koordinatsistemi.py` veri yapılarına dönüştürür."""
    uav = UavState(
        position=np.array([release_x, release_y, inputs.release_altitude_m], dtype=float),
        speed=inputs.uav_speed_mps,
        heading=inputs.uav_heading_deg,
        flight_path_angle=inputs.flight_path_angle_deg,
    )
    payload = payloadParameters(
        mass=inputs.payload_mass_kg,
        cd=inputs.drag_coefficient,
        cross_sectional_area=inputs.payload_area_m2,
    )
    env = environmentParameters(
        g=inputs.gravity_mps2,
        rho_sea_level=inputs.air_density_kgm3,
        use_is=inputs.use_isa,
        wind_speed=inputs.wind_speed_mps,
        wind_director=inputs.wind_from_deg,
        wind_shear_coeff=inputs.wind_shear_coeff,
    )
    return uav, payload, env


def _derive_time_and_speed(
    res: ForwardDropResult,
    step_dt: float | None = 0.01,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """`simulationResult` zaman/hız serisi döndürmediğinde doğru adım zamanlarını ve çarpma hızını türetir."""
    n = len(res.x)
    if n == 0:
        return (), ()
    if res.t and res.speed and len(res.t) == n and len(res.speed) == n:
        return res.t, res.speed

    t_total = max(res.flight_time, 1e-6)
    if n == 1:
        spd = res.impact_speed_mps if res.impact_speed_mps is not None else 0.0
        return (t_total,), (spd,)

    if step_dt is not None and (n - 2) * step_dt < t_total <= (n - 1) * step_dt + 1e-9:
        ts = tuple([i * step_dt for i in range(n - 1)] + [t_total])
    else:
        ts = tuple(t_total * i / (n - 1) for i in range(n))

    speeds: list[float] = []
    for i in range(n):
        if i == n - 1 and res.impact_speed_mps is not None:
            speeds.append(res.impact_speed_mps)
            continue
        i0 = max(0, i - 1)
        i1 = min(n - 1, i + 1)
        dt = max(ts[i1] - ts[i0], 1e-9)
        vx = (res.x[i1] - res.x[i0]) / dt
        vy = (res.y[i1] - res.y[i0]) / dt
        vz = (res.z[i1] - res.z[i0]) / dt
        speeds.append(math.sqrt(vx * vx + vy * vy + vz * vz))
    return ts, tuple(speeds)


def _forward_trajectory_series(
    res: ForwardDropResult,
    release_point: Point3D,
    label: str,
) -> TrajectorySeries:
    actual_impact = Point3D(*res.impact_point)
    ts, speeds = _derive_time_and_speed(res)
    xs = res.x or (release_point.x, actual_impact.x)
    ys = res.y or (release_point.y, actual_impact.y)
    zs = res.z or (release_point.z, actual_impact.z)
    if len(ts) != len(xs):
        ts = (0.0, res.flight_time)
        speeds = (0.0, 0.0)
    return TrajectorySeries(
        label=label,
        x=xs,
        y=ys,
        z=zs,
        t=ts,
        speed=speeds,
        impact_point=actual_impact,
        flight_time=res.flight_time,
        horizontal_range=math.hypot(actual_impact.x - release_point.x, actual_impact.y - release_point.y),
        is_reference=False,
    )


def load_71_scenario(inputs: SimulationInputs) -> DropScenarioView:
    """7.1 Vakum Balistiği: `balistik_motor.compute_vacum_ballistics` ile temel düşüşü üretir."""
    uav, _, env = _to_friend_models(inputs, release_x=0.0, release_y=0.0)
    impact_arr, t_flight = compute_vacum_ballistics(uav, env, z_ground=0.0)
    vx0, vy0, vz0 = (float(v) for v in uav.initial_velocity)

    release_point = Point3D(0.0, 0.0, inputs.release_altitude_m)
    vacuum_series = compute_vacuum_trajectory(
        release=release_point,
        vx0=vx0,
        vy0=vy0,
        gravity=env.g,
        vz0=vz0,
    )
    impact_point = Point3D(float(impact_arr[0]), float(impact_arr[1]), float(impact_arr[2]))
    actual_series = TrajectorySeries(
        label="Vakum Yörüngesi (7.1)",
        x=vacuum_series.x,
        y=vacuum_series.y,
        z=vacuum_series.z,
        t=vacuum_series.t,
        speed=vacuum_series.speed,
        impact_point=impact_point,
        flight_time=float(t_flight),
        horizontal_range=math.hypot(impact_point.x, impact_point.y),
        is_reference=False,
    )

    lead_distance_m = vacuum_series.horizontal_range
    uav_track = build_uav_track(
        release_point=release_point,
        heading_deg=inputs.uav_heading_deg,
        lead_distance_m=lead_distance_m,
        vacuum_range_m=vacuum_series.horizontal_range,
    )
    return DropScenarioView(
        inputs=inputs,
        vacuum_trajectory=vacuum_series,
        actual_trajectory=actual_series,
        uav_track=uav_track,
        wind_vector_mps=(0.0, 0.0),
        release_solution=ReleaseSolutionView(
            release_point=release_point,
            target_point=impact_point,
            lead_distance_m=lead_distance_m,
            lateral_offset_m=0.0,
            predicted_error_m=0.0,
            vacuum_lead_distance_m=lead_distance_m,
            fixed_track_lead_m=lead_distance_m,
            fixed_track_miss_m=0.0,
            solver_iterations=1,
            solver_converged=True,
            solver_method="7.1 Analitik Vakum",
        ),
        drift_from_vacuum_m=0.0,
        is_demo_mode=False,
        scenario_mode="7.1",
    )


def load_72_scenario(inputs: SimulationInputs) -> DropScenarioView:
    """7.2 Hava Sürtünmesi ve Rüzgar: `balistik_motor.simulate_trajectory` (RK4) ile sapmayı hesaplar."""
    uav, payload, env = _to_friend_models(inputs, release_x=0.0, release_y=0.0)
    vac_impact_arr, _ = compute_vacum_ballistics(uav, env, z_ground=0.0)
    rk4_res = simulate_trajectory(uav, payload, env, dt=0.01, z_ground=0.0, record_trajectory=True)

    release_point = Point3D(0.0, 0.0, inputs.release_altitude_m)
    vx0, vy0, vz0 = (float(v) for v in uav.initial_velocity)
    vacuum_series = compute_vacuum_trajectory(
        release=release_point,
        vx0=vx0,
        vy0=vy0,
        gravity=env.g,
        vz0=vz0,
    )

    arr = np.asarray(rk4_res.trajectory, dtype=float)
    forward_res = ForwardDropResult(
        impact_point=(
            float(rk4_res.impact_point[0]),
            float(rk4_res.impact_point[1]),
            float(rk4_res.impact_point[2]),
        ),
        flight_time=float(rk4_res.flight_time),
        x=tuple(float(v) for v in arr[:, 0]),
        y=tuple(float(v) for v in arr[:, 1]),
        z=tuple(float(v) for v in arr[:, 2]),
        impact_speed_mps=float(np.linalg.norm(rk4_res.impact_velocity)),
    )
    actual_series = _forward_trajectory_series(forward_res, release_point, "Cd + Rüzgar (7.2 RK4)")

    vac_impact = Point3D(float(vac_impact_arr[0]), float(vac_impact_arr[1]), float(vac_impact_arr[2]))
    drift_from_vacuum_m = math.hypot(
        actual_series.impact_point.x - vac_impact.x,
        actual_series.impact_point.y - vac_impact.y,
    )

    (hx, hy), _ = heading_basis(inputs.uav_heading_deg)
    along_dist = actual_series.impact_point.x * hx + actual_series.impact_point.y * hy
    uav_track = build_uav_track(
        release_point=release_point,
        heading_deg=inputs.uav_heading_deg,
        lead_distance_m=along_dist,
        vacuum_range_m=vacuum_series.horizontal_range,
    )
    wind_vec = env.wind_vector(inputs.release_altitude_m)
    return DropScenarioView(
        inputs=inputs,
        vacuum_trajectory=vacuum_series,
        actual_trajectory=actual_series,
        uav_track=uav_track,
        wind_vector_mps=(float(wind_vec[0]), float(wind_vec[1])),
        release_solution=ReleaseSolutionView(
            release_point=release_point,
            target_point=actual_series.impact_point,
            lead_distance_m=along_dist,
            lateral_offset_m=0.0,
            predicted_error_m=0.0,
            vacuum_lead_distance_m=vacuum_series.horizontal_range,
            fixed_track_lead_m=along_dist,
            fixed_track_miss_m=0.0,
            solver_iterations=1,
            solver_converged=True,
            solver_method="7.2 RK4 (dt=0.01 s)",
        ),
        drift_from_vacuum_m=drift_from_vacuum_m,
        is_demo_mode=False,
        scenario_mode="7.2",
    )


def build_scenario_from_friend_physics(
    inputs: SimulationInputs,
    friend_simulate_fn: Callable[[Any, Any, Any], Any],
    uav_template: Any,
    payload: Any,
    environment: Any,
    probe_simulate_fn: Optional[Callable[[Any, Any, Any], Any]] = None,
) -> DropScenarioView:
    """Arkadaşınızın 7.1+7.2 ileri fizik motorunu 7.3 hedefleme ve görselleştirmeye bağlar."""
    final_forward_fn = adapt_friend_simulator(friend_simulate_fn, uav_template, payload, environment)
    probe_forward_fn = (
        adapt_friend_simulator(probe_simulate_fn, uav_template, payload, environment)
        if probe_simulate_fn is not None
        else final_forward_fn
    )

    gamma_deg = float(getattr(uav_template, "flight_path_angle", inputs.flight_path_angle_deg))
    gravity = float(getattr(environment, "g", inputs.gravity_mps2))

    solution, forward_res = solve_release_point(
        simulate_fn=probe_forward_fn,
        target_point=(inputs.target_x_m, inputs.target_y_m, 0.0),
        release_altitude_m=inputs.release_altitude_m,
        uav_speed_mps=inputs.uav_speed_mps,
        uav_heading_deg=inputs.uav_heading_deg,
        flight_path_angle_deg=gamma_deg,
        gravity_mps2=gravity,
    )

    if not forward_res.x:
        forward_res = final_forward_fn(*solution.release_point)

    release_point = Point3D(*solution.release_point)
    target_point = Point3D(*solution.target_point)
    actual_series = _forward_trajectory_series(forward_res, release_point, "Gerçekçi (Cd + Rüzgar)")
    actual_impact = actual_series.impact_point

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

    wind_fn = getattr(environment, "wind_vector", None)
    if callable(wind_fn):
        w_vec = wind_fn(inputs.release_altitude_m)
        wind_vector_mps = (float(w_vec[0]), float(w_vec[1]))
    else:
        wind_vector_mps = wind_from_to_vector(inputs.wind_speed_mps, inputs.wind_from_deg)

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
        wind_vector_mps=wind_vector_mps,
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
        scenario_mode="7.3",
    )


def load_scenario(
    inputs: SimulationInputs,
    solver: Optional[ScenarioSolver] = None,
) -> DropScenarioView:
    """Harici bir çözücü verilmişse onu, aksi halde gerçek `balistik_motor` RK4 motorunu çalıştırır."""
    if solver is not None:
        return solver(inputs)

    uav, payload, env = _to_friend_models(inputs, release_x=0.0, release_y=0.0)
    return build_scenario_from_friend_physics(
        inputs=inputs,
        friend_simulate_fn=lambda u, p, e: simulate_trajectory(u, p, e, dt=0.01, z_ground=0.0, record_trajectory=True),
        uav_template=uav,
        payload=payload,
        environment=env,
        probe_simulate_fn=lambda u, p, e: simulate_trajectory(u, p, e, dt=0.01, z_ground=0.0, record_trajectory=False),
    )
