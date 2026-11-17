"""Kenar çubuğu için sürüklenebilir 2 boyutlu yön kadranı ve senkronize manuel derece girişi."""

from typing import Literal
import streamlit as st
from src.ui.theme import FONT_BODY, FONT_MONO, ThemePalette

_DIAL_CSS = f"""
.dial-card {{
  border: 1px solid var(--dial-border);
  background: var(--dial-surface);
  border-radius: 8px;
  padding: 10px 12px;
  font-family: {FONT_BODY};
  color: var(--dial-text);
  user-select: none;
}}
.dial-head {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}}
.dial-label {{
  font-size: 0.84rem;
  font-weight: 500;
  color: var(--dial-text);
}}
.dial-readout {{
  font-family: {FONT_MONO};
  font-variant-numeric: tabular-nums;
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--dial-primary);
}}
.dial-stage {{
  display: flex;
  justify-content: center;
  align-items: center;
}}
.dial-svg {{
  width: 176px;
  height: 176px;
  touch-action: none;
  cursor: grab;
}}
.dial-svg.dragging {{
  cursor: grabbing;
}}
.dial-cardinal {{
  cursor: pointer;
  font-family: {FONT_BODY};
  font-size: 10.5px;
  font-weight: 600;
}}
.dial-sub {{
  margin-top: 4px;
  font-size: 0.75rem;
  line-height: 1.35;
  color: var(--dial-muted);
  text-align: center;
}}
"""

_DIAL_JS = """
const COMPASS_NAMES = ["Kuzey", "KD", "Doğu", "GD", "Güney", "GB", "Batı", "KB"];

function cardinalLabel(deg) {
  const idx = Math.round(((deg % 360) + 360) % 360 / 45) % 8;
  return COMPASS_NAMES[idx];
}

function angleFromPointer(svg, clientX, clientY, step) {
  const rect = svg.getBoundingClientRect();
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  const dx = clientX - cx;
  const dy = clientY - cy;
  const raw = (Math.atan2(dx, -dy) * 180) / Math.PI;
  const snapped = Math.round(raw / step) * step;
  return ((snapped % 360) + 360) % 360;
}

export default function(component) {
  const { data, setTriggerValue, parentElement } = component;
  const root = parentElement.querySelector("#dial-root");
  if (!root || !data) return;

  const p = data.palette;
  const mode = data.mode || "uav";
  let currentAngle = ((Math.round(data.angle ?? 0) % 360) + 360) % 360;

  root.style.setProperty("--dial-surface", p.surface);
  root.style.setProperty("--dial-page", p.page);
  root.style.setProperty("--dial-text", p.text);
  root.style.setProperty("--dial-muted", p.muted);
  root.style.setProperty("--dial-primary", p.primary);
  root.style.setProperty("--dial-accent", p.accent);
  root.style.setProperty("--dial-border", p.border);

  let ticks = "";
  for (let a = 0; a < 360; a += 15) {
    const isMajor = a % 45 === 0;
    const r1 = isMajor ? 69 : 73;
    const r2 = 79;
    const rad = (a * Math.PI) / 180;
    const x1 = 110 + r1 * Math.sin(rad);
    const y1 = 110 - r1 * Math.cos(rad);
    const x2 = 110 + r2 * Math.sin(rad);
    const y2 = 110 - r2 * Math.cos(rad);
    ticks += `<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${isMajor ? p.muted : p.border}" stroke-width="${isMajor ? 1.6 : 1}" />`;
  }

  // Rüzgar modunda kalın ok seçili 'estiği yön' tarafından merkeze doğru eser;
  // böylece imleçle tutulan ok yönü asla ters yöne zıplamaz.
  const centerGraphic = mode === "uav"
    ? `<g id="centerRotor" transform="rotate(${currentAngle} 110 110)">
         <line x1="110" y1="110" x2="110" y2="33" stroke="${p.primary}" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.75" />
         <path d="M110 82 L116 99 L136 111 L136 117 L116 112 L114 127 L123 134 L123 138 L110 134 L97 138 L97 134 L106 127 L104 112 L84 117 L84 111 L104 99 Z"
               fill="${p.primary}" stroke="${p.surface}" stroke-width="1.4" stroke-linejoin="round" />
       </g>`
    : `<g id="centerRotor" transform="rotate(${currentAngle} 110 110)">
         <line x1="110" y1="36" x2="110" y2="95" stroke="${p.accent}" stroke-width="3.2" stroke-linecap="round" />
         <polygon points="110,104 102,89 118,89" fill="${p.accent}" />
         <line x1="110" y1="118" x2="110" y2="152" stroke="${p.accent}" stroke-width="1.6" stroke-dasharray="3 3" opacity="0.55" />
         <polygon points="110,158 106,148 114,148" fill="${p.accent}" opacity="0.55" />
         <circle cx="110" cy="110" r="4.5" fill="${p.surface}" stroke="${p.accent}" stroke-width="2" />
       </g>`;

  root.innerHTML = `
    <div class="dial-card">
      <div class="dial-head">
        <span class="dial-label">${data.label}</span>
        <span id="dialReadout" class="dial-readout">${currentAngle}° · ${cardinalLabel(currentAngle)}</span>
      </div>
      <div class="dial-stage">
        <svg id="dialSvg" class="dial-svg" viewBox="0 0 220 220" aria-label="${data.label}">
          <circle cx="110" cy="110" r="79" fill="${p.page}" stroke="${p.border}" stroke-width="1.5" />
          <circle cx="110" cy="110" r="50" fill="none" stroke="${p.border}" stroke-width="1" stroke-dasharray="2 3" />
          ${ticks}
          <text class="dial-cardinal" data-deg="0" x="110" y="18" text-anchor="middle" fill="${p.text}">0° K</text>
          <text class="dial-cardinal" data-deg="90" x="205" y="114" text-anchor="middle" fill="${p.text}">90° D</text>
          <text class="dial-cardinal" data-deg="180" x="110" y="210" text-anchor="middle" fill="${p.text}">180° G</text>
          <text class="dial-cardinal" data-deg="270" x="16" y="114" text-anchor="middle" fill="${p.text}">270° B</text>
          ${centerGraphic}
          <g id="knobGroup" transform="rotate(${currentAngle} 110 110)">
            <circle cx="110" cy="31" r="7.5" fill="${mode === "uav" ? p.primary : p.accent}" stroke="${p.surface}" stroke-width="2" />
          </g>
        </svg>
      </div>
      <div id="dialSub" class="dial-sub">${data.subtitle || ""}</div>
    </div>
  `;

  const svg = root.querySelector("#dialSvg");
  const rotor = root.querySelector("#centerRotor");
  const knob = root.querySelector("#knobGroup");
  const readout = root.querySelector("#dialReadout");
  const cardinals = root.querySelectorAll(".dial-cardinal");

  function applyAngleVisual(deg) {
    currentAngle = deg;
    rotor.setAttribute("transform", `rotate(${deg} 110 110)`);
    knob.setAttribute("transform", `rotate(${deg} 110 110)`);
    readout.textContent = `${deg}° · ${cardinalLabel(deg)}`;
  }

  let dragging = false;

  const onMove = (ev) => {
    if (!dragging) return;
    const step = ev.shiftKey ? 1 : 5;
    applyAngleVisual(angleFromPointer(svg, ev.clientX, ev.clientY, step));
  };

  const onUp = (ev) => {
    if (!dragging) return;
    dragging = false;
    svg.classList.remove("dragging");
    const step = ev.shiftKey ? 1 : 5;
    const finalAngle = angleFromPointer(svg, ev.clientX, ev.clientY, step);
    applyAngleVisual(finalAngle);
    setTriggerValue("picked", finalAngle);
  };

  svg.addEventListener("pointerdown", (ev) => {
    if (ev.target && ev.target.classList && ev.target.classList.contains("dial-cardinal")) {
      return;
    }
    dragging = true;
    svg.classList.add("dragging");
    if (svg.setPointerCapture) {
      try { svg.setPointerCapture(ev.pointerId); } catch (_) {}
    }
    const step = ev.shiftKey ? 1 : 5;
    applyAngleVisual(angleFromPointer(svg, ev.clientX, ev.clientY, step));
  });

  svg.addEventListener("pointermove", onMove);
  svg.addEventListener("pointerup", onUp);
  svg.addEventListener("pointercancel", onUp);

  cardinals.forEach((el) => {
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const deg = parseInt(el.getAttribute("data-deg") || "0", 10);
      applyAngleVisual(deg);
      setTriggerValue("picked", deg);
    });
  });

  return () => {
    dragging = false;
  };
}
"""

