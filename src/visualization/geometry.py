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
