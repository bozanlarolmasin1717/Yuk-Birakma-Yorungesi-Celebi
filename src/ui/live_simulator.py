"""HTML5 Canvas tabanlı senkronize canlı yük bırakma simülatörü."""

import json
import streamlit.components.v1 as components
from src.ui.theme import (
    FONT_BODY,
    FONT_HEADING,
    FONT_MONO,
    SPACE_1,
    SPACE_2,
    SPACE_3,
    ThemePalette,
)
from src.visualization.geometry import (
    compute_axis_bounds,
    format_lead_distance,
    heading_basis,
    project_along_heading,
)
from src.visualization.schemas import DropScenarioView, TrajectorySeries


def _serialize_series(
    series: TrajectorySeries,
    rel_x: float,
    rel_y: float,
    rel_z: float,
    heading_deg: float,
) -> dict[str, list[float]]:
    from src.visualization.schemas import Point3D

    s_vals = project_along_heading(series.x, series.y, Point3D(rel_x, rel_y, rel_z), heading_deg)
    return {
        "t": [round(v, 4) for v in series.t],
        "s": [round(v, 3) for v in s_vals],
        "x": [round(v, 3) for v in series.x],
        "y": [round(v, 3) for v in series.y],
        "z": [round(v, 3) for v in series.z],
        "speed": [round(v, 3) for v in series.speed],
    }


