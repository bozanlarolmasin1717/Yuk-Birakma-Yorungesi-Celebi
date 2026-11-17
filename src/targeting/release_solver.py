"""7.3 Hedefleme Algoritması: Tersine bırakma noktası ve mesafe çözücüsü.

Verilen herhangi bir ileri balistik simülatörü (`ForwardSimulatorFn`) kara kutu olarak
kullanarak şu iki soruyu çözer:
1. Tam vuruş için yükü hangi `(x_rel, y_rel, z_rel)` noktasından bırakmalıyım?
   (Hem ileri bırakma mesafesi hem yan rüzgar sapma telafisi dahil)
2. İHA yanal düzeltme yapmadan doğrudan hedefin üzerinden uçarsa kaç metre önce
   bırakmalı ve yan rüzgar yüzünden ne kadar sapma oluşur?
"""

import math
from src.targeting.contracts import (
    ForwardDropResult,
    ForwardSimulatorFn,
    ReleaseSolution,
    TargetingConfig,
)
from src.visualization.geometry import heading_basis


def estimate_vacuum_lead_distance(
    altitude_m: float,
    speed_mps: float,
    flight_path_angle_deg: float = 0.0,
    gravity_mps2: float = 9.81,
    target_z_m: float = 0.0,
) -> float:
    """7.1 Vakum referansına göre analitik bırakma mesafesini (m) hesaplar."""
    dz = altitude_m - target_z_m
    if dz <= 0.0:
        raise ValueError("Bırakılma irtifası hedef irtifasından büyük olmalıdır.")
    if gravity_mps2 <= 0.0:
        raise ValueError("Yerçekimi ivmesi sıfırdan büyük olmalıdır.")

    gamma = math.radians(flight_path_angle_deg)
    vz0 = speed_mps * math.sin(gamma)
    vh0 = speed_mps * math.cos(gamma)
    discriminant = max(vz0 * vz0 + 2.0 * gravity_mps2 * dz, 0.0)
    t_vac = (vz0 + math.sqrt(discriminant)) / gravity_mps2
    return vh0 * t_vac


def _error_norm(impact: tuple[float, float, float], target: tuple[float, float, float]) -> float:
    return math.hypot(impact[0] - target[0], impact[1] - target[1])


def _solve_2x2(
    j00: float,
    j01: float,
    j10: float,
    j11: float,
    rhs0: float,
    rhs1: float,
) -> tuple[float, float] | None:
    det = j00 * j11 - j01 * j10
    if abs(det) < 1e-10:
        return None
    dx = (rhs0 * j11 - j01 * rhs1) / det
    dy = (j00 * rhs1 - rhs0 * j10) / det
    return dx, dy


def _solve_fixed_track_release(
    simulate_fn: ForwardSimulatorFn,
    target_point: tuple[float, float, float],
    release_altitude_m: float,
    hx: float,
    hy: float,
    initial_lead_m: float,
    tolerance_m: float,
    max_iterations: int,
) -> tuple[float, float]:
    """İHA'nın doğrudan hedef üzerinden geçen rotada bırakması gereken mesafeyi çözer."""
    tx, ty, _ = target_point

    def eval_along(d: float) -> tuple[float, float]:
        res = simulate_fn(tx - d * hx, ty - d * hy, release_altitude_m)
        ex = res.impact_point[0] - tx
        ey = res.impact_point[1] - ty
        along_err = ex * hx + ey * hy
        total_miss = math.hypot(ex, ey)
        return along_err, total_miss

    d0 = initial_lead_m
    g0, m0 = eval_along(d0)
    if abs(g0) <= tolerance_m:
        return d0, m0

    # Eğim yaklaşık dg/dd = -1 olduğu için ileri aşım (+) varsa d artırılır.
    d1 = d0 + g0
    g1, m1 = eval_along(d1)
    if abs(g1) <= tolerance_m:
        return d1, m1

    for _ in range(max_iterations):
        denom = g1 - g0
        if abs(denom) < 1e-12:
            break
        d_next = d1 - g1 * (d1 - d0) / denom
        g_next, m_next = eval_along(d_next)
        d0, g0 = d1, g1
        d1, g1, m1 = d_next, g_next, m_next
        if abs(g1) <= tolerance_m:
            return d1, m1

    return (d0, m0) if abs(g0) < abs(g1) else (d1, m1)


