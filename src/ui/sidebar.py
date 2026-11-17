"""Kenar çubuğu (sidebar) kontrol paneli: Tema seçimi, 2B yön kadranları ve SI uçuş girdileri."""

import streamlit as st
from src.ui.direction_dial import compass_direction_name, render_direction_dial
from src.ui.theme import SPACE_2, ThemePalette, get_palette, svg_icon
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

        theme_choice = st.radio(
            "Görünüm Teması",
            options=["acik", "koyu"],
            format_func=lambda key: "Açık Teknik Tema" if key == "acik" else "Koyu Kokpit Teması",
            horizontal=True,
            key="theme_mode",
        )
        active_palette = get_palette(theme_choice)

        st.divider()
        st.markdown(
            f'<div class="celebi-metric-label">{svg_icon("aircraft", "var(--primary)", 16)} '
            f"<span>İHA Uçuş Durumu</span></div>",
            unsafe_allow_html=True,
        )
        uav_speed_mps = st.slider(
            "İHA Hızı (m/s)",
            min_value=8.0,
            max_value=80.0,
            value=28.0,
            step=1.0,
        )
        release_altitude_m = st.slider(
            "Bırakma Yüksekliği (m)",
            min_value=15.0,
            max_value=400.0,
            value=120.0,
            step=5.0,
        )
        uav_heading_deg = render_direction_dial(
            key="uav_heading_dial",
            label="Uçuş İstikameti",
            mode="uav",
            default_angle=90,
            palette=active_palette,
            subtitle="Sürükleyerek (5° adım) veya alttan yazarak belirleyin",
        )

        st.divider()
        st.markdown(
            f'<div class="celebi-metric-label">{svg_icon("trajectory", "var(--primary)", 16)} '
            f"<span>Faydalı Yük ve Hava Direnci (Cd)</span></div>",
            unsafe_allow_html=True,
        )
        payload_shape = st.selectbox(
            "Yük Şekli",
            options=list(PAYLOAD_SHAPE_CD_PRESETS.keys()),
            index=4,
        )
        preset_cd = PAYLOAD_SHAPE_CD_PRESETS[payload_shape]
        if payload_shape == "Özel Değer":
            drag_coefficient = st.slider(
                "Hava Direnci Katsayısı (Cd)",
                min_value=0.05,
                max_value=2.00,
                value=0.47,
                step=0.01,
            )
        else:
            drag_coefficient = preset_cd
            st.caption(f"Sürtünme katsayısı: Cd = {drag_coefficient:.2f}")

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
            f"<span>Rüzgar</span></div>",
            unsafe_allow_html=True,
        )
        wind_speed_mps = st.slider(
            "Rüzgar Hızı (m/s)",
            min_value=0.0,
            max_value=25.0,
            value=7.5,
            step=0.5,
        )
        wind_from_deg = render_direction_dial(
            key="wind_from_dial",
            label="Rüzgarın Estiği Yön",
            mode="wind",
            default_angle=210,
            palette=active_palette,
            subtitle="Ok rüzgarın geldiği taraftan merkeze doğru eser",
        )
        wx, wy = wind_from_to_vector(wind_speed_mps, float(wind_from_deg))
        push_dir = compass_direction_name((wind_from_deg + 180) % 360)
        st.caption(f"Yükü {push_dir} yönüne iter (Doğu {wx:+.1f}, Kuzey {wy:+.1f} m/s)")

        st.divider()
        st.markdown(
            f'<div class="celebi-metric-label">{svg_icon("target", "var(--primary)", 16)} '
            f"<span>Hedef Konumu (m)</span></div>",
            unsafe_allow_html=True,
        )
        col_tx, col_ty = st.columns(2)
        with col_tx:
            target_x_m = st.number_input("Doğu X (m)", value=0.0, step=10.0)
        with col_ty:
            target_y_m = st.number_input("Kuzey Y (m)", value=0.0, step=10.0)

        with st.expander("Gelişmiş Fizik Ayarları"):
            flight_path_angle_deg = st.slider(
                "Tırmanma / Dalış Açısı γ (°)",
                min_value=-20,
                max_value=20,
                value=0,
                step=1,
            )
            use_isa = st.checkbox(
                "İrtifaya bağlı hava yoğunluğu (ISA)",
                value=False,
            )
            wind_shear_coeff = st.slider(
                "Yükseklikle rüzgar artışı (1/m)",
                min_value=0.0,
                max_value=0.010,
                value=0.0,
                step=0.001,
                format="%.3f",
            )

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
        flight_path_angle_deg=float(flight_path_angle_deg),
        use_isa=bool(use_isa),
        wind_shear_coeff=float(wind_shear_coeff),
    )
    return theme_choice, inputs
