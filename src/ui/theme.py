"""Oturgan (kahverengi, siyah, beyaz) açık/koyu tema sistemi ve SVG ikonları.

8px tabanlı boşluk sistemi, tek başlık/gövde font çifti ve WCAG AA uyumlu
kontrast değerleri tüm Streamlit bileşenleri ile Plotly/Matplotlib grafiklerinde
ortak kaynak olarak kullanılır.
"""

from dataclasses import dataclass

# 8px tabanlı sabit boşluk ölçeği (px)
SPACE_1 = 8
SPACE_2 = 16
SPACE_3 = 24
SPACE_4 = 32
SPACE_5 = 48
SPACE_6 = 64
SPACE_7 = 96

FONT_HEADING = "'Newsreader', Georgia, 'Times New Roman', serif"
FONT_BODY = "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
FONT_MONO = "'IBM Plex Mono', ui-monospace, SFMono-Regular, monospace"


@dataclass(frozen=True)
class ThemePalette:
    """Açık ve koyu modlar için marka renk paleti."""

    name: str
    is_dark: bool
    bg_page: str
    bg_surface: str
    bg_sidebar: str
    bg_elevated: str
    text_primary: str
    text_secondary: str
    primary: str
    primary_hover: str
    button_text: str
    accent: str
    reference: str
    target_color: str
    wind_color: str
    border: str
    grid_line: str
    shadow: str
    plotly_template: str


LIGHT_PALETTE = ThemePalette(
    name="acik",
    is_dark=False,
    bg_page="#F7F5F2",
    bg_surface="#FFFFFF",
    bg_sidebar="#EFECE6",
    bg_elevated="#F1ECE5",
    text_primary="#171614",
    text_secondary="#595149",
    primary="#5C4033",
    primary_hover="#463026",
    button_text="#FFFFFF",
    accent="#9E5629",
    reference="#2B2825",
    target_color="#171614",
    wind_color="#7A563E",
    border="#DDD5CA",
    grid_line="#E6E0D8",
    shadow="0 4px 16px rgba(92, 64, 51, 0.08)",
    plotly_template="plotly_white",
)

DARK_PALETTE = ThemePalette(
    name="koyu",
    is_dark=True,
    bg_page="#121110",
    bg_surface="#1B1917",
    bg_sidebar="#161412",
    bg_elevated="#24201C",
    text_primary="#F3EFEA",
    text_secondary="#B5ACA2",
    primary="#C49A74",
    primary_hover="#D4AE8B",
    button_text="#171614",
    accent="#D98348",
    reference="#E5DFD7",
    target_color="#F3EFEA",
    wind_color="#B88E68",
    border="#332C26",
    grid_line="#2A241F",
    shadow="0 6px 20px rgba(0, 0, 0, 0.45)",
    plotly_template="plotly_dark",
)


def get_palette(mode: str) -> ThemePalette:
    """Seçilen tema adına göre ilgili paleti döner."""
    return DARK_PALETTE if mode == "koyu" else LIGHT_PALETTE


_SVG_ICONS: dict[str, str] = {
    "target": (
        '<circle cx="12" cy="12" r="9"/>'
        '<circle cx="12" cy="12" r="4"/>'
        '<line x1="12" y1="2" x2="12" y2="5"/>'
        '<line x1="12" y1="19" x2="12" y2="22"/>'
        '<line x1="2" y1="12" x2="5" y2="12"/>'
        '<line x1="19" y1="12" x2="22" y2="12"/>'
    ),
    "wind": (
        '<path d="M3 8h11a3 3 0 1 0-3-3"/>'
        '<path d="M3 12h15a3 3 0 1 1-3 3"/>'
        '<path d="M3 16h8"/>'
    ),
    "trajectory": (
        '<path d="M3 6c7 0 12 4 15 13"/>'
        '<circle cx="3" cy="6" r="1.5"/>'
        '<circle cx="18" cy="19" r="1.5"/>'
    ),
    "aircraft": (
        '<path d="M3 12h18"/>'
        '<path d="M13 5l5 7-5 7"/>'
        '<path d="M6 9l3 3-3 3"/>'
    ),
    "download": (
        '<path d="M12 3v12"/>'
        '<path d="M7 11l5 5 5-5"/>'
        '<path d="M4 20h16"/>'
    ),
    "sun": (
        '<circle cx="12" cy="12" r="4"/>'
        '<line x1="12" y1="2" x2="12" y2="4"/>'
        '<line x1="12" y1="20" x2="12" y2="22"/>'
        '<line x1="4.93" y1="4.93" x2="6.34" y2="6.34"/>'
        '<line x1="17.66" y1="17.66" x2="19.07" y2="19.07"/>'
        '<line x1="2" y1="12" x2="4" y2="12"/>'
        '<line x1="20" y1="12" x2="22" y2="12"/>'
        '<line x1="6.34" y1="17.66" x2="4.93" y2="19.07"/>'
        '<line x1="19.07" y1="4.93" x2="17.66" y2="6.34"/>'
    ),
    "moon": '<path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/>',
}


