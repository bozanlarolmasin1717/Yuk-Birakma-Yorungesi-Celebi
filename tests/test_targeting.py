"""7.3 Hedefleme algoritması ve arkadaş adaptörü için doğrulama testleri."""

from dataclasses import dataclass
import math
import numpy as np
import pytest
from balistik_motor import compute_vacum_ballistics, simulate_trajectory
from koordinatsistemi import UavState, environmentParameters, payloadParameters
from src.integration.adapter import (
    build_scenario_from_friend_physics,
    load_71_scenario,
    load_72_scenario,
    load_scenario,
)
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


def test_real_friend_engine_71_72_and_73_end_to_end() -> None:
    # 7.1 ve 7.2 sıfır sürtünme + sıfır rüzgar tutarlılık testi
    uav = UavState(position=np.array([0.0, 0.0, 120.0]), speed=28.0, heading=60.0, flight_path_angle=5.0)
    env = environmentParameters(g=9.81, use_is=True, wind_speed=0.0)
    payload_zero_cd = payloadParameters(mass=5.0, cd=0.0, cross_sectional_area=0.04)

    vac_imp, vac_t = compute_vacum_ballistics(uav, env)
    rk4_zero = simulate_trajectory(uav, payload_zero_cd, env, dt=0.01)
    assert np.linalg.norm(rk4_zero.impact_point - vac_imp) < 1e-4
    assert rk4_zero.flight_time == pytest.approx(vac_t, abs=1e-4)

    # ISA 0.0065 düzeltmesi kontrolü (1000 m'de standart ~1.111 kg/m³)
    assert env.air_density(1000.0) == pytest.approx(1.1116, abs=0.002)

    inputs = SimulationInputs(
        uav_speed_mps=28.0,
        uav_heading_deg=60.0,
        release_altitude_m=120.0,
        payload_mass_kg=6.0,
        payload_area_m2=0.045,
        drag_coefficient=1.05,
        payload_shape="Kübik Yardım Paketi",
        wind_speed_mps=8.0,
        wind_from_deg=200.0,
        target_x_m=30.0,
        target_y_m=-15.0,
        flight_path_angle_deg=5.0,
        use_isa=True,
        wind_shear_coeff=0.002,
    )

    s71 = load_71_scenario(inputs)
    s72 = load_72_scenario(inputs)
    s73 = load_scenario(inputs)

    assert s71.scenario_mode == "7.1" and s71.is_demo_mode is False
    assert s72.scenario_mode == "7.2" and s72.drift_from_vacuum_m > 5.0
    assert s73.scenario_mode == "7.3" and s73.is_demo_mode is False
    assert s73.release_solution.solver_converged is True
    assert s73.release_solution.predicted_error_m < 1e-3

    # Gerçek çarpma hızı (||impact_velocity||) hem 7.2 hem 7.3 serisinde birebir korunmalı
    uav_rel = UavState(
        position=np.array(
            [
                s73.release_solution.release_point.x,
                s73.release_solution.release_point.y,
                s73.release_solution.release_point.z,
            ]
        ),
        speed=inputs.uav_speed_mps,
        heading=inputs.uav_heading_deg,
        flight_path_angle=inputs.flight_path_angle_deg,
    )
    env_full = environmentParameters(
        g=inputs.gravity_mps2,
        rho_sea_level=inputs.air_density_kgm3,
        use_is=inputs.use_isa,
        wind_speed=inputs.wind_speed_mps,
        wind_director=inputs.wind_from_deg,
        wind_shear_coeff=inputs.wind_shear_coeff,
    )
    payload_full = payloadParameters(
        mass=inputs.payload_mass_kg,
        cd=inputs.drag_coefficient,
        cross_sectional_area=inputs.payload_area_m2,
    )
    rk4_72 = simulate_trajectory(uav, payload_full, env_full, dt=0.01)
    rk4_73 = simulate_trajectory(uav_rel, payload_full, env_full, dt=0.01)
    assert s72.actual_trajectory.speed[-1] == pytest.approx(float(np.linalg.norm(rk4_72.impact_velocity)), abs=1e-4)
    assert s73.actual_trajectory.speed[-1] == pytest.approx(float(np.linalg.norm(rk4_73.impact_velocity)), abs=1e-4)
    assert s73.wind_vector_mps == pytest.approx(
        (float(env_full.wind_vector(inputs.release_altitude_m)[0]), float(env_full.wind_vector(inputs.release_altitude_m)[1])),
        abs=1e-6,
    )
