"""Gerçek fizik motoru bağlanana kadar arayüzü besleyen geçici demo veri üretici.

Bu modül yalnızca sürgülerin canlı tepki vermesi için yaklaşık bir yörünge ve
bırakma noktası üretir. Arkadaşınızın koordinat/fizik motoru tamamlandığında
`src/integration/adapter.py` üzerinden gerçek hesaplamaya geçilecektir.
"""

import math
from src.visualization.geometry import heading_basis, wind_from_to_vector
from src.visualization.schemas import (
    DropScenarioView,
    Point3D,
    ReleaseSolutionView,
    SimulationInputs,
    TrajectorySeries,
)


def _compute_vacuum_from(
    release: Point3D,
    vx0: float,
    vy0: float,
    gravity: float,
    samples: int = 60,
) -> TrajectorySeries:
    """Referans vakum (hava direncisiz) parabolik yörüngesini üretir."""
    t_flight = math.sqrt(2.0 * max(release.z, 0.1) / max(gravity, 0.1))
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    ts: list[float] = []
    speeds: list[float] = []

    for i in range(samples + 1):
        t = t_flight * i / samples
        x = release.x + vx0 * t
        y = release.y + vy0 * t
        z = max(0.0, release.z - 0.5 * gravity * t * t)
        vz = -gravity * t
        xs.append(x)
        ys.append(y)
        zs.append(z)
        ts.append(t)
        speeds.append(math.sqrt(vx0 * vx0 + vy0 * vy0 + vz * vz))

    impact = Point3D(xs[-1], ys[-1], 0.0)
    horiz_range = math.hypot(impact.x - release.x, impact.y - release.y)
    return TrajectorySeries(
        label="Vakum Referansı (7.1)",
        x=tuple(xs),
        y=tuple(ys),
        z=tuple(zs),
        t=tuple(ts),
        speed=tuple(speeds),
        impact_point=impact,
        flight_time=t_flight,
        horizontal_range=horiz_range,
        is_reference=True,
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
    """Kullanıcı girdilerine tepki veren geçici demo senaryo verisi üretir."""
    (hx, hy), (rx_axis, ry_axis) = heading_basis(inputs.uav_heading_deg)
    vx0 = inputs.uav_speed_mps * hx
    vy0 = inputs.uav_speed_mps * hy
    wx, wy = wind_from_to_vector(inputs.wind_speed_mps, inputs.wind_from_deg)

    rel_xs, rel_ys, zs, ts, speeds = _integrate_demo_drag(inputs, vx0, vy0, wx, wy)
    dx_total = rel_xs[-1]
    dy_total = rel_ys[-1]

    release_point = Point3D(
        x=inputs.target_x_m - dx_total,
        y=inputs.target_y_m - dy_total,
        z=inputs.release_altitude_m,
    )
    target_point = Point3D(inputs.target_x_m, inputs.target_y_m, 0.0)

    actual_x = tuple(release_point.x + dx for dx in rel_xs)
    actual_y = tuple(release_point.y + dy for dy in rel_ys)
    actual_impact = Point3D(actual_x[-1], actual_y[-1], 0.0)

    actual_series = TrajectorySeries(
        label="Hava Sürtünmeli + Rüzgarlı (Demo)",
        x=actual_x,
        y=actual_y,
        z=tuple(zs),
        t=tuple(ts),
        speed=tuple(speeds),
        impact_point=actual_impact,
        flight_time=ts[-1],
        horizontal_range=math.hypot(actual_impact.x - release_point.x, actual_impact.y - release_point.y),
        is_reference=False,
    )

    vacuum_series = _compute_vacuum_from(release_point, vx0, vy0, inputs.gravity_mps2)

    lead_distance_m = (target_point.x - release_point.x) * hx + (target_point.y - release_point.y) * hy
    lateral_offset_m = (release_point.x - target_point.x) * rx_axis + (release_point.y - target_point.y) * ry_axis
    predicted_error_m = math.hypot(actual_impact.x - target_point.x, actual_impact.y - target_point.y)
    drift_from_vacuum_m = math.hypot(
        actual_impact.x - vacuum_series.impact_point.x,
        actual_impact.y - vacuum_series.impact_point.y,
    )

    min_s = min(0.0, lead_distance_m)
    max_s = max(0.0, lead_distance_m, vacuum_series.horizontal_range)
    uav_track = (
        Point3D(
            release_point.x + (min_s - 40.0) * hx,
            release_point.y + (min_s - 40.0) * hy,
            inputs.release_altitude_m,
        ),
        release_point,
        Point3D(
            release_point.x + (max_s + 40.0) * hx,
            release_point.y + (max_s + 40.0) * hy,
            inputs.release_altitude_m,
        ),
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
            lead_distance_m=lead_distance_m,
            lateral_offset_m=lateral_offset_m,
            predicted_error_m=predicted_error_m,
        ),
        drift_from_vacuum_m=drift_from_vacuum_m,
        is_demo_mode=True,
    )