def solve_release_point(
    simulate_fn: ForwardSimulatorFn,
    target_point: tuple[float, float, float],
    release_altitude_m: float,
    uav_speed_mps: float,
    uav_heading_deg: float,
    flight_path_angle_deg: float = 0.0,
    gravity_mps2: float = 9.81,
    config: TargetingConfig | None = None,
) -> tuple[ReleaseSolution, ForwardDropResult]:
    """Hedefi vurmak için ideal 2B/3B bırakma noktasını sayısal olarak hesaplar.

    İlk tahmin olarak 7.1 vakum çözümünü kullanır, ardından sabit-nokta öteleme ve
    gerektiğinde sonlu fark Jacobianlı sönümlü 2B Newton-Raphson ile yakınsar.
    """
    cfg = config or TargetingConfig()
    tx, ty, tz = target_point
    (hx, hy), (rx_axis, ry_axis) = heading_basis(uav_heading_deg)

    vacuum_lead = estimate_vacuum_lead_distance(
        altitude_m=release_altitude_m,
        speed_mps=uav_speed_mps,
        flight_path_angle_deg=flight_path_angle_deg,
        gravity_mps2=gravity_mps2,
        target_z_m=tz,
    )

    best_x = tx - vacuum_lead * hx
    best_y = ty - vacuum_lead * hy
    best_res = simulate_fn(best_x, best_y, release_altitude_m)
    best_err = _error_norm(best_res.impact_point, target_point)
    iterations = 1

    # 1. Aşama: Sabit-nokta vektör düzeltmesi (yatay homojen rüzgarlarda 1 adımda tam yakınsar)
    if best_err > cfg.tolerance_m:
        cand_x = best_x + (tx - best_res.impact_point[0])
        cand_y = best_y + (ty - best_res.impact_point[1])
        cand_res = simulate_fn(cand_x, cand_y, release_altitude_m)
        cand_err = _error_norm(cand_res.impact_point, target_point)
        iterations += 1
        if cand_err < best_err:
            best_x, best_y, best_res, best_err = cand_x, cand_y, cand_res, cand_err

    method = "7.1 İlk Tahmin + Sabit Nokta"

    # 2. Aşama: Uzaysal değişen rüzgar/arazi varsa sönümlü 2B Newton-Raphson , jacobian ile
    while best_err > cfg.tolerance_m and iterations < cfg.max_iterations:
        method = "Sabit Nokta + 2B Newton-Raphson"
        h = cfg.fd_step_m
        res_dx = simulate_fn(best_x + h, best_y, release_altitude_m)
        res_dy = simulate_fn(best_x, best_y + h, release_altitude_m)
        j00 = (res_dx.impact_point[0] - best_res.impact_point[0]) / h
        j10 = (res_dx.impact_point[1] - best_res.impact_point[1]) / h
        j01 = (res_dy.impact_point[0] - best_res.impact_point[0]) / h
        j11 = (res_dy.impact_point[1] - best_res.impact_point[1]) / h

        rhs0 = tx - best_res.impact_point[0]
        rhs1 = ty - best_res.impact_point[1]
        step = _solve_2x2(j00, j01, j10, j11, rhs0, rhs1)
        if step is None:
            step = (rhs0, rhs1)

        improved = False
        for alpha in (1.0, 0.5, 0.25, 0.1):
            nx = best_x + alpha * step[0]
            ny = best_y + alpha * step[1]
            nres = simulate_fn(nx, ny, release_altitude_m)
            nerr = _error_norm(nres.impact_point, target_point)
            iterations += 1
            if nerr < best_err:
                best_x, best_y, best_res, best_err = nx, ny, nres, nerr
                improved = True
                break

        if not improved:
            break

    lead_distance_m = (tx - best_x) * hx + (ty - best_y) * hy
    lateral_offset_m = (best_x - tx) * rx_axis + (best_y - ty) * ry_axis

    if abs(lateral_offset_m) <= 1e-4:
        fixed_track_lead_m = lead_distance_m
        fixed_track_miss_m = best_err
    else:
        fixed_track_lead_m, fixed_track_miss_m = _solve_fixed_track_release(
            simulate_fn=simulate_fn,
            target_point=target_point,
            release_altitude_m=release_altitude_m,
            hx=hx,
            hy=hy,
            initial_lead_m=lead_distance_m,
            tolerance_m=cfg.tolerance_m,
            max_iterations=cfg.max_iterations,
        )

    solution = ReleaseSolution(
        release_point=(best_x, best_y, release_altitude_m),
        target_point=target_point,
        lead_distance_m=lead_distance_m,
        lateral_offset_m=lateral_offset_m,
        vacuum_lead_distance_m=vacuum_lead,
        fixed_track_lead_m=fixed_track_lead_m,
        fixed_track_miss_m=fixed_track_miss_m,
        time_to_impact_s=best_res.flight_time,
        predicted_error_m=best_err,
        iterations=iterations,
        converged=best_err <= cfg.tolerance_m,
        method=method,
    )
    return solution, best_res
