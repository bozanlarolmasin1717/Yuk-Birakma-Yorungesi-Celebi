"""Görselleştirme sözleşmesi, demo sağlayıcı ve Plotly/Matplotlib çıktıları için birim testleri."""

from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.integration.adapter import load_scenario
from src.ui.live_simulator import build_simulator_html
from src.ui.theme import DARK_PALETTE, LIGHT_PALETTE, build_theme_css
from src.visualization.export_static import export_summary_figure_bytes
from src.visualization.geometry import format_lead_distance
from src.visualization.profile_2d import build_side_profile_figure
from src.visualization.schemas import SimulationInputs
from src.visualization.topdown_map import build_topdown_figure
from src.visualization.trajectory_3d import build_3d_figure


def _sample_inputs(wind_speed: float = 8.0) -> SimulationInputs:
    return SimulationInputs(
        uav_speed_mps=30.0,
        uav_heading_deg=90.0,
        release_altitude_m=120.0,
        payload_mass_kg=6.0,
        payload_area_m2=0.045,
        drag_coefficient=1.05,
        payload_shape="Kübik Yardım Paketi",
        wind_speed_mps=wind_speed,
        wind_from_deg=210.0,
        target_x_m=0.0,
        target_y_m=0.0,
    )


def test_demo_scenario_hits_target_within_tolerance() -> None:
    scenario = load_scenario(_sample_inputs())
    assert scenario.is_demo_mode is True
    assert scenario.release_solution.predicted_error_m < 0.05
    assert scenario.release_solution.lead_distance_m > 0.0
    assert scenario.actual_trajectory.z[-1] == 0.0
    assert scenario.vacuum_trajectory.z[-1] == 0.0


def test_zero_wind_and_low_drag_reduces_drift() -> None:
    calm_low_drag = SimulationInputs(
        uav_speed_mps=25.0,
        uav_heading_deg=0.0,
        release_altitude_m=100.0,
        payload_mass_kg=20.0,
        payload_area_m2=0.01,
        drag_coefficient=0.05,
        payload_shape="Özel Değer",
        wind_speed_mps=0.0,
        wind_from_deg=0.0,
        target_x_m=0.0,
        target_y_m=0.0,
    )
    calm = load_scenario(calm_low_drag)
    windy = load_scenario(_sample_inputs(wind_speed=12.0))
    assert calm.drift_from_vacuum_m < windy.drift_from_vacuum_m


def test_plotly_figures_generate_for_both_themes() -> None:
    scenario = load_scenario(_sample_inputs())
    for palette in (LIGHT_PALETTE, DARK_PALETTE):
        fig3d = build_3d_figure(scenario, palette)
        fig2d = build_side_profile_figure(scenario, palette)
        fig_top = build_topdown_figure(scenario, palette)
        assert len(fig3d.data) >= 6
        assert len(fig2d.data) >= 3
        assert len(fig_top.data) >= 5

        fig2d_ref = build_side_profile_figure(scenario, palette, show_vacuum_reference=True)
        assert len(fig2d_ref.data) >= 4


def test_static_matplotlib_export_produces_png_and_svg() -> None:
    scenario = load_scenario(_sample_inputs())
    png_bytes = export_summary_figure_bytes(scenario, LIGHT_PALETTE, fmt="png")
    svg_bytes = export_summary_figure_bytes(scenario, DARK_PALETTE, fmt="svg")
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
    assert b"<svg" in svg_bytes


def test_streamlit_app_renders_light_and_dark_themes() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()
    assert len(at.exception) == 0
    assert len(at.markdown) > 0

    at.radio(key="theme_mode").set_value("koyu").run()
    assert len(at.exception) == 0


def test_strong_headwind_negative_lead_distance_formatting() -> None:
    headwind_inputs = SimulationInputs(
        uav_speed_mps=8.0,
        uav_heading_deg=90.0,
        release_altitude_m=120.0,
        payload_mass_kg=6.0,
        payload_area_m2=0.045,
        drag_coefficient=1.45,
        payload_shape="Paraşütlü Yardım Yükü",
        wind_speed_mps=25.0,
        wind_from_deg=90.0,
        target_x_m=0.0,
        target_y_m=0.0,
    )
    scenario = load_scenario(headwind_inputs)
    lead_m = scenario.release_solution.lead_distance_m
    assert lead_m < 0.0
    assert "geç bırak (ters rüzgar)" in format_lead_distance(lead_m)
    assert format_lead_distance(42.34) == "42.3 m önce bırak"

    track_xs = [p.x for p in scenario.uav_track]
    assert min(track_xs) < scenario.release_solution.target_point.x
    assert max(track_xs) > scenario.vacuum_trajectory.impact_point.x

    fig_side = build_side_profile_figure(scenario, LIGHT_PALETTE)
    assert any("geç bırak (ters rüzgar)" in str(ann.text) for ann in fig_side.layout.annotations)


def test_decluttered_3d_dark_css_and_live_simulator() -> None:
    scenario = load_scenario(_sample_inputs())
    fig3d = build_3d_figure(scenario, DARK_PALETTE)
    assert fig3d.layout.scene.aspectmode == "manual"
    assert len([tr for tr in fig3d.data if tr.showlegend is not False]) == 2

    fig3d_ref = build_3d_figure(scenario, DARK_PALETTE, show_vacuum_reference=True)
    assert len([tr for tr in fig3d_ref.data if tr.showlegend is not False]) == 3

    dark_css = build_theme_css(DARK_PALETTE)
    assert "stNumberInputContainer" in dark_css
    assert "stSelectbox" in dark_css
    assert 'div[data-baseweb="popover"]' in dark_css

    html_doc = build_simulator_html(scenario, DARK_PALETTE)
    assert "sideCanvas" in html_doc
    assert "topCanvas" in html_doc
    assert '"showVacuum": false' in html_doc
    assert '"tFlight"' in html_doc


def test_direction_dial_manual_inputs_sync_state() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()
    assert at.session_state["uav_heading_dial_deg"] == 90
    assert at.session_state["wind_from_dial_deg"] == 210

    at.number_input(key="uav_heading_dial_num").set_value(180).run()
    assert len(at.exception) == 0
    assert at.session_state["uav_heading_dial_deg"] == 180

    at.number_input(key="wind_from_dial_num").set_value(45).run()
    assert len(at.exception) == 0
    assert at.session_state["wind_from_dial_deg"] == 45


def test_module_selector_renders_71_72_and_73_independently() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(app_path, default_timeout=15)
    at.run()
    assert at.session_state["active_module"] == "7.3 · Hedefleme Algoritması"

    at.radio(key="active_module").set_value("7.1 · Balistik Hareket Denklemleri").run()
    assert len(at.exception) == 0
    assert any("7.1 Balistik Hareket Denklemleri Henüz Bağlanmadı" in m.value for m in at.markdown)

    at.radio(key="active_module").set_value("7.2 · Hava Sürtünmesi ve Rüzgar").run()
    assert len(at.exception) == 0
    assert any("7.2 Hava Sürtünmesi ve Rüzgar Modeli Henüz Bağlanmadı" in m.value for m in at.markdown)


