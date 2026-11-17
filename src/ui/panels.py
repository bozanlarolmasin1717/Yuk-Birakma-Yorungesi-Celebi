"""Ana ekran başlık, asimetrik KPI kartları ve statik dışa aktarım panelleri."""

import streamlit as st
from src.ui.theme import SPACE_1, SPACE_2, SPACE_3, ThemePalette, svg_icon
from src.visualization.export_static import export_summary_figure_bytes
from src.visualization.geometry import format_lead_distance
from src.visualization.schemas import DropScenarioView


def render_header(scenario: DropScenarioView, palette: ThemePalette) -> None:
    """Sayfa üst başlığını ve veri kaynağı durum rozetini çizer."""
    badge_text = (
        "7.3 Hedefleme Aktif · Geçici İleri Fizik"
        if scenario.is_demo_mode
        else "7.3 Hedefleme + Fizik Motoru Bağlı"
    )
    theme_icon = svg_icon("sun" if not palette.is_dark else "moon", palette.primary, 15)
    target_icon = svg_icon("target", palette.accent, 15)

    st.markdown(
        f"""
        <header class="celebi-header">
          <div>
            <div class="celebi-kicker">Proje 7 · Balistik Bırakma Görselleştirme</div>
            <h1 style="margin:0;">Yük Bırakma Yörüngesi ve Hedefleme Analizi</h1>
            <p class="celebi-subtitle">
              Hareket halindeki İHA'dan bırakılan yükün vakum referansı ile hava sürtünmesi (Cd)
              ve rüzgar etkileri altındaki yörüngesini karşılaştırır; hedefi vurmak için gereken
              bırakma noktasını SI birimlerinde görselleştirir.
            </p>
          </div>
          <div style="display:flex; gap:{SPACE_1}px; flex-wrap:wrap;">
            <span class="celebi-badge">{theme_icon} { "Açık Tema" if not palette.is_dark else "Koyu Tema" }</span>
            <span class="celebi-badge">{target_icon} {badge_text}</span>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(scenario: DropScenarioView, palette: ThemePalette) -> None:
    """Kırık simetrili (asimetrik) temel bırakma ve sapma kartlarını sunar."""
    rel = scenario.release_solution
    act = scenario.actual_trajectory
    vac = scenario.vacuum_trajectory

    # Asimetrik ızgara: Sol vurgulu ana cevap (7.3), sağda iki destekleyici teknik blok
    col_primary, col_drift, col_flight = st.columns([1.65, 1.0, 1.0], gap="medium")

    lead_text = format_lead_distance(rel.lead_distance_m)

    fixed_note = (
        f"<br/>Doğrudan hedef hattında: <span class='celebi-mono'>{format_lead_distance(rel.fixed_track_lead_m)}</span> "
        f"(yan sapma: <span class='celebi-mono'>{rel.fixed_track_miss_m:.1f} m</span>)"
        if rel.fixed_track_miss_m > 0.1
        else ""
    )

    with col_primary:
        st.markdown(
            f"""
            <div class="celebi-card celebi-card-featured">
              <div class="celebi-metric-label">
                {svg_icon("target", palette.accent, 17)}
                <span>7.3 İdeal Bırakma Mesafesi (Hedefin Öncesi)</span>
              </div>
              <div class="celebi-metric-value">{lead_text}</div>
              <div class="celebi-metric-note">
                Bırakma (ENU):
                <span class="celebi-mono">X={rel.release_point.x:.1f} m, Y={rel.release_point.y:.1f} m, Z={rel.release_point.z:.0f} m</span>
                · Yanal kayma: <span class="celebi-mono">{rel.lateral_offset_m:+.1f} m</span>
                · Vakum hesabı: <span class="celebi-mono">{rel.vacuum_lead_distance_m:.1f} m önce</span>
                {fixed_note}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_drift:
        st.markdown(
            f"""
            <div class="celebi-card">
              <div class="celebi-metric-label">
                {svg_icon("wind", palette.primary, 17)}
                <span>7.2 Sürtünme + Rüzgar Sapması</span>
              </div>
              <div class="celebi-metric-value">{scenario.drift_from_vacuum_m:.1f} m</div>
              <div class="celebi-metric-note">
                Vakum menzili: <span class="celebi-mono">{vac.horizontal_range:.1f} m</span> ·
                Gerçek menzil: <span class="celebi-mono">{act.horizontal_range:.1f} m</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_flight:
        st.markdown(
            f"""
            <div class="celebi-card">
              <div class="celebi-metric-label">
                {svg_icon("trajectory", palette.primary, 17)}
                <span>7.1 Uçuş Süresi ve Çarpma Hızı</span>
              </div>
              <div class="celebi-metric-value">{act.flight_time:.2f} s</div>
              <div class="celebi-metric-note">
                Vakum süresi: <span class="celebi-mono">{vac.flight_time:.2f} s</span> ·
                Çarpma hızı: <span class="celebi-mono">{act.speed[-1]:.1f} m/s</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_export_and_notes(scenario: DropScenarioView, palette: ThemePalette) -> None:
    """Statik Matplotlib rapor indirme ve senaryo özet panelini çizer."""
    rel = scenario.release_solution
    inp = scenario.inputs

    st.markdown(
        f"""
        <div class="celebi-card" style="margin-bottom:{SPACE_2}px;">
          <div class="celebi-metric-label">
            {svg_icon("download", palette.primary, 17)}
            <span>Rapor Çıktısı ve Senaryo Özeti</span>
          </div>
          <p style="font-size:0.875rem; color:{palette.text_secondary}; margin-bottom:{SPACE_2}px;">
            Etkileşimli Plotly grafiklerine ek olarak, sunum ve teknik raporlar için 3 panelli
            yüksek çözünürlüklü Matplotlib özet görselini dışa aktarabilirsiniz.
          </p>
          <div style="font-size:0.85rem; line-height:1.65; color:{palette.text_primary};">
            <strong>Yük:</strong> {inp.payload_shape} (Cd={inp.drag_coefficient:.2f}, {inp.payload_mass_kg:.1f} kg)<br/>
            <strong>İHA:</strong> {inp.uav_speed_mps:.1f} m/s @ {inp.release_altitude_m:.0f} m irtifa, {inp.uav_heading_deg:.0f}° yön<br/>
            <strong>Rüzgar:</strong> {inp.wind_speed_mps:.1f} m/s ({inp.wind_from_deg:.0f}° yönünden)<br/>
            <strong>Hedef Sapması:</strong> <span class="celebi-mono">{rel.predicted_error_m:.4f} m</span>
            ({rel.solver_method}, {rel.solver_iterations} adım)
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_png, col_svg = st.columns(2, gap="small")
    with col_png:
        st.download_button(
            label="PNG Rapor İndir (220 DPI)",
            data=lambda: export_summary_figure_bytes(scenario, palette, fmt="png"),
            file_name="celebi_yorunge_ozeti.png",
            mime="image/png",
            width="stretch",
        )
    with col_svg:
        st.download_button(
            label="SVG Vektör İndir",
            data=lambda: export_summary_figure_bytes(scenario, palette, fmt="svg"),
            file_name="celebi_yorunge_ozeti.svg",
            mime="image/svg+xml",
            width="stretch",
        )

    with st.expander("Fizik Motoru Entegrasyon Notu (Adaptör Sözleşmesi)"):
        st.markdown(
            f"""
            <div style="font-size:0.85rem; color:{palette.text_secondary}; padding:{SPACE_1}px 0;">
              <strong>7.3 Hedefleme Algoritması</strong> aktif olarak <code>src/targeting/</code> üzerinden
              çalışmaktadır. İleri fizik tarafı şu an <code>src/integration/demo_provider.py</code>
              ile simüle edilir; arkadaşınızın <code>7.1 + 7.2</code> motoru hazır olduğunda
              <code>src/integration/adapter.py</code> içindeki <code>build_scenario_from_friend_physics</code>
              çağrısıyla doğrudan bağlanır.
            </div>
            """,
            unsafe_allow_html=True,
        )
