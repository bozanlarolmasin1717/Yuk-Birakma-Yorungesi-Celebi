"""Ana ekran başlık, modül bekleme ekranları, 7.3 özet kartları ve rapor dışa aktarımı."""

import streamlit as st
from src.ui.theme import SPACE_1, SPACE_2, SPACE_3, ThemePalette, svg_icon
from src.visualization.export_static import export_summary_figure_bytes
from src.visualization.geometry import format_lead_distance
from src.visualization.schemas import DropScenarioView


def render_header(active_module: str, scenario: DropScenarioView | None, palette: ThemePalette) -> None:
    """Seçili modüle göre sade sayfa başlığını ve durum rozetini çizer."""
    if active_module.startswith("7.3"):
        badge_text = (
            "7.3 Aktif · Geçici İleri Fizik Kullanılıyor"
            if (scenario is None or scenario.is_demo_mode)
            else "7.3 Aktif · Fizik Motoru Bağlı"
        )
        subtitle = (
            "Hedefi vurmak için yükü hedeften kaç metre önce (ve rüzgar varsa kaç metre yandan) "
            "bırakmanız gerektiğini hesaplar ve canlı gösterir."
        )
    elif active_module.startswith("7.1"):
        badge_text = "7.1 · Arkadaşından Bekleniyor"
        subtitle = "İlk hız, bırakılma irtifası ve yerçekimi ile temel (sürtünmesiz) düşüş yörüngesi."
    else:
        badge_text = "7.2 · Arkadaşından Bekleniyor"
        subtitle = "Yük şekli (Cd) ve rüzgarın yönü/şiddetine göre oluşan sapma modeli."

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


def render_module_placeholder(module_code: str, palette: ThemePalette) -> None:
    """7.1 ve 7.2 modülleri için arkadaşının kodu gelene kadar sade bilgi kartı gösterir."""
    if module_code == "7.1":
        title = "7.1 Balistik Hareket Denklemleri Henüz Bağlanmadı"
        goal = (
            "Bu bölümde İHA'nın ilk hızı, bırakılma irtifası ve yerçekimi ivmesi kullanılarak "
            "temel düşüş yörüngesi çizilecek."
        )
        ready = "koordinatsistemi.py içinde ENU koordinat ekseni, UavState ve simulationResult tanımları hazır."
        pending = "Arkadaşının yazacağı temel ileri balistik fonksiyonu (simulate_drop) bekleniyor."
    else:
        title = "7.2 Hava Sürtünmesi ve Rüzgar Modeli Henüz Bağlanmadı"
        goal = (
            "Bu bölümde yükün sürtünme katsayısı (Cd) ile rüzgar yönü ve şiddetine göre "
            "oluşan sapma miktarı hesaplanıp gösterilecek."
        )
        ready = (
            "koordinatsistemi.py içinde payloadParameters (kütle, Cd, kesit alanı) ve "
            "environmentParameters (rüzgar hızı, yönü, hava yoğunluğu) tanımları hazır."
        )
        pending = "Arkadaşının sürükleme kuvveti ve rüzgar etkili sayısal yörünge motoru bekleniyor."

    st.markdown(
        f"""
        <div class="celebi-card celebi-card-featured" style="margin-top:{SPACE_2}px; max-width: 78ch;">
          <div class="celebi-metric-label">
            {svg_icon("trajectory", palette.accent, 18)}
            <span>Arkadaşının Kısmı · Entegrasyona Hazır</span>
          </div>
          <h2 style="margin-top:{SPACE_1}px;">{title}</h2>
          <p style="font-size:0.95rem; color:{palette.text_primary}; margin-bottom:{SPACE_2}px;">
            {goal}
          </p>
          <div style="font-size:0.875rem; line-height:1.7; color:{palette.text_secondary};">
            <strong>Hazır olanlar:</strong> {ready}<br/>
            <strong>Beklenen:</strong> {pending}<br/>
            <strong>Nasıl bağlanacak:</strong> İleri fizik fonksiyonu geldiğinde yalnızca
            <code>src/integration/adapter.py</code> üzerinden bağlanıp bu ekran otomatik açılacak.
            Şimdilik çalışan hedefleme ekranını görmek için üstten <strong>7.3 · Hedefleme Algoritması</strong>
            seçeneğini kullanabilirsin.
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
    """Statik Matplotlib rapor indirme ve 7.3 senaryo özet panelini çizer."""
    rel = scenario.release_solution
    inp = scenario.inputs

    st.markdown(
        f"""
        <div class="celebi-card" style="margin-bottom:{SPACE_2}px;">
          <div class="celebi-metric-label">
            {svg_icon("download", palette.primary, 17)}
            <span>7.3 Rapor Çıktısı ve Senaryo Özeti</span>
          </div>
          <p style="font-size:0.875rem; color:{palette.text_secondary}; margin-bottom:{SPACE_2}px;">
            Sunum ve teknik raporlar için 3 panelli yüksek çözünürlüklü özet görselini
            PNG veya vektör SVG olarak indirebilirsin.
          </p>
          <div style="font-size:0.85rem; line-height:1.7; color:{palette.text_primary};">
            <strong>Sonuç:</strong> {format_lead_distance(rel.lead_distance_m)}<br/>
            <strong>Yük:</strong> {inp.payload_shape} (Cd={inp.drag_coefficient:.2f}, {inp.payload_mass_kg:.1f} kg)<br/>
            <strong>İHA:</strong> {inp.uav_speed_mps:.1f} m/s · {inp.release_altitude_m:.0f} m yükseklik · {inp.uav_heading_deg:.0f}° istikamet<br/>
            <strong>Rüzgar:</strong> {inp.wind_speed_mps:.1f} m/s ({inp.wind_from_deg:.0f}° yönünden)<br/>
            <strong>Hedefleme Hatası:</strong> <span class="celebi-mono">{rel.predicted_error_m:.4f} m</span>
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
            file_name="celebi_7_3_hedefleme_ozeti.png",
            mime="image/png",
            width="stretch",
        )
    with col_svg:
        st.download_button(
            label="SVG Vektör İndir",
            data=lambda: export_summary_figure_bytes(scenario, palette, fmt="svg"),
            file_name="celebi_7_3_hedefleme_ozeti.svg",
            mime="image/svg+xml",
            width="stretch",
        )

    with st.expander("Fizik Motoru Entegrasyon Notu (Adaptör Sözleşmesi)"):
        st.markdown(
            f"""
            <div style="font-size:0.85rem; color:{palette.text_secondary}; padding:{SPACE_1}px 0;">
              <strong>7.3 Hedefleme Algoritması</strong> <code>src/targeting/</code> altında gerçek olarak
              çalışmaktadır. İleri fizik şimdilik <code>src/integration/demo_provider.py</code> ile
              üretilir; arkadaşının <code>7.1 + 7.2</code> fizik motoru geldiğinde
              <code>src/integration/adapter.py</code> üzerinden bağlanır.
            </div>
            """,
            unsafe_allow_html=True,
        )