_DIRECTION_DIAL = st.components.v2.component(
    "celebi_direction_dial",
    html='<div id="dial-root"></div>',
    css=_DIAL_CSS,
    js=_DIAL_JS,
)


def compass_direction_name(deg: float) -> str:
    """Dereceyi kısa pusula yönü adına (Kuzey, KD, Doğu...) çevirir."""
    names = ("Kuzey", "Kuzeydoğu", "Doğu", "Güneydoğu", "Güney", "Güneybatı", "Batı", "Kuzeybatı")
    idx = round((deg % 360.0) / 45.0) % 8
    return names[idx]


def render_direction_dial(
    key: str,
    label: str,
    mode: Literal["uav", "wind"],
    default_angle: int,
    palette: ThemePalette,
    subtitle: str = "",
) -> int:
    """2 boyutlu döndürülebilir kadranı ve senkronize manuel derece kutusunu sunar."""
    deg_key = f"{key}_deg"
    num_key = f"{key}_num"

    if deg_key not in st.session_state:
        st.session_state[deg_key] = int(default_angle) % 360
    if num_key not in st.session_state:
        st.session_state[num_key] = int(st.session_state[deg_key]) % 360

    def _on_num_change() -> None:
        val = int(st.session_state.get(num_key, default_angle)) % 360
        st.session_state[deg_key] = val

    def _on_dial_picked() -> None:
        comp_state = st.session_state.get(key)
        if comp_state is not None and "picked" in comp_state and comp_state["picked"] is not None:
            val = int(round(float(comp_state["picked"]))) % 360
            st.session_state[deg_key] = val
            st.session_state[num_key] = val

    current = int(st.session_state[deg_key]) % 360

    _DIRECTION_DIAL(
        key=key,
        data={
            "mode": mode,
            "angle": current,
            "label": label,
            "subtitle": subtitle,
            "palette": {
                "surface": palette.bg_surface,
                "page": palette.bg_page,
                "text": palette.text_primary,
                "muted": palette.text_secondary,
                "primary": palette.primary,
                "accent": palette.accent,
                "border": palette.border,
            },
        },
        on_picked_change=_on_dial_picked,
    )

    st.number_input(
        f"{label} — Manuel Giriş (°)",
        min_value=0,
        max_value=359,
        step=1,
        key=num_key,
        on_change=_on_num_change,
    )
    return int(st.session_state[deg_key]) % 360
