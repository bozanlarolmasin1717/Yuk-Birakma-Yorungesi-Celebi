"""Arkadaşınızın fizik/koordinat motorunu görselleştirme katmanına bağlayan adaptör.

Arkadaşınızın dosyaları projeye eklendiğinde yalnızca bu modül içindeki
`load_scenario` fonksiyonu güncellenir; arayüz ve grafik kodları değişmez.
"""

from typing import Callable, Optional
from src.integration.demo_provider import build_demo_scenario
from src.visualization.schemas import DropScenarioView, SimulationInputs

ScenarioSolver = Callable[[SimulationInputs], DropScenarioView]


def load_scenario(
    inputs: SimulationInputs,
    solver: Optional[ScenarioSolver] = None,
) -> DropScenarioView:
    """Harici bir çözücü verilmişse onu, verilmemişse geçici demo sağlayıcıyı çalıştırır."""
    if solver is not None:
        return solver(inputs)
    return build_demo_scenario(inputs)
