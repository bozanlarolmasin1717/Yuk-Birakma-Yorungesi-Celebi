"""Plotly ve Matplotlib görünümleri arasında paylaşılan geometri yardımcıları."""

import math
from src.visualization.schemas import Point3D, TrajectorySeries


def heading_basis(heading_deg: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Havacılık azimutundan (0°=Kuzey, 90°=Doğu) ileri ve sağ birim vektörleri döner."""
    rad = math.radians(heading_deg)
    forward = (math.sin(rad), math.cos(rad))
    right = (math.cos(rad), -math.sin(rad))
    return forward, right


def wind_from_to_vector(wind_speed_mps: float, wind_from_deg: float) -> tuple[float, float]:
    """Meteorolojik yönelimden (rüzgarın estiği açı) rüzgar itiş vektörünü (wx, wy) döner."""
    to_rad = math.radians((wind_from_deg + 180.0) % 360.0)
    return (
        wind_speed_mps * math.sin(to_rad),
        wind_speed_mps * math.cos(to_rad),
    )


def project_along_heading(
    xs: tuple[float, ...],
    ys: tuple[float, ...],
    origin: Point3D,
    heading_deg: float,
) -> tuple[float, ...]:
    """(x, y) noktalarını bırakma noktası merkezli İHA uçuş ekseni boyunca metreye izdüşürür."""
    (hx, hy), _ = heading_basis(heading_deg)
    return tuple((x - origin.x) * hx + (y - origin.y) * hy for x, y in zip(xs, ys))


def circle_points(center_x: float, center_y: float, radius_m: float, steps: int = 64) -> tuple[list[float], list[float]]:
    """Üstten görünüm hedef halkaları için kapalı çember koordinatları üretir."""
    xs: list[float] = []
    ys: list[float] = []
    for i in range(steps + 1):
        angle = 2.0 * math.pi * i / steps
        xs.append(center_x + radius_m * math.cos(angle))
        ys.append(center_y + radius_m * math.sin(angle))
    return xs, ys


def compute_axis_bounds(
    vacuum: TrajectorySeries,
    actual: TrajectorySeries,
    target: Point3D,
    padding_ratio: float = 0.12,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Üstten görünüm haritası için dengeli X ve Y sınırları hesaplar."""
    all_x = list(vacuum.x) + list(actual.x) + [target.x]
    all_y = list(vacuum.y) + list(actual.y) + [target.y]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    span = max(max_x - min_x, max_y - min_y, 20.0)
    pad = span * padding_ratio
    cx = 0.5 * (min_x + max_x)
    cy = 0.5 * (min_y + max_y)
    half = 0.5 * span + pad
    return (cx - half, cx + half), (cy - half, cy + half)


def format_lead_distance(lead_distance_m: float) -> str:
    """7.3 bırakma mesafesini işaretine göre okunur Türkçe metne çevirir."""
    if lead_distance_m >= 0.0:
        return f"{lead_distance_m:.1f} m önce"
    return f"{abs(lead_distance_m):.1f} m sonra (ters rüzgar)"


def compute_vacuum_trajectory(
    release: Point3D,
    vx0: float,
    vy0: float,
    gravity: float,
    vz0: float = 0.0,
    samples: int = 60,
) -> TrajectorySeries:
    """7.1 referans vakum (hava direncisiz) parabolik yörüngesini üretir."""
    dz = max(release.z, 0.1)
    g = max(gravity, 0.1)
    discriminant = max(vz0 * vz0 + 2.0 * g * dz, 0.0)
    t_flight = (vz0 + math.sqrt(discriminant)) / g

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    ts: list[float] = []
    speeds: list[float] = []

    for i in range(samples + 1):
        t = t_flight * i / samples
        x = release.x + vx0 * t
        y = release.y + vy0 * t
        z = max(0.0, release.z + vz0 * t - 0.5 * g * t * t)
        vz = vz0 - g * t
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


def build_uav_track(
    release_point: Point3D,
    heading_deg: float,
    lead_distance_m: float,
    vacuum_range_m: float,
) -> tuple[Point3D, ...]:
    """Bırakma, hedef ve vakum düşüşü boyunca İHA yaklaşma/ayrılma hattını üretir."""
    (hx, hy), _ = heading_basis(heading_deg)
    min_s = min(0.0, lead_distance_m)
    max_s = max(0.0, lead_distance_m, vacuum_range_m)
    return (
        Point3D(
            release_point.x + (min_s - 40.0) * hx,
            release_point.y + (min_s - 40.0) * hy,
            release_point.z,
        ),
        release_point,
        Point3D(
            release_point.x + (max_s + 40.0) * hx,
            release_point.y + (max_s + 40.0) * hy,
            release_point.z,
        ),
    )
