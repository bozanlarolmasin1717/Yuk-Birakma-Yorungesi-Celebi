"""7.3 Hedefleme algoritması ve arkadaş adaptörü için doğrulama testleri."""

from dataclasses import dataclass
import math
import numpy as np
import pytest
from src.integration.adapter import build_scenario_from_friend_physics
from src.targeting import (
    ForwardDropResult,
    TargetingConfig,
    estimate_vacuum_lead_distance,
    solve_release_point,
)
from src.ui.theme import LIGHT_PALETTE
from src.visualization.geometry import heading_basis
from src.visualization.schemas import SimulationInputs
from src.visualization.trajectory_3d import build_3d_figure


def test_vacuum_lead_distance_level_and_angled_flight() -> None:
    lead_level = estimate_vacuum_lead_distance(altitude_m=125.0, speed_mps=30.0, gravity_mps2=10.0)
    assert lead_level == pytest.approx(30.0 * math.sqrt(25.0), rel=1e-6)

    lead_climb = estimate_vacuum_lead_distance(
        altitude_m=120.0,
        speed_mps=30.0,
        flight_path_angle_deg=15.0,
        gravity_mps2=9.81,
    )
    lead_dive = estimate_vacuum_lead_distance(
        altitude_m=120.0,
        speed_mps=30.0,
        flight_path_angle_deg=-15.0,
        gravity_mps2=9.81,
    )
    assert lead_climb > lead_dive

    with pytest.raises(ValueError):
        estimate_vacuum_lead_distance(altitude_m=10.0, speed_mps=20.0, target_z_m=10.0)


def test_solver_compensates_crosswind_and_reports_fixed_track_miss() -> None:
    def forward_sim(rx: float, ry: float, rz: float) -> ForwardDropResult:
        t_flight = math.sqrt(2.0 * rz / 9.81) * 1.12
        # İHA doğuya (vx=26), rüzgar kuzeye (wy=+6) sürüklüyor
        imp_x = rx + 21.5 * t_flight
        imp_y = ry + 4.8 * t_flight
        return ForwardDropResult(
            impact_point=(imp_x, imp_y, 0.0),
            flight_time=t_flight,
        )

    solution, _ = solve_release_point(
        simulate_fn=forward_sim,
        target_point=(100.0, 50.0, 0.0),
        release_altitude_m=120.0,
        uav_speed_mps=26.0,
        uav_heading_deg=90.0,
    )

    assert solution.converged is True
    assert solution.predicted_error_m < 1e-3
    assert solution.lead_distance_m > 0.0
    # Rüzgar kuzeye (+y) ittiği için uçak güneyden (sağ taraftan) bırakmalı -> lateral_offset > 0
    assert solution.lateral_offset_m > 10.0
    assert solution.fixed_track_miss_m > 10.0


def test_newton_raphson_converges_on_spatially_varying_wind_field() -> None:
    def spatially_varying_forward(rx: float, ry: float, rz: float) -> ForwardDropResult:
        t_flight = 5.0 + 0.002 * rz
        # Bırakma konumuna bağlı doğrusal olmayan rüzgar alanı
        drift_x = 22.0 * t_flight + 0.14 * rx + 0.03 * ry
        drift_y = 3.5 * t_flight + 0.02 * rx - 0.12 * ry
        return ForwardDropResult(
            impact_point=(rx + drift_x, ry + drift_y, 0.0),
            flight_time=t_flight,
        )

    solution, _ = solve_release_point(
        simulate_fn=spatially_varying_forward,
        target_point=(0.0, 0.0, 0.0),
        release_altitude_m=120.0,
        uav_speed_mps=28.0,
        uav_heading_deg=90.0,
        config=TargetingConfig(tolerance_m=1e-4, max_iterations=25),
    )

    assert solution.converged is True
    assert solution.predicted_error_m < 1e-4
    assert "Newton-Raphson" in solution.method
    assert solution.iterations >= 3


def test_friend_dataclass_contract_integration_via_adapter() -> None:
    # Arkadaşın `koordinatsistemi.py` veri yapılarını birebir taklit eden test sınıfları
    @dataclass
    class MockPayload:
        mass: float
        cd: float
        cross_sectional_area: float

    @dataclass
    class MockEnv:
        g: float = 9.81
        wind_speed: float = 6.0
        wind_director: float = 180.0

    @dataclass
    class MockUavState:
        position: np.ndarray
        speed: float
        heading: float = 90.0
        flight_path_angle: float = 0.0

    @dataclass
    class MockSimResult:
        impact_point: np.ndarray
        flight_time: float
        impact_velocity: np.ndarray
        trajectory: np.ndarray

    def mock_friend_physics(uav: MockUavState, payload: MockPayload, env: MockEnv) -> MockSimResult:
        (hx, hy), _ = heading_basis(uav.heading)
        t_f = math.sqrt(2.0 * float(uav.position[2]) / env.g) * (1.0 + 0.08 * payload.cd)
        ts = np.linspace(0.0, t_f, 35)
        w_rad = math.radians(env.wind_director)
        wx = -env.wind_speed * math.sin(w_rad)
        wy = -env.wind_speed * math.cos(w_rad)

        xs = uav.position[0] + (uav.speed * hx * 0.88 + wx * 0.45) * ts
        ys = uav.position[1] + (uav.speed * hy * 0.88 + wy * 0.45) * ts
        zs = np.maximum(0.0, uav.position[2] * (1.0 - (ts / t_f) ** 2))
        traj = np.column_stack([xs, ys, zs])
        return MockSimResult(
            impact_point=traj[-1].copy(),
            flight_time=float(t_f),
            impact_velocity=np.array([uav.speed * hx * 0.8, uav.speed * hy * 0.8, -32.0]),
            trajectory=traj,
        )

    inputs = SimulationInputs(
        uav_speed_mps=30.0,
        uav_heading_deg=90.0,
        release_altitude_m=120.0,
        payload_mass_kg=6.0,
        payload_area_m2=0.045,
        drag_coefficient=0.82,
        payload_shape="Silindirik Kapsül",
        wind_speed_mps=6.0,
        wind_from_deg=180.0,
        target_x_m=20.0,
        target_y_m=-10.0,
    )

    scenario = build_scenario_from_friend_physics(
        inputs=inputs,
        friend_simulate_fn=mock_friend_physics,
        uav_template=MockUavState(position=np.array([0.0, 0.0, 120.0]), speed=30.0, heading=90.0),
        payload=MockPayload(mass=6.0, cd=0.82, cross_sectional_area=0.045),
        environment=MockEnv(),
    )

    assert scenario.is_demo_mode is False
    assert scenario.release_solution.solver_converged is True
    assert scenario.release_solution.predicted_error_m < 1e-3
    assert len(scenario.actual_trajectory.t) == len(scenario.actual_trajectory.x) == 35
    assert len(scenario.actual_trajectory.speed) == 35
    fig3d = build_3d_figure(scenario, LIGHT_PALETTE)
    assert len(fig3d.data) >= 6
