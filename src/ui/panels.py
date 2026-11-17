"""Ana ekran başlık, 7.1/7.2/7.3 özet kartları ve rapor dışa aktarım panelleri."""

import streamlit as st
from src.ui.theme import SPACE_1, SPACE_2, ThemePalette, svg_icon
from src.visualization.export_static import export_summary_figure_bytes
from src.visualization.geometry import format_lead_distance
from src.visualization.schemas import DropScenarioView


def render_header(active_module: str, scenario: DropScenarioView | None, palette: ThemePalette) -> None:
    """Seçili modüle göre sade sayfa başlığını ve durum rozetini çizer."""
    if active_module.startswith("7.3"):
        badge_text = (
            "7.3 Aktif · Geçici İleri Fizik"
            if (scenario is None or scenario.is_demo_mode)
            else "7.3 Aktif · Gerçek RK4 Fizik Motoru"
        )
        subtitle = (
            "Hedefi vurmak için yükü hedeften kaç metre önce (ve rüzgar varsa kaç metre yandan) "
            "bırakmanız gerektiğini gerçek RK4 fizik motoru üzerinde hesaplar."
        )
    elif active_module.startswith("7.1"):
        badge_text = "7.1 Aktif · compute_vacum_ballistics"
        subtitle = (
            "İHA ilk hızı, bırakılma irtifası ve yerçekimi ivmesi kullanarak sürtünmesiz (vakum) "
            "temel düşüş yörüngesini ve menzilini hesaplar."
        )
    else:
        badge_text = "7.2 Aktif · simulate_trajectory (RK4)"
        subtitle = (
            "Aynı bırakma noktasından bırakılan yükün hava direnci (Cd) ve rüzgar etkisiyle "
            "7.1 vakum yörüngesinden ne kadar saptığını gösterir."
        )

    theme_icon = svg_icon("sun" if not palette.is_dark else "moon", palette.primary, 15)
    target_icon = svg_icon("target", palette.accent, 15)

    st.markdown(
        f"""
        <header class="celebi-header">
          <div>
            <div class="celebi-kicker">Çelebi İHA · Yük Bırakma Simülatörü</div>
            <h1 style="margin:0;">{active_module}</h1>
            <p class="celebi-subtitle">{subtitle}</p>
          </div>
          <div style="display:flex; gap:{SPACE_1}px; flex-wrap:wrap;">
            <span class="celebi-badge">{theme_icon} { "Açık Tema" if not palette.is_dark else "Koyu Tema" }</span>
            <span class="celebi-badge">{target_icon} {badge_text}</span>
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_71_kpis(scenario: DropScenarioView, palette: ThemePalette) -> None:
    """7.1 Balistik Hareket Denklemleri özet kartlarını çizer."""
    act = scenario.actual_trajectory
    imp = act.impact_point
    inp = scenario.inputs

    col1, col2, col3 = st.columns([1.5, 1.0, 1.0], gap="medium")
    with col1:
        st.markdown(
            f"""
            <div class="celebi-card celebi-card-featured">
              <div class="celebi-metric-label">
                {svg_icon("trajectory", palette.accent, 17)}
                <span>7.1 Sürtünmesiz Düşüş Menzili</span>
              </div>
              <div class="celebi-metric-value">{act.horizontal_range:.1f} m</div>
              <div class="celebi-metric-note" style="line-height:1.5;">
                (0, 0) noktasından {inp.uav_speed_mps:.0f} m/s hız ve {inp.release_altitude_m:.0f} m yükseklikten
                bırakılan yük, hava direnci yokken <strong>{act.horizontal_range:.1f} m</strong> ileri düşer.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="celebi-card">
              <div class="celebi-metric-label">
                {svg_icon("aircraft", palette.primary, 17)}
                <span>Serbest Düşüş Süresi</span>
              </div>
              <div class="celebi-metric-value">{act.flight_time:.2f} sn</div>
              <div class="celebi-metric-note">
                Analitik vakum uçuş süresi (g = {inp.gravity_mps2:.2f} m/s²).
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="celebi-card">
              <div class="celebi-metric-label">
                {svg_icon("target", palette.primary, 17)}
                <span>Çarpma Hızı ve Koordinatı</span>
              </div>
              <div class="celebi-metric-value">{act.speed[-1]:.1f} m/s</div>
              <div class="celebi-metric-note">
                Düşüş (ENU): <span class="celebi-mono">X={imp.x:.1f} m, Y={imp.y:.1f} m</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_72_kpis(scenario: DropScenarioView, palette: ThemePalette) -> None:
    """7.2 Hava Sürtünmesi ve Rüzgar Sapması özet kartlarını çizer."""
    act = scenario.actual_trajectory
    vac = scenario.vacuum_trajectory
    inp = scenario.inputs

    col1, col2, col3 = st.columns([1.6, 1.0, 1.0], gap="medium")
    with col1:
        st.markdown(
            f"""
            <div class="celebi-card celebi-card-featured">
              <div class="celebi-metric-label">
                {svg_icon("wind", palette.accent, 17)}
                <span>7.2 Vakuma Göre Toplam Sapma</span>
              </div>
              <div class="celebi-metric-value">{scenario.drift_from_vacuum_m:.1f} m</div>
              <div class="celebi-metric-note" style="line-height:1.5;">
                Aynı (0, 0) noktasından bırakıldığında hava direnci (Cd={inp.drag_coefficient:.2f}) ve
                rüzgar ({inp.wind_speed_mps:.1f} m/s) yükü sürtünmesiz hesaba göre
                <strong>{scenario.drift_from_vacuum_m:.1f} m</strong> saptırır.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="celebi-card">
              <div class="celebi-metric-label">
                {svg_icon("trajectory", palette.primary, 17)}
                <span>Gerçekçi vs Vakum Menzili</span>
              </div>
              <div class="celebi-metric-value">{act.horizontal_range:.1f} m</div>
              <div class="celebi-metric-note">
                Sürtünmesiz (7.1): <span class="celebi-mono">{vac.horizontal_range:.1f} m</span><br/>
                Düşüş (ENU): <span class="celebi-mono">({act.impact_point.x:.1f}, {act.impact_point.y:.1f}) m</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="celebi-card">
              <div class="celebi-metric-label">
                {svg_icon("aircraft", palette.primary, 17)}
                <span>RK4 Düşüş Süresi ve Hızı</span>
              </div>
              <div class="celebi-metric-value">{act.flight_time:.2f} sn</div>
              <div class="celebi-metric-note">
                Vakum süresi: <span class="celebi-mono">{vac.flight_time:.2f} sn</span><br/>
                Yere çarpma hızı: <span class="celebi-mono">{act.speed[-1]:.1f} m/s</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_kpis(scenario: DropScenarioView, palette: ThemePalette) -> None:
    """7.3 Hedefleme için sade ve doğrudan anlaşılır cevap kartlarını çizer."""
    rel = scenario.release_solution
    act = scenario.actual_trajectory
    inp = scenario.inputs

    col_primary, col_sidewind, col_flight = st.columns([1.7, 1.0, 1.0], gap="medium")

    if rel.lead_distance_m >= 0.0:
        headline = f"Hedefin {rel.lead_distance_m:.1f} m önünden bırak"
        plain_explain = (
            f"İHA {inp.uav_speed_mps:.0f} m/s hızla {inp.release_altitude_m:.0f} m yükseklikten uçarken, "
            f"yükü hedefin tam tepesine gelmeden <strong>{rel.lead_distance_m:.1f} metre önce</strong> "
            f"bırakırsan rüzgar ve hava direnci altında tam hedefe iner."
        )
    else:
        headline = f"Hedefi {abs(rel.lead_distance_m):.1f} m geçince bırak"
        plain_explain = (
            f"Karşıdan esen rüzgar ({inp.wind_speed_mps:.1f} m/s) yükü geriye ittiği için "
            f"hedefi <strong>{abs(rel.lead_distance_m):.1f} metre geçtikten sonra</strong> bırakman gerekir."
        )

    with col_primary:
        st.markdown(
            f"""
            <div class="celebi-card celebi-card-featured">
              <div class="celebi-metric-label">
                {svg_icon("target", palette.accent, 17)}
                <span>7.3 Soru: "Hedefi vurmak için yükü kaç metre önce bırakmalıyım?"</span>
              </div>
              <div class="celebi-metric-value">{headline}</div>
              <div class="celebi-metric-note" style="line-height:1.5;">
                {plain_explain}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if abs(rel.lateral_offset_m) < 0.2:
        side_headline = "Tam rota üstünde"
        side_note = "Yan rüzgar sapması yok; İHA doğrudan hedef hizasından geçebilir."
    else:
        side_dir = "sağından" if rel.lateral_offset_m > 0 else "solundan"
        side_headline = f"{abs(rel.lateral_offset_m):.1f} m {side_dir} geç"
        side_note = (
            f"Yan rüzgarı dengelemek için rotayı hedefin {abs(rel.lateral_offset_m):.1f} m {side_dir} geçir. "
            f"Doğrudan hedef üstünden uçulursa {rel.fixed_track_miss_m:.1f} m yandan sapar."
        )

    with col_sidewind:
        st.markdown(
            f"""
            <div class="celebi-card">
              <div class="celebi-metric-label">
                {svg_icon("wind", palette.primary, 17)}
                <span>Yan Rüzgar Düzeltmesi</span>
              </div>
              <div class="celebi-metric-value">{side_headline}</div>
              <div class="celebi-metric-note" style="line-height:1.45;">
                {side_note}
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
                <span>Düşüş Süresi ve İniş Hızı</span>
              </div>
              <div class="celebi-metric-value">{act.flight_time:.2f} sn</div>
              <div class="celebi-metric-note" style="line-height:1.45;">
                Bırakma sonrası yere ulaşma süresi.<br/>
                Yere çarpma hızı: <span class="celebi-mono">{act.speed[-1]:.1f} m/s</span>
                · Bırakma ENU: <span class="celebi-mono">({rel.release_point.x:.0f}, {rel.release_point.y:.0f}) m</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_export_and_notes(scenario: DropScenarioView, palette: ThemePalette) -> None:
    """Statik Matplotlib rapor indirme ve senaryo özet panelini çizer."""
    rel = scenario.release_solution
    inp = scenario.inputs
    mode = scenario.scenario_mode

    if mode == "7.1":
        summary_line = f"<strong>Menzil:</strong> {scenario.actual_trajectory.horizontal_range:.1f} m"
    elif mode == "7.2":
        summary_line = (
            f"<strong>Vakuma Göre Sapma:</strong> {scenario.drift_from_vacuum_m:.1f} m "
            f"(Gerçek {scenario.actual_trajectory.horizontal_range:.1f} m / "
            f"Vakum {scenario.vacuum_trajectory.horizontal_range:.1f} m)"
        )
    else:
        summary_line = (
            f"<strong>Sonuç:</strong> {format_lead_distance(rel.lead_distance_m)} "
            f"(Hata: <span class='celebi-mono'>{rel.predicted_error_m:.4f} m</span>, "
            f"{rel.solver_method}, {rel.solver_iterations} adım)"
        )

    st.markdown(
        f"""
        <div class="celebi-card" style="margin-bottom:{SPACE_2}px;">
          <div class="celebi-metric-label">
            {svg_icon("download", palette.primary, 17)}
            <span>{mode} Rapor Çıktısı ve Senaryo Özeti</span>
          </div>
          <p style="font-size:0.875rem; color:{palette.text_secondary}; margin-bottom:{SPACE_2}px;">
            Sunum ve teknik raporlar için 3 panelli yüksek çözünürlüklü özet görselini
            PNG veya vektör SVG olarak indirebilirsin.
          </p>
          <div style="font-size:0.85rem; line-height:1.7; color:{palette.text_primary};">
            {summary_line}<br/>
            <strong>Yük:</strong> {inp.payload_shape} (Cd={inp.drag_coefficient:.2f}, {inp.payload_mass_kg:.1f} kg)<br/>
            <strong>İHA:</strong> {inp.uav_speed_mps:.1f} m/s · {inp.release_altitude_m:.0f} m yükseklik · {inp.uav_heading_deg:.0f}° istikamet<br/>
            <strong>Rüzgar:</strong> {inp.wind_speed_mps:.1f} m/s ({inp.wind_from_deg:.0f}° yönünden) · ISA: {"Açık" if inp.use_isa else "Kapalı"}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    show_vac = mode == "7.2"
    col_png, col_svg = st.columns(2, gap="small")
    with col_png:
        st.download_button(
            label="PNG Rapor İndir (220 DPI)",
            data=lambda: export_summary_figure_bytes(scenario, palette, fmt="png", show_vacuum_reference=show_vac),
            file_name=f"celebi_{mode.replace('.', '_')}_ozet.png",
            mime="image/png",
            width="stretch",
        )
    with col_svg:
        st.download_button(
            label="SVG Vektör İndir",
            data=lambda: export_summary_figure_bytes(scenario, palette, fmt="svg", show_vacuum_reference=show_vac),
            file_name=f"celebi_{mode.replace('.', '_')}_ozet.svg",
            mime="image/svg+xml",
            width="stretch",
        )

    with st.expander("Bağlı Fizik Motoru Bilgisi"):
        st.markdown(
            f"""
            <div style="font-size:0.85rem; color:{palette.text_secondary}; padding:{SPACE_1}px 0;">
              <strong>7.1 & 7.2:</strong> Arkadaşınızın <code>koordinatsistemi.py</code> ve
              <code>balistik_motor.py</code> (RK4 <code>dt=0.01 s</code>) motorundan doğrudan çalışır.<br/>
              <strong>7.3:</strong> <code>src/targeting/release_solver.py</code> algoritması gerçek RK4
              motorunu yinelemeli olarak çalıştırarak hedefleme noktasını hesaplar.
            </div>
            """,
            unsafe_allow_html=True,
        )
