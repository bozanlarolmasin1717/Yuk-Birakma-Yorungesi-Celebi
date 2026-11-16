"""Çelebi İHA Yük Bırakma Yörüngesi — Streamlit Etkileşimli Simülasyon Arayüzü."""

import streamlit as st
from src.integration.adapter import load_scenario
from src.ui.live_simulator import render_live_simulator
from src.ui.panels import render_export_and_notes, render_header, render_kpis
from src.ui.sidebar import render_sidebar
from src.ui.theme import SPACE_3, build_theme_css, get_palette, svg_icon
from src.visualization.profile_2d import build_side_profile_figure
from src.visualization.topdown_map import build_topdown_figure
from src.visualization.trajectory_3d import build_3d_figure


def main() -> None:
    st.set_page_config(
        page_title="Çelebi · Yük Bırakma Yörüngesi",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "theme_mode" not in st.session_state:
        st.session_state["theme_mode"] = "acik"

    initial_palette = get_palette(st.session_state["theme_mode"])
    theme_mode, inputs = render_sidebar(initial_palette)
    palette = get_palette(theme_mode)

    st.markdown(build_theme_css(palette), unsafe_allow_html=True)

    scenario = load_scenario(inputs)

    render_header(scenario, palette)
    render_kpis(scenario, palette)

    # Birincil etkileşimli sahne: Canlı Yörünge Simülasyonu
    st.markdown(
        f'<div class="celebi-section-head">'
        f'<h2 style="margin:0;">{svg_icon("aircraft", palette.primary, 20)} Canlı Yörünge Simülasyonu</h2>'
        f'<span style="font-size:0.85rem; color:{palette.text_secondary};">Gerçek zamanlı düşüş, rüzgar akışı ve telemetri</span>'
        f"</div>",
        unsafe_allow_html=True,
    )
    render_live_simulator(scenario, palette)

    # Detaylı mühendislik grafikleri ve raporlama (geniş sekmeli düzen)
    st.markdown(
        f'<div class="celebi-section-head" style="margin-top:{SPACE_3}px;">'
        f'<h2 style="margin:0;">{svg_icon("trajectory", palette.primary, 20)} Detaylı Yörünge Grafikleri ve Raporlama</h2>'
        f'<span style="font-size:0.85rem; color:{palette.text_secondary};">Tam SI birimleri (m, m/s, s)</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    tab_3d, tab_side, tab_top, tab_export = st.tabs(
        [
            "3B Uzay Yörüngesi",
            "Yandan Düşüş Profili",
            "Kuşbakışı Harita",
            "Statik Rapor Çıktısı (PNG/SVG)",
        ]
    )

    with tab_3d:
        st.plotly_chart(build_3d_figure(scenario, palette), width="stretch", theme=None)

    with tab_side:
        st.plotly_chart(build_side_profile_figure(scenario, palette), width="stretch", theme=None)

    with tab_top:
        st.plotly_chart(build_topdown_figure(scenario, palette), width="stretch", theme=None)

    with tab_export:
        render_export_and_notes(scenario, palette)


if __name__ == "__main__":
    main()