def build_simulator_html(scenario: DropScenarioView, palette: ThemePalette) -> str:
    """Canlı simülasyon bileşeninin saf HTML/CSS/JS çıktısını üretir."""
    rel = scenario.release_solution.release_point
    tgt = scenario.release_solution.target_point
    vac = scenario.vacuum_trajectory
    act = scenario.actual_trajectory
    heading_deg = scenario.inputs.uav_heading_deg
    (hx, hy), _ = heading_basis(heading_deg)

    tgt_s = project_along_heading((tgt.x,), (tgt.y,), rel, heading_deg)[0]
    vac_s = project_along_heading(vac.x, vac.y, rel, heading_deg)
    (x_min, x_max), (y_min, y_max) = compute_axis_bounds(vac, act, tgt, padding_ratio=0.18)

    payload = {
        "actual": _serialize_series(act, rel.x, rel.y, rel.z, heading_deg),
        "vacuum": _serialize_series(vac, rel.x, rel.y, rel.z, heading_deg),
        "release": {"x": rel.x, "y": rel.y, "z": rel.z, "s": 0.0},
        "target": {"x": tgt.x, "y": tgt.y, "z": 0.0, "s": tgt_s},
        "vacImpact": {"x": vac.impact_point.x, "y": vac.impact_point.y, "s": vac_s[-1]},
        "uav": {
            "speed": scenario.inputs.uav_speed_mps,
            "headingDeg": heading_deg,
            "hx": hx,
            "hy": hy,
            "altitude": scenario.inputs.release_altitude_m,
        },
        "wind": {
            "wx": scenario.wind_vector_mps[0],
            "wy": scenario.wind_vector_mps[1],
            "speed": scenario.inputs.wind_speed_mps,
        },
        "bounds2d": {"x": [x_min, x_max], "y": [y_min, y_max]},
        "leadLabel": format_lead_distance(scenario.release_solution.lead_distance_m),
        "tFlight": max(act.flight_time, vac.flight_time),
        "tActualImpact": act.flight_time,
        "palette": {
            "bgPage": palette.bg_page,
            "bgSurface": palette.bg_surface,
            "bgElevated": palette.bg_elevated,
            "textPrimary": palette.text_primary,
            "textSecondary": palette.text_secondary,
            "primary": palette.primary,
            "primaryHover": palette.primary_hover,
            "buttonText": palette.button_text,
            "accent": palette.accent,
            "reference": palette.reference,
            "windColor": palette.wind_color,
            "border": palette.border,
            "gridLine": palette.grid_line,
        },
    }

    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8" />
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0;
      padding: 0;
      background: transparent;
      color: {palette.text_primary};
      font-family: {FONT_BODY};
    }}
    .sim-shell {{
      background: {palette.bg_surface};
      border: 1px solid {palette.border};
      border-radius: 8px;
      padding: {SPACE_2}px;
      box-shadow: {palette.shadow};
    }}
    .sim-controls {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: {SPACE_2}px;
      padding-bottom: {SPACE_2}px;
      border-bottom: 1px solid {palette.border};
    }}
    .btn-group {{
      display: flex;
      align-items: center;
      gap: {SPACE_1}px;
      flex-wrap: wrap;
    }}
    .sim-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      height: 34px;
      padding: 0 12px;
      border-radius: 6px;
      border: 1px solid {palette.border};
      background: {palette.bg_elevated};
      color: {palette.text_primary};
      font-family: {FONT_BODY};
      font-size: 0.8125rem;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 0.16s ease, border-color 0.16s ease;
    }}
    .sim-btn:hover {{
      border-color: {palette.primary};
    }}
    .sim-btn.primary {{
      background: {palette.primary};
      border-color: {palette.primary};
      color: {palette.button_text};
    }}
    .sim-btn.primary:hover {{
      background: {palette.primary_hover};
      border-color: {palette.primary_hover};
    }}
    .sim-btn.active {{
      border-color: {palette.accent};
      color: {palette.accent};
      font-weight: 600;
    }}
    .scrubber-wrap {{
      display: flex;
      align-items: center;
      gap: {SPACE_2}px;
      flex: 1 1 260px;
      min-width: 220px;
    }}
    .scrubber-wrap input[type="range"] {{
      width: 100%;
      accent-color: {palette.primary};
      cursor: pointer;
    }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 12px;
      border-radius: 6px;
      border: 1px solid {palette.border};
      background: {palette.bg_page};
      color: {palette.text_primary};
      font-size: 0.8125rem;
      font-weight: 600;
      white-space: nowrap;
    }}
    .status-dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: {palette.primary};
    }}
    .status-dot.dropped {{ background: {palette.accent}; }}
    .status-dot.hit {{ background: {palette.primary}; }}

    .telemetry-bar {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: {SPACE_1}px;
      padding: {SPACE_2}px 0;
    }}
    .tele-cell {{
      background: {palette.bg_page};
      border: 1px solid {palette.border};
      border-radius: 6px;
      padding: {SPACE_1}px {SPACE_2}px;
    }}
    .tele-label {{
      font-size: 0.75rem;
      color: {palette.text_secondary};
      margin-bottom: 2px;
    }}
    .tele-val {{
      font-family: {FONT_MONO};
      font-variant-numeric: tabular-nums;
      font-size: 1.05rem;
      font-weight: 600;
      color: {palette.text_primary};
    }}

    .canvas-grid {{
      display: grid;
      grid-template-columns: 1.35fr 1fr;
      gap: {SPACE_2}px;
      margin-top: {SPACE_1}px;
    }}
    .canvas-card {{
      background: {palette.bg_page};
      border: 1px solid {palette.border};
      border-radius: 6px;
      padding: {SPACE_2}px;
      display: flex;
      flex-direction: column;
    }}
    .canvas-head {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: {SPACE_1}px;
      gap: {SPACE_1}px;
    }}
    .canvas-title {{
      font-family: {FONT_HEADING};
      font-size: 1rem;
      font-weight: 600;
      color: {palette.text_primary};
    }}
    .canvas-legend {{
      display: flex;
      gap: {SPACE_2}px;
      font-size: 0.75rem;
      color: {palette.text_secondary};
      flex-wrap: wrap;
    }}
    .leg-item {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}
    .leg-line {{
      width: 14px;
      height: 2px;
      display: inline-block;
    }}
    canvas {{
      width: 100%;
      height: 296px;
      display: block;
    }}
    @media (max-width: 820px) {{
      .telemetry-bar {{
        grid-template-columns: repeat(2, minmax(110px, 1fr));
      }}
      .canvas-grid {{
        grid-template-columns: 1fr;
      }}
      canvas {{
        height: 250px;
      }}
    }}
  </style>
