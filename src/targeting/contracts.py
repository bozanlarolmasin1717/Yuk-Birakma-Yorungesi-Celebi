"""7.3 Hedefleme algoritması veri sözleşmeleri ve ileri simülatör adaptörleri."""

from copy import copy
from dataclasses import dataclass, is_dataclass, replace
from typing import Any, Callable
import numpy as np


@dataclass(frozen=True)
class ForwardDropResult:
    """7.3 çözücüsünün ileri fizik motorundan beklediği standart çıktı."""

    impact_point: tuple[float, float, float]
    flight_time: float
    x: tuple[float, ...] = ()
    y: tuple[float, ...] = ()
    z: tuple[float, ...] = ()
    t: tuple[float, ...] = ()
    speed: tuple[float, ...] = ()
    impact_speed_mps: float | None = None


ForwardSimulatorFn = Callable[[float, float, float], ForwardDropResult]


@dataclass(frozen=True)
class TargetingConfig:
    """7.3 sayısal kök bulma çözücüsü için yakınsama ayarları."""

    tolerance_m: float = 1e-3
    max_iterations: int = 25
    fd_step_m: float = 0.5


@dataclass(frozen=True)
class ReleaseSolution:
    """7.3 Tersine hesaplama sonucu: Bırakma noktası, mesafeler ve yakınsama bilgisi."""

    release_point: tuple[float, float, float]
    target_point: tuple[float, float, float]
    lead_distance_m: float
    lateral_offset_m: float
    vacuum_lead_distance_m: float
    fixed_track_lead_m: float
    fixed_track_miss_m: float
    time_to_impact_s: float
    predicted_error_m: float
    iterations: int
    converged: bool
    method: str


def adapt_friend_simulator(
    simulate_fn: Callable[[Any, Any, Any], Any],
    uav_template: Any,
    payload: Any,
    environment: Any,
) -> ForwardSimulatorFn:
    """Arkadaşınızın `(UavState, payloadParameters, environmentParameters) -> simulationResult`
    imzalı ileri fizik fonksiyonunu 7.3 çözücüsünün beklediği `ForwardSimulatorFn` tipine sarar.
    """

    def _run_forward(rx: float, ry: float, rz: float) -> ForwardDropResult:
        pos = np.array([rx, ry, rz], dtype=float)
        if is_dataclass(uav_template):
            uav_state = replace(uav_template, position=pos)
        else:
            uav_state = copy(uav_template)
            uav_state.position = pos

        result = simulate_fn(uav_state, payload, environment)
        imp = result.impact_point
        imp_vel = getattr(result, "impact_velocity", None)
        impact_speed = float(np.linalg.norm(imp_vel)) if imp_vel is not None else None
        traj = getattr(result, "trajectory", None)

        xs: tuple[float, ...] = ()
        ys: tuple[float, ...] = ()
        zs: tuple[float, ...] = ()
        if traj is not None and len(traj) > 0:
            arr = np.asarray(traj, dtype=float)
            if arr.ndim == 2 and arr.shape[1] >= 3:
                xs = tuple(float(v) for v in arr[:, 0])
                ys = tuple(float(v) for v in arr[:, 1])
                zs = tuple(float(v) for v in arr[:, 2])

        return ForwardDropResult(
            impact_point=(float(imp[0]), float(imp[1]), float(imp[2])),
            flight_time=float(result.flight_time),
            x=xs,
            y=ys,
            z=zs,
            impact_speed_mps=impact_speed,
        )

    return _run_forward