def svg_icon(name: str, color: str = "currentColor", size: int = 18) -> str:
    """Aynı outline ailesinden (1.75px çizgi) satır içi SVG ikonu üretir."""
    paths = _SVG_ICONS.get(name, _SVG_ICONS["target"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.75" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align: -0.18em; flex-shrink: 0;">{paths}</svg>'
    )


def build_theme_css(palette: ThemePalette) -> str:
    """Streamlit sayfasına uygulanacak özel CSS stil bloğunu oluşturur."""
    return f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap');

      :root, body {{
        --bg-page: {palette.bg_page};
        --bg-surface: {palette.bg_surface};
        --bg-sidebar: {palette.bg_sidebar};
        --bg-elevated: {palette.bg_elevated};
        --text-primary: {palette.text_primary};
        --text-secondary: {palette.text_secondary};
        --primary: {palette.primary};
        --primary-hover: {palette.primary_hover};
        --accent: {palette.accent};
        --border: {palette.border};
        --shadow: {palette.shadow};
      }}

      .stApp {{
        background-color: var(--bg-page);
        color: var(--text-primary);
        font-family: {FONT_BODY};
      }}

      header[data-testid="stHeader"] {{
        background-color: transparent;
      }}

      .block-container {{
        padding-top: {SPACE_4}px;
        padding-bottom: {SPACE_5}px;
        padding-left: {SPACE_4}px;
        padding-right: {SPACE_4}px;
        max-width: 1440px;
      }}

      section[data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar);
        border-right: 1px solid var(--border);
        color: var(--text-primary);
      }}

      section[data-testid="stSidebar"] label,
      section[data-testid="stSidebar"] p,
      section[data-testid="stSidebar"] span,
      section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"],
      [data-testid="stRadio"] label span,
      [data-testid="stRadio"] p {{
        color: var(--text-primary);
      }}

      section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"],
      section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] p {{
        color: var(--text-secondary) !important;
      }}

      [data-testid="stSlider"] [data-testid="stTickBarMin"],
      [data-testid="stSlider"] [data-testid="stTickBarMax"],
      [data-testid="stSlider"] [data-testid="stThumbValue"] {{
        color: var(--text-secondary) !important;
      }}

      [data-testid="stNumberInputContainer"],
      [data-testid="stNumberInput"] [data-baseweb="input"],
      [data-testid="stNumberInput"] [data-baseweb="base-input"],
      [data-testid="stNumberInput"] input {{
        background-color: var(--bg-surface) !important;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        border-color: var(--border) !important;
      }}

      [data-testid="stNumberInputStepDown"],
      [data-testid="stNumberInputStepUp"] {{
        background-color: var(--bg-elevated) !important;
        color: var(--text-primary) !important;
        border-color: var(--border) !important;
      }}

      [data-testid="stNumberInputStepDown"] svg,
      [data-testid="stNumberInputStepUp"] svg {{
        fill: var(--text-primary) !important;
        stroke: var(--text-primary) !important;
      }}

      [data-testid="stSelectbox"] [data-baseweb="select"] > div,
      [data-testid="stSelectbox"] [data-baseweb="select"] div,
      [data-testid="stSelectbox"] [data-baseweb="select"] span {{
        background-color: var(--bg-surface) !important;
        color: var(--text-primary) !important;
        border-color: var(--border) !important;
      }}

      [data-testid="stSelectbox"] svg {{
        fill: var(--text-primary) !important;
      }}

      div[data-baseweb="popover"],
      div[data-baseweb="popover"] ul,
      div[data-baseweb="popover"] li[role="option"] {{
        background-color: var(--bg-surface) !important;
        color: var(--text-primary) !important;
      }}

      div[data-baseweb="popover"] li[role="option"]:hover,
      div[data-baseweb="popover"] li[role="option"][aria-selected="true"] {{
        background-color: var(--bg-elevated) !important;
        color: var(--primary) !important;
      }}

      [data-testid="stExpander"] {{
        background-color: var(--bg-surface);
        border: 1px solid var(--border);
        border-radius: 8px;
      }}

      [data-testid="stExpander"] summary,
      [data-testid="stExpander"] summary span {{
        color: var(--text-primary);
      }}

      section[data-testid="stSidebar"] .block-container {{
        padding: {SPACE_3}px {SPACE_2}px;
      }}

      h1, h2, h3, .celebi-title {{
        font-family: {FONT_HEADING};
        color: var(--text-primary);
        letter-spacing: -0.015em;
      }}

      h1 {{ font-size: 2.25rem; line-height: 1.15; margin-bottom: {SPACE_1}px; }}
      h2 {{ font-size: 1.5rem; line-height: 1.25; margin-bottom: {SPACE_2}px; }}
      h3 {{ font-size: 1.125rem; line-height: 1.3; margin-bottom: {SPACE_1}px; }}

      p, span, label, div {{
        font-family: {FONT_BODY};
      }}

      .celebi-header {{
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: flex-end;
        gap: {SPACE_2}px;
        padding-bottom: {SPACE_3}px;
        margin-bottom: {SPACE_3}px;
        border-bottom: 1px solid var(--border);
      }}

      .celebi-kicker {{
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--primary);
        margin-bottom: {SPACE_1}px;
      }}

      .celebi-subtitle {{
        font-size: 0.95rem;
        color: var(--text-secondary);
        margin: 0;
        max-width: 68ch;
      }}

      .celebi-badge {{
        display: inline-flex;
        align-items: center;
        gap: {SPACE_1}px;
        padding: {SPACE_1}px {SPACE_2}px;
        border-radius: 6px;
        border: 1px solid var(--border);
        background-color: var(--bg-surface);
        color: var(--text-secondary);
        font-size: 0.8125rem;
        font-weight: 500;
        box-shadow: var(--shadow);
      }}

      .celebi-card {{
        background-color: var(--bg-surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: {SPACE_3}px;
        box-shadow: var(--shadow);
        transition: border-color 0.18s ease, transform 0.18s ease;
      }}

      .celebi-card:hover {{
        border-color: var(--primary);
        transform: translateY(-1px);
      }}

      .celebi-card-featured {{
        border-left: 4px solid var(--accent);
        background-color: var(--bg-surface);
      }}

      .celebi-metric-label {{
        display: flex;
        align-items: center;
        gap: {SPACE_1}px;
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text-secondary);
        margin-bottom: {SPACE_1}px;
      }}

      .celebi-metric-value {{
        font-family: {FONT_BODY};
        font-variant-numeric: tabular-nums;
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.15;
      }}

      .celebi-metric-note {{
        font-size: 0.8125rem;
        color: var(--text-secondary);
        margin-top: {SPACE_1}px;
      }}

      .celebi-section-head {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: {SPACE_2}px;
        margin-top: {SPACE_4}px;
        margin-bottom: {SPACE_2}px;
        padding-bottom: {SPACE_1}px;
        border-bottom: 1px solid var(--border);
      }}

      .celebi-mono {{
        font-family: {FONT_MONO};
        font-variant-numeric: tabular-nums;
      }}

      .stTabs [data-baseweb="tab-list"] {{
        gap: {SPACE_2}px;
        border-bottom: 1px solid var(--border);
      }}

      .stTabs [data-baseweb="tab"] {{
        padding: {SPACE_1}px {SPACE_2}px;
        border-radius: 6px 6px 0 0;
        color: var(--text-secondary);
        font-weight: 500;
        transition: color 0.18s ease, background-color 0.18s ease;
      }}

      .stTabs [data-baseweb="tab"]:hover {{
        color: var(--text-primary);
        background-color: var(--bg-elevated);
      }}

      .stTabs [aria-selected="true"] {{
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary) !important;
      }}

      .stDownloadButton > button, .stButton > button {{
        border-radius: 6px;
        border: 1px solid var(--primary);
        background-color: var(--primary);
        color: {palette.button_text};
        font-weight: 500;
        padding: {SPACE_1}px {SPACE_2}px;
        transition: background-color 0.18s ease, border-color 0.18s ease;
      }}

      .stDownloadButton > button:hover, .stButton > button:hover {{
        background-color: var(--primary-hover);
        border-color: var(--primary-hover);
        color: {palette.button_text};
      }}

      @media (max-width: 768px) {{
        .block-container {{
          padding: {SPACE_2}px;
        }}
        h1 {{ font-size: 1.75rem; }}
        .celebi-metric-value {{ font-size: 1.4rem; }}
      }}
    </style>
    """
