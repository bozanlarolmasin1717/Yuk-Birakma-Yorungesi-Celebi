"""Gerçek fizik motoru bağlanana kadar arayüzü besleyen geçici demo veri üretici.

Bu modül yalnızca sürgülerin canlı tepki vermesi için yaklaşık bir yörünge ve
bırakma noktası üretir. Arkadaşınızın koordinat/fizik motoru tamamlandığında
`src/integration/adapter.py` üzerinden gerçek hesaplamaya geçilecektir.
"""

import math
from src.targeting import ForwardDropResult, solve_release_point
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


def _integrate_demo_drag(
    inputs: SimulationInputs,
    vx0: float,
    vy0: float,
    wx: float,
    wy: float,
    dt: float = 0.04,
) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    """Orta nokta (RK2) yöntemiyle yaklaşık sürtünmeli+rüzgarlı yer değiştirme üretir."""
    k_drag = 0.5 * inputs.air_density_kgm3 * inputs.drag_coefficient * inputs.payload_area_m2 / max(inputs.payload_mass_kg, 0.05)

    def accel(vx: float, vy: float, vz: float) -> tuple[float, float, float]:
        rx = vx - wx
        ry = vy - wy
        rz = vz
        rel_mag = math.sqrt(rx * rx + ry * ry + rz * rz)
        return (
            -k_drag * rel_mag * rx,
            -k_drag * rel_mag * ry,
            -inputs.gravity_mps2 - k_drag * rel_mag * rz,
        )

    x = 0.0
    y = 0.0
    z = inputs.release_altitude_m
    vx, vy, vz = vx0, vy0, 0.0
    t = 0.0

    xs = [x]
    ys = [y]
    zs = [z]
    ts = [t]
    speeds = [math.hypot(vx, vy)]

    max_steps = 15000
    for _ in range(max_steps):
        ax1, ay1, az1 = accel(vx, vy, vz)
        vx_mid = vx + 0.5 * dt * ax1
        vy_mid = vy + 0.5 * dt * ay1
        vz_mid = vz + 0.5 * dt * az1
        ax2, ay2, az2 = accel(vx_mid, vy_mid, vz_mid)

        nx = x + dt * vx_mid
        ny = y + dt * vy_mid
        nz = z + dt * vz_mid
        nvx = vx + dt * ax2
        nvy = vy + dt * ay2
        nvz = vz + dt * az2

        if nz <= 0.0:
            alpha = z / max(z - nz, 1e-9)
            fx = x + alpha * (nx - x)
            fy = y + alpha * (ny - y)
            ft = t + alpha * dt
            fvx = vx + alpha * (nvx - vx)
            fvy = vy + alpha * (nvy - vy)
            fvz = vz + alpha * (nvz - vz)
            xs.append(fx)
            ys.append(fy)
            zs.append(0.0)
            ts.append(ft)
            speeds.append(math.sqrt(fvx * fvx + fvy * fvy + fvz * fvz))
            break

        x, y, z = nx, ny, nz
        vx, vy, vz = nvx, nvy, nvz
        t += dt
        xs.append(x)
        ys.append(y)
        zs.append(z)
        ts.append(t)
        speeds.append(math.sqrt(vx * vx + vy * vy + vz * vz))

    return xs, ys, zs, ts, speeds


def build_demo_scenario(inputs: SimulationInputs) -> DropScenarioView:
    """Geçici ileri sürükleme+rüzgar simülatörü üzerinde gerçek 7.3 çözücüyü çalıştırır."""
    (hx, hy), _ = heading_basis(inputs.uav_heading_deg)
    vx0 = inputs.uav_speed_mps * hx
    vy0 = inputs.uav_speed_mps * hy
    wx, wy = wind_from_to_vector(inputs.wind_speed_mps, inputs.wind_from_deg)

    # İleri fizik yatayda öteleme bağımsız olsa da, 7.3 çözücüyü gerçek kara-kutu
    # sözleşmesiyle doğrulamak için tam ForwardSimulatorFn imzasıyla sarıyoruz.
    rel_xs, rel_ys, rel_zs, rel_ts, rel_speeds = _integrate_demo_drag(inputs, vx0, vy0, wx, wy)

    def _forward_drop_demo(rx: float, ry: float, rz: float) -> ForwardDropResult:
        if abs(rz - inputs.release_altitude_m) < 1e-9:
            xs = tuple(rx + dx for dx in rel_xs)
            ys = tuple(ry + dy for dy in rel_ys)
            zs = tuple(rel_zs)
            ts = tuple(rel_ts)
            spds = tuple(rel_speeds)
        else:
            sub_inputs = SimulationInputs(
                uav_speed_mps=inputs.uav_speed_mps,
                uav_heading_deg=inputs.uav_heading_deg,
                release_altitude_m=rz,
                payload_mass_kg=inputs.payload_mass_kg,
                payload_area_m2=inputs.payload_area_m2,
                drag_coefficient=inputs.drag_coefficient,
                payload_shape=inputs.payload_shape,
                wind_speed_mps=inputs.wind_speed_mps,
                wind_from_deg=inputs.wind_from_deg,
                target_x_m=inputs.target_x_m,
                target_y_m=inputs.target_y_m,
                gravity_mps2=inputs.gravity_mps2,
                air_density_kgm3=inputs.air_density_kgm3,
            )
            lxs, lys, lzs, lts, lspds = _integrate_demo_drag(sub_inputs, vx0, vy0, wx, wy)
            xs = tuple(rx + dx for dx in lxs)
            ys = tuple(ry + dy for dy in lys)
            zs = tuple(lzs)
            ts = tuple(lts)
            spds = tuple(lspds)

        return ForwardDropResult(
            impact_point=(xs[-1], ys[-1], zs[-1]),
            flight_time=ts[-1],
            x=xs,
            y=ys,
            z=zs,
            t=ts,
            speed=spds,
        )

    target_point = Point3D(inputs.target_x_m, inputs.target_y_m, 0.0)
    solution, forward_res = solve_release_point(
        simulate_fn=_forward_drop_demo,
        target_point=(target_point.x, target_point.y, target_point.z),
        release_altitude_m=inputs.release_altitude_m,
        uav_speed_mps=inputs.uav_speed_mps,
        uav_heading_deg=inputs.uav_heading_deg,
        gravity_mps2=inputs.gravity_mps2,
    )

    release_point = Point3D(*solution.release_point)
    actual_impact = Point3D(*forward_res.impact_point)

    actual_series = TrajectorySeries(
        label="Gerçekçi (Cd + Rüzgar)",
        x=forward_res.x,
        y=forward_res.y,
        z=forward_res.z,
        t=forward_res.t,
        speed=forward_res.speed,
        impact_point=actual_impact,
        flight_time=forward_res.flight_time,
        horizontal_range=math.hypot(actual_impact.x - release_point.x, actual_impact.y - release_point.y),
        is_reference=False,
    )

    vacuum_series = compute_vacuum_trajectory(release_point, vx0, vy0, inputs.gravity_mps2)

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
        is_demo_mode=True,
    )
