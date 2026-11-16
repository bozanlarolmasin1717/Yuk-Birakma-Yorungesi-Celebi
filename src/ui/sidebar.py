"""Kenar çubuğu (sidebar) kontrol paneli: Tema seçimi ve SI biriminde uçuş girdileri."""

import streamlit as st
from src.ui.theme import SPACE_2, ThemePalette, svg_icon
from src.visualization.geometry import wind_from_to_vector
from src.visualization.schemas import PAYLOAD_SHAPE_CD_PRESETS, SimulationInputs


def render_sidebar(palette: ThemePalette) -> tuple[str, SimulationInputs]:
    """Tema anahtarını ve tüm fiziksel senaryo girdilerini kenar çubuğunda sunar."""
    with st.sidebar:
        st.markdown(
            f'<div style="margin-bottom:{SPACE_2}px;">'
            f'<div class="celebi-kicker">Çelebi Simülasyon Paneli</div>'
            f'<h2 style="margin:0;">Senaryo Girdileri</h2>'
            f"</div>",
            unsafe_allow_html=True,
        )

        # Açık / Koyu tema seçimi
        theme_choice = st.radio(
            "Görünüm Teması",
            options=["acik", "koyu"],
            format_func=lambda key: "Açık Teknik Tema" if key == "acik" else "Koyu Kokpit Teması",
            horizontal=True,
            key="theme_mode",
        )

        st.divider()
        st.markdown(
            f'<div class="celebi-metric-label">{svg_icon("aircraft", "var(--primary)", 16)} '
            f"<span>İHA Uçuş Durumu</span></div>",
            unsafe_allow_html=True,
        )
        uav_speed_mps = st.slider(
            "İHA Yer Hızı (m/s)",
            min_value=8.0,
            max_value=80.0,
            value=28.0,
            step=1.0,
        )
        release_altitude_m = st.slider(
            "Bırakılma İrtifası (m)",
            min_value=15.0,
            max_value=400.0,
            value=120.0,
            step=5.0,
        )
        uav_heading_deg = st.slider(
            "Uçuş İstikameti (° — 0° Kuzey, 90° Doğu)",
            min_value=0,
            max_value=359,
            value=90,
            step=5,
        )

        st.divider()
        st.markdown(
            f'<div class="celebi-metric-label">{svg_icon("trajectory", "var(--primary)", 16)} '
            f"<span>Faydalı Yük ve Sürtünme (Cd)</span></div>",
            unsafe_allow_html=True,
        )
        payload_shape = st.selectbox(
            "Yük Geometrisi Profili",
            options=list(PAYLOAD_SHAPE_CD_PRESETS.keys()),
            index=4,
        )
        preset_cd = PAYLOAD_SHAPE_CD_PRESETS[payload_shape]
        if payload_shape == "Özel Değer":
            drag_coefficient = st.slider(
                "Sürtünme Katsayısı (Cd)",
                min_value=0.05,
                max_value=2.00,
                value=0.47,
                step=0.01,
            )
        else:
            drag_coefficient = preset_cd
            st.caption(f"Seçili profil sürtünme katsayısı: Cd = {drag_coefficient:.2f}")

        col_m, col_a = st.columns(2)
        with col_m:
            payload_mass_kg = st.number_input(
                "Kütle (kg)",
                min_value=0.5,
                max_value=250.0,
                value=6.0,
                step=0.5,
            )
        with col_a:
            payload_area_m2 = st.number_input(
                "Kesit Alanı (m²)",
                min_value=0.005,
                max_value=2.000,
                value=0.045,
                step=0.005,
                format="%.3f",
            )

        st.divider()
        st.markdown(
            f'<div class="celebi-metric-label">{svg_icon("wind", "var(--primary)", 16)} '
            f"<span>Rüzgar Modeli</span></div>",
            unsafe_allow_html=True,
        )
        wind_speed_mps = st.slider(
            "Rüzgar Şiddeti (m/s)",
            min_value=0.0,
            max_value=25.0,
            value=7.5,
            step=0.5,
        )
        wind_from_deg = st.slider(
            "Rüzgarın Estiği Yön (° — 0° Kuzeyden)",
            min_value=0,
            max_value=359,
            value=210,
            step=5,
        )
        wx, wy = wind_from_to_vector(wind_speed_mps, float(wind_from_deg))
        st.caption(f"İtiş vektörü: Doğu {wx:+.1f} m/s, Kuzey {wy:+.1f} m/s")

        st.divider()
        st.markdown(
            f'<div class="celebi-metric-label">{svg_icon("target", "var(--primary)", 16)} '
            f"<span>Hedef Koordinatı (ENU)</span></div>",
            unsafe_allow_html=True,
        )
        col_tx, col_ty = st.columns(2)
        with col_tx:
            target_x_m = st.number_input("Hedef Doğu X (m)", value=0.0, step=10.0)
        with col_ty:
            target_y_m = st.number_input("Hedef Kuzey Y (m)", value=0.0, step=10.0)

    inputs = SimulationInputs(
        uav_speed_mps=float(uav_speed_mps),
        uav_heading_deg=float(uav_heading_deg),
        release_altitude_m=float(release_altitude_m),
        payload_mass_kg=float(payload_mass_kg),
        payload_area_m2=float(payload_area_m2),
        drag_coefficient=float(drag_coefficient),
        payload_shape=payload_shape,
        wind_speed_mps=float(wind_speed_mps),
        wind_from_deg=float(wind_from_deg),
        target_x_m=float(target_x_m),
        target_y_m=float(target_y_m),
    )
    return theme_choice, inputs