</head>
<body>
  <div class="sim-shell">
    <div class="sim-controls">
      <div class="btn-group">
        <button id="btnPlay" class="sim-btn primary" type="button">Duraklat</button>
        <button id="btnReset" class="sim-btn" type="button">Başa Sar</button>
        <button class="sim-btn speed-btn" data-speed="0.5" type="button">0.5x</button>
        <button class="sim-btn speed-btn active" data-speed="1" type="button">1x</button>
        <button class="sim-btn speed-btn" data-speed="2" type="button">2x</button>
      </div>
      <div class="scrubber-wrap">
        <input id="timeSlider" type="range" min="-1.2" max="10" step="0.01" value="-1.2" />
      </div>
      <div class="status-pill">
        <span id="statusDot" class="status-dot"></span>
        <span id="statusText">İHA Yaklaşıyor</span>
      </div>
    </div>

    <div class="telemetry-bar">
      <div class="tele-cell">
        <div class="tele-label">Bırakmaya Göre Zaman</div>
        <div id="valTime" class="tele-val">0.00 s</div>
      </div>
      <div class="tele-cell">
        <div class="tele-label">Yük İrtifası (Z)</div>
        <div id="valAlt" class="tele-val">0.0 m</div>
      </div>
      <div class="tele-cell">
        <div class="tele-label">Yük Anlık Hızı</div>
        <div id="valSpeed" class="tele-val">0.0 m/s</div>
      </div>
      <div class="tele-cell">
        <div class="tele-label">Hedefe Yatay Mesafe</div>
        <div id="valDist" class="tele-val">0.0 m</div>
      </div>
    </div>

    <div class="canvas-grid">
      <div class="canvas-card">
        <div class="canvas-head">
          <span class="canvas-title">Yandan Kesit (İrtifa – Rota Mesafesi)</span>
          <div class="canvas-legend">
            <span class="leg-item"><span class="leg-line" style="background:{palette.accent};"></span>Cd + Rüzgar</span>
            <span class="leg-item"><span class="leg-line" style="border-top:2px dashed {palette.reference};"></span>Vakum</span>
          </div>
        </div>
        <canvas id="sideCanvas"></canvas>
      </div>
      <div class="canvas-card">
        <div class="canvas-head">
          <span class="canvas-title">Kuşbakışı Radar (Doğu – Kuzey)</span>
          <div class="canvas-legend">
            <span class="leg-item"><span class="leg-line" style="background:{palette.wind_color};"></span>Rüzgar Akışı</span>
            <span class="leg-item"><span class="leg-line" style="background:{palette.primary};"></span>Bırakma</span>
          </div>
        </div>
        <canvas id="topCanvas"></canvas>
      </div>
    </div>
  </div>

  <script>
    const DATA = {data_json};
    const P = DATA.palette;
    const PRE_ROLL = -1.2;
    const POST_DWELL = 0.85;
    const T_MAX = DATA.tFlight;

    let simTime = PRE_ROLL;
    let isPlaying = true;
    let speedMult = 1.0;
    let lastTs = null;
    let windPhase = 0;

    const btnPlay = document.getElementById("btnPlay");
    const btnReset = document.getElementById("btnReset");
    const slider = document.getElementById("timeSlider");
    const speedBtns = document.querySelectorAll(".speed-btn");
    const statusDot = document.getElementById("statusDot");
    const statusText = document.getElementById("statusText");
    const valTime = document.getElementById("valTime");
    const valAlt = document.getElementById("valAlt");
    const valSpeed = document.getElementById("valSpeed");
    const valDist = document.getElementById("valDist");

    const sideCanvas = document.getElementById("sideCanvas");
    const topCanvas = document.getElementById("topCanvas");

    slider.min = String(PRE_ROLL);
    slider.max = String(T_MAX.toFixed(2));
    slider.value = String(PRE_ROLL);

    function sampleSeries(series, tQuery) {{
      const ts = series.t;
      const n = ts.length;
      if (tQuery <= 0) {{
        return {{
          s: DATA.uav.speed * tQuery,
          x: DATA.release.x + DATA.uav.hx * DATA.uav.speed * tQuery,
          y: DATA.release.y + DATA.uav.hy * DATA.uav.speed * tQuery,
          z: DATA.uav.altitude,
          speed: DATA.uav.speed,
          dropped: false,
          landed: false,
        }};
      }}
      if (tQuery >= ts[n - 1]) {{
        return {{
          s: series.s[n - 1],
          x: series.x[n - 1],
          y: series.y[n - 1],
          z: series.z[n - 1],
          speed: series.speed[n - 1],
          dropped: true,
          landed: true,
        }};
      }}
      let lo = 0;
      let hi = n - 1;
      while (hi - lo > 1) {{
        const mid = (lo + hi) >> 1;
        if (ts[mid] <= tQuery) lo = mid;
        else hi = mid;
      }}
      const span = Math.max(ts[hi] - ts[lo], 1e-6);
      const a = (tQuery - ts[lo]) / span;
      return {{
        s: series.s[lo] + a * (series.s[hi] - series.s[lo]),
        x: series.x[lo] + a * (series.x[hi] - series.x[lo]),
        y: series.y[lo] + a * (series.y[hi] - series.y[lo]),
        z: series.z[lo] + a * (series.z[hi] - series.z[lo]),
        speed: series.speed[lo] + a * (series.speed[hi] - series.speed[lo]),
        dropped: true,
        landed: false,
      }};
    }}

    function fitCanvas(canvas) {{
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      const w = Math.max(240, Math.round(rect.width * dpr));
      const h = Math.max(180, Math.round(rect.height * dpr));
      if (canvas.width !== w || canvas.height !== h) {{
        canvas.width = w;
        canvas.height = h;
      }}
      const ctx = canvas.getContext("2d");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return {{ ctx, w: rect.width, h: rect.height }};
    }}

    function drawUavGlyph(ctx, px, py, angleRad, color) {{
      ctx.save();
      ctx.translate(px, py);
      ctx.rotate(angleRad);
      ctx.fillStyle = color;
      ctx.strokeStyle = P.bgPage;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(12, 0);
      ctx.lineTo(-4, -3);
      ctx.lineTo(-7, -11);
      ctx.lineTo(-10, -11);
      ctx.lineTo(-8, -2);
      ctx.lineTo(-12, -4);
      ctx.lineTo(-12, 4);
      ctx.lineTo(-8, 2);
      ctx.lineTo(-10, 11);
      ctx.lineTo(-7, 11);
      ctx.lineTo(-4, 3);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }}

    function drawSideCanvas(actState, vacState) {{
      const {{ ctx, w, h }} = fitCanvas(sideCanvas);
      ctx.clearRect(0, 0, w, h);

      const pad = {{ l: 48, r: 22, t: 22, b: 34 }};
      const plotW = w - pad.l - pad.r;
      const plotH = h - pad.t - pad.b;

      const sSamples = [
        PRE_ROLL * DATA.uav.speed,
        0,
        DATA.target.s,
        DATA.vacImpact.s,
        ...DATA.actual.s,
        ...DATA.vacuum.s,
      ];
      let sMin = Math.min(...sSamples) - 18;
      let sMax = Math.max(...sSamples) + 28;
      if (sMax - sMin < 40) {{ sMin -= 20; sMax += 20; }}
      const zMax = Math.max(DATA.uav.altitude * 1.15, 25);

      const toX = (s) => pad.l + ((s - sMin) / (sMax - sMin)) * plotW;
      const toY = (z) => pad.t + plotH - (z / zMax) * plotH;

      // Izgara
      ctx.strokeStyle = P.gridLine;
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {{
        const zTick = (zMax * i) / 4;
        const y = toY(zTick);
        ctx.beginPath();
        ctx.moveTo(pad.l, y);
        ctx.lineTo(w - pad.r, y);
        ctx.stroke();
        ctx.fillStyle = P.textSecondary;
        ctx.font = "11px IBM Plex Mono, monospace";
        ctx.textAlign = "right";
        ctx.fillText(Math.round(zTick) + " m", pad.l - 6, y + 4);
      }}

      // Zemin çizgisi
      const yGround = toY(0);
      ctx.strokeStyle = P.border;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(pad.l, yGround);
      ctx.lineTo(w - pad.r, yGround);
      ctx.stroke();

      // İHA uçuş hattı
      const yAlt = toY(DATA.uav.altitude);
      ctx.save();
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = P.textSecondary;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(pad.l, yAlt);
      ctx.lineTo(w - pad.r, yAlt);
      ctx.stroke();
      ctx.restore();

      // Bırakma düşey kılavuzu
      const xRel = toX(0);
      ctx.save();
      ctx.setLineDash([3, 4]);
      ctx.strokeStyle = P.primary;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(xRel, yAlt);
      ctx.lineTo(xRel, yGround);
      ctx.stroke();
      ctx.restore();

      // Vakum referans eğrisi (soluk rehber + aktif iz)
      ctx.save();
      ctx.setLineDash([5, 4]);
      ctx.strokeStyle = P.reference;
      ctx.globalAlpha = 0.28;
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      DATA.vacuum.s.forEach((sv, idx) => {{
        const px = toX(sv);
        const py = toY(DATA.vacuum.z[idx]);
        if (idx === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }});
      ctx.stroke();
      ctx.restore();

      if (simTime > 0) {{
        // Aktif vakum izi
        ctx.save();
        ctx.setLineDash([5, 4]);
        ctx.strokeStyle = P.reference;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(toX(0), toY(DATA.uav.altitude));
        for (let i = 0; i < DATA.vacuum.t.length; i++) {{
          if (DATA.vacuum.t[i] <= simTime) {{
            ctx.lineTo(toX(DATA.vacuum.s[i]), toY(DATA.vacuum.z[i]));
          }}
        }}
        ctx.lineTo(toX(vacState.s), toY(vacState.z));
        ctx.stroke();
        ctx.restore();

        // Aktif sürtünmeli + rüzgarlı iz
        ctx.save();
        ctx.strokeStyle = P.accent;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(toX(0), toY(DATA.uav.altitude));
        for (let i = 0; i < DATA.actual.t.length; i++) {{
          if (DATA.actual.t[i] <= simTime) {{
            ctx.lineTo(toX(DATA.actual.s[i]), toY(DATA.actual.z[i]));
          }}
        }}
        ctx.lineTo(toX(actState.s), toY(actState.z));
        ctx.stroke();
        ctx.restore();
      }}

      // Bırakma anı nabız halkası
      if (simTime >= 0 && simTime < 1.2) {{
        const pulse = 6 + (simTime / 1.2) * 18;
        ctx.save();
        ctx.strokeStyle = P.primary;
        ctx.globalAlpha = Math.max(0, 1 - simTime / 1.2);
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(xRel, yAlt, pulse, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      }}

      // Hedef işareti
      const xTgt = toX(DATA.target.s);
      ctx.strokeStyle = P.accent;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(xTgt - 6, yGround - 6);
      ctx.lineTo(xTgt + 6, yGround + 6);
      ctx.moveTo(xTgt + 6, yGround - 6);
      ctx.lineTo(xTgt - 6, yGround + 6);
      ctx.stroke();

      ctx.fillStyle = P.textSecondary;
      ctx.font = "11px IBM Plex Sans, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Bırakma", xRel, yGround + 16);
      ctx.fillStyle = P.accent;
      ctx.fillText("Hedef (" + DATA.leadLabel + ")", xTgt, yGround + 28);

      // Hareketli İHA ve yükler
      const uavS = Math.min(Math.max(DATA.uav.speed * simTime, sMin), sMax);
      drawUavGlyph(ctx, toX(uavS), yAlt, 0, P.primary);

      if (simTime > 0) {{
        // Vakum yükü (açık halka)
        ctx.strokeStyle = P.reference;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(toX(vacState.s), toY(vacState.z), 5, 0, Math.PI * 2);
        ctx.stroke();

        // Gerçekçi yük (dolu vurgu noktası)
        ctx.fillStyle = P.accent;
        ctx.beginPath();
        ctx.arc(toX(actState.s), toY(actState.z), 6, 0, Math.PI * 2);
        ctx.fill();
      }}
    }}

    function drawTopCanvas(actState, vacState) {{
      const {{ ctx, w, h }} = fitCanvas(topCanvas);
      ctx.clearRect(0, 0, w, h);

      const pad = 28;
      const size = Math.min(w - pad * 2, h - pad * 2);
      const ox = (w - size) / 2;
      const oy = (h - size) / 2;

      const xMin = DATA.bounds2d.x[0];
      const xMax = DATA.bounds2d.x[1];
      const yMin = DATA.bounds2d.y[0];
      const yMax = DATA.bounds2d.y[1];
      const span = Math.max(xMax - xMin, 1);

      const toPx = (x) => ox + ((x - xMin) / span) * size;
      const toPy = (y) => oy + size - ((y - yMin) / span) * size;

      // Radar çerçevesi ve eksenler
      ctx.strokeStyle = P.gridLine;
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {{
        const p = ox + (size * i) / 4;
        ctx.beginPath();
        ctx.moveTo(p, oy);
        ctx.lineTo(p, oy + size);
        ctx.stroke();
        const q = oy + (size * i) / 4;
        ctx.beginPath();
        ctx.moveTo(ox, q);
        ctx.lineTo(ox + size, q);
        ctx.stroke();
      }}
      ctx.strokeStyle = P.border;
      ctx.strokeRect(ox, oy, size, size);

      // Akan rüzgar akış çizgileri
      if (DATA.wind.speed > 0.1) {{
        const wux = DATA.wind.wx / DATA.wind.speed;
        const wuy = -DATA.wind.wy / DATA.wind.speed;
        ctx.save();
        ctx.beginPath();
        ctx.rect(ox, oy, size, size);
        ctx.clip();
        ctx.strokeStyle = P.windColor;
        ctx.globalAlpha = 0.25;
        ctx.lineWidth = 1.4;
        for (let row = 0; row < 4; row++) {{
          for (let col = 0; col < 4; col++) {{
            const baseX = ox + ((col + 0.5) / 4) * size;
            const baseY = oy + ((row + 0.5) / 4) * size;
            const shift = ((windPhase * (8 + DATA.wind.speed * 3)) % 60) - 30;
            const sx = baseX + wux * shift;
            const sy = baseY + wuy * shift;
            ctx.beginPath();
            ctx.moveTo(sx - wux * 10, sy - wuy * 10);
            ctx.lineTo(sx + wux * 10, sy + wuy * 10);
            ctx.stroke();
          }}
        }}
        ctx.restore();
      }}

      // Hedef 5m ve 15m halkaları
      const pxPerM = size / span;
      const tx = toPx(DATA.target.x);
      const ty = toPy(DATA.target.y);
      [5, 15].forEach((r, idx) => {{
        ctx.save();
        ctx.strokeStyle = P.border;
        if (idx === 1) ctx.setLineDash([3, 3]);
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.arc(tx, ty, Math.max(r * pxPerM, 4), 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      }});

      // İHA yer izi
      const trackStartS = PRE_ROLL * DATA.uav.speed - 20;
      const trackEndS = Math.max(DATA.target.s, DATA.vacImpact.s, 40) + 40;
      ctx.save();
      ctx.setLineDash([3, 4]);
      ctx.strokeStyle = P.textSecondary;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(toPx(DATA.release.x + DATA.uav.hx * trackStartS), toPy(DATA.release.y + DATA.uav.hy * trackStartS));
      ctx.lineTo(toPx(DATA.release.x + DATA.uav.hx * trackEndS), toPy(DATA.release.y + DATA.uav.hy * trackEndS));
      ctx.stroke();
      ctx.restore();

      // Bırakma noktası işareti
      const rx = toPx(DATA.release.x);
      const ry = toPy(DATA.release.y);
      ctx.fillStyle = P.primary;
      ctx.beginPath();
      ctx.moveTo(rx, ry - 6);
      ctx.lineTo(rx + 6, ry);
      ctx.lineTo(rx, ry + 6);
      ctx.lineTo(rx - 6, ry);
      ctx.closePath();
      ctx.fill();

      // Hedef X
      ctx.strokeStyle = P.accent;
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.moveTo(tx - 6, ty - 6);
      ctx.lineTo(tx + 6, ty + 6);
      ctx.moveTo(tx + 6, ty - 6);
      ctx.lineTo(tx - 6, ty + 6);
      ctx.stroke();

      if (simTime > 0) {{
        // Vakum izi
        ctx.save();
        ctx.setLineDash([5, 4]);
        ctx.strokeStyle = P.reference;
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.moveTo(rx, ry);
        for (let i = 0; i < DATA.vacuum.t.length; i++) {{
          if (DATA.vacuum.t[i] <= simTime) {{
            ctx.lineTo(toPx(DATA.vacuum.x[i]), toPy(DATA.vacuum.y[i]));
          }}
        }}
        ctx.lineTo(toPx(vacState.x), toPy(vacState.y));
        ctx.stroke();
        ctx.restore();

        // Gerçekçi iz
        ctx.strokeStyle = P.accent;
        ctx.lineWidth = 2.8;
        ctx.beginPath();
        ctx.moveTo(rx, ry);
        for (let i = 0; i < DATA.actual.t.length; i++) {{
          if (DATA.actual.t[i] <= simTime) {{
            ctx.lineTo(toPx(DATA.actual.x[i]), toPy(DATA.actual.y[i]));
          }}
        }}
        ctx.lineTo(toPx(actState.x), toPy(actState.y));
        ctx.stroke();

        // Vakum ve gerçekçi yük işaretleri
        ctx.strokeStyle = P.reference;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(toPx(vacState.x), toPy(vacState.y), 4.5, 0, Math.PI * 2);
        ctx.stroke();

        ctx.fillStyle = P.accent;
        ctx.beginPath();
        ctx.arc(toPx(actState.x), toPy(actState.y), 5.5, 0, Math.PI * 2);
        ctx.fill();
      }}

      // İHA radar ikonu (Canvas Y aşağı olduğu için açı: headingDeg - 90°)
      const uavDist = DATA.uav.speed * simTime;
      const ux = DATA.release.x + DATA.uav.hx * uavDist;
      const uy = DATA.release.y + DATA.uav.hy * uavDist;
      const canvasAngle = ((DATA.uav.headingDeg - 90) * Math.PI) / 180;
      drawUavGlyph(ctx, toPx(ux), toPy(uy), canvasAngle, P.primary);

      // Etiketler
      ctx.fillStyle = P.textSecondary;
      ctx.font = "11px IBM Plex Sans, sans-serif";
      ctx.textAlign = "left";
      ctx.fillText("Kuzey (+Y)", ox + 6, oy + 14);
      ctx.textAlign = "right";
      ctx.fillText("Rüzgar: " + DATA.wind.speed.toFixed(1) + " m/s", ox + size - 6, oy + size - 8);
    }}

    function updateTelemetry(actState) {{
      valTime.textContent = (simTime >= 0 ? "+" : "") + simTime.toFixed(2) + " s";
      valAlt.textContent = actState.z.toFixed(1) + " m";
      valSpeed.textContent = actState.speed.toFixed(1) + " m/s";
      const distToTarget = Math.hypot(DATA.target.x - actState.x, DATA.target.y - actState.y);
      valDist.textContent = distToTarget.toFixed(1) + " m";

      statusDot.className = "status-dot";
      if (simTime < 0) {{
        statusText.textContent = "İHA Yaklaşıyor";
      }} else if (simTime < DATA.tActualImpact) {{
        statusDot.classList.add("dropped");
        statusText.textContent = "Yük Bırakıldı · Serbest Düşüş";
      }} else {{
        statusDot.classList.add("hit");
        statusText.textContent = "Hedefe Ulaştı";
      }}
    }}

    function renderFrame() {{
      const actState = sampleSeries(DATA.actual, simTime);
      const vacState = sampleSeries(DATA.vacuum, simTime);
      updateTelemetry(actState);
      drawSideCanvas(actState, vacState);
      drawTopCanvas(actState, vacState);
      slider.value = String(Math.min(Math.max(simTime, PRE_ROLL), T_MAX).toFixed(2));
    }}

    function loop(ts) {{
      if (lastTs === null) lastTs = ts;
      const dt = Math.min((ts - lastTs) / 1000, 0.05);
      lastTs = ts;
      windPhase += dt;

      if (isPlaying) {{
        simTime += dt * speedMult;
        if (simTime > T_MAX + POST_DWELL) {{
          simTime = PRE_ROLL;
        }}
      }}
      renderFrame();
      requestAnimationFrame(loop);
    }}

    btnPlay.addEventListener("click", () => {{
      isPlaying = !isPlaying;
      btnPlay.textContent = isPlaying ? "Duraklat" : "Başlat";
    }});

    btnReset.addEventListener("click", () => {{
      simTime = PRE_ROLL;
      isPlaying = true;
      btnPlay.textContent = "Duraklat";
      renderFrame();
    }});

    slider.addEventListener("input", () => {{
      isPlaying = false;
      btnPlay.textContent = "Başlat";
      simTime = parseFloat(slider.value);
      renderFrame();
    }});

    speedBtns.forEach((btn) => {{
      btn.addEventListener("click", () => {{
        speedBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        speedMult = parseFloat(btn.dataset.speed || "1");
      }});
    }});

    window.addEventListener("resize", renderFrame);
    renderFrame();
    requestAnimationFrame(loop);
  </script>
</body>
</html>
"""


def render_live_simulator(scenario: DropScenarioView, palette: ThemePalette) -> None:
    """Streamlit içine senkronize HTML5 canlı simülatör bileşenini yerleştirir."""
    html_doc = build_simulator_html(scenario, palette)
    components.html(html_doc, height=540, scrolling=True)
