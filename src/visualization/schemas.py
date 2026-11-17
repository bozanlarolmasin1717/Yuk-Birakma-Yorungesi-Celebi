"""Görselleştirme ve arayüz katmanının kullandığı sade veri sözleşmeleri.

Bu modül arkadaşınızın geliştirdiği koordinat/fizik sınıflarından bağımsızdır;
çizim ve arayüz katmanı yalnızca burada tanımlanan SI birimli (m, m/s, kg, s, °)
veri yapılarını tüketir.
"""

from dataclasses import dataclass


PAYLOAD_SHAPE_CD_PRESETS: dict[str, float] = {
    "Özel Değer": 0.47,
    "Küre (Referans)": 0.47,
    "Aerodinamik Damla Gövde": 0.15,
    "Silindirik Kapsül": 0.82,
    "Kübik Yardım Paketi": 1.05,
    "Paraşütlü Yardım Yükü": 1.45,
}


@dataclass(frozen=True)
class Point3D:
    """ENU koordinat sisteminde 3B konum (x: Doğu, y: Kuzey, z: İrtifa [m])."""

    x: float
    y: float
    z: float


@dataclass(frozen=True)
class SimulationInputs:
    """Kullanıcı arayüzünden alınan tam SI birimli senaryo parametreleri."""

    uav_speed_mps: float
    uav_heading_deg: float
    release_altitude_m: float
    payload_mass_kg: float
    payload_area_m2: float
    drag_coefficient: float
    payload_shape: str
    wind_speed_mps: float
    wind_from_deg: float
    target_x_m: float
    target_y_m: float
    gravity_mps2: float = 9.81
    air_density_kgm3: float = 1.225
    flight_path_angle_deg: float = 0.0
    use_isa: bool = False
    wind_shear_coeff: float = 0.0


@dataclass(frozen=True)
class TrajectorySeries:
    """Tek bir düşüş yörüngesinin zaman serisi ve özet sonuçları."""

    label: str
    x: tuple[float, ...]
    y: tuple[float, ...]
    z: tuple[float, ...]
    t: tuple[float, ...]
    speed: tuple[float, ...]
    impact_point: Point3D
    flight_time: float
    horizontal_range: float
    is_reference: bool = False


@dataclass(frozen=True)
class ReleaseSolutionView:
    """7.3 Hedefleme algoritmasının arayüzde gösterilecek bırakma çözümü."""

    release_point: Point3D
    target_point: Point3D
    lead_distance_m: float
    lateral_offset_m: float
    predicted_error_m: float
    vacuum_lead_distance_m: float = 0.0
    fixed_track_lead_m: float = 0.0
    fixed_track_miss_m: float = 0.0
    solver_iterations: int = 1
    solver_converged: bool = True
    solver_method: str = ""


@dataclass(frozen=True)
class DropScenarioView:
    """Tüm görselleştirme ve özet panellerini besleyen tam senaryo çıktısı."""

    inputs: SimulationInputs
    vacuum_trajectory: TrajectorySeries
    actual_trajectory: TrajectorySeries
    uav_track: tuple[Point3D, ...]
    wind_vector_mps: tuple[float, float]
    release_solution: ReleaseSolutionView
    drift_from_vacuum_m: float
    is_demo_mode: bool = True
    scenario_mode: str = "7.3"
