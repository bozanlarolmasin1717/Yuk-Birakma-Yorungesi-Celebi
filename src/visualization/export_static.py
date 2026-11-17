"""Raporlama ve arşivleme için statik yüksek çözünürlüklü Matplotlib dışa aktarıcısı."""

from io import BytesIO
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.ui.theme import ThemePalette
from src.visualization.geometry import (
    circle_points,
    compute_axis_bounds,
    format_lead_distance,
    project_along_heading,
)
from src.visualization.schemas import DropScenarioView


def _style_axis(ax: plt.Axes, palette: ThemePalette) -> None:
    ax.set_facecolor(palette.bg_page)
    ax.tick_params(colors=palette.text_secondary, labelsize=8.5)
    ax.xaxis.label.set_color(palette.text_primary)
    ax.yaxis.label.set_color(palette.text_primary)
    ax.title.set_color(palette.text_primary)
    for spine in ax.spines.values():
        spine.set_color(palette.border)
    ax.grid(True, color=palette.grid_line, linewidth=0.7, alpha=0.8)


def _style_legend(ax: plt.Axes, palette: ThemePalette, loc: str) -> None:
    legend = ax.legend(
        loc=loc,
        fontsize=7.5,
        frameon=True,
        facecolor=palette.bg_surface,
        edgecolor=palette.border,
        labelcolor=palette.text_primary,
    )
    legend.get_frame().set_alpha(0.92)


def export_summary_figure_bytes(
    scenario: DropScenarioView,
    palette: ThemePalette,
    fmt: str = "png",
    show_vacuum_reference: bool = False,
) -> bytes:
    """3 panelli (3B Yörünge, Yandan Profil, Kuşbakışı) statik rapor görseli üretir."""
    vac = scenario.vacuum_trajectory
    act = scenario.actual_trajectory
    rel = scenario.release_solution.release_point
    tgt = scenario.release_solution.target_point

    fig = plt.figure(figsize=(15, 5.2), dpi=220, facecolor=palette.bg_surface)
    fig.suptitle(
        (
            f"Çelebi 7.3 Hedefleme Analizi  |  "
            f"{format_lead_distance(scenario.release_solution.lead_distance_m)}  |  "
            f"Yanal kayma: {scenario.release_solution.lateral_offset_m:+.1f} m"
        ),
        color=palette.text_primary,
        fontsize=12,
        fontweight="bold",
        y=0.98,
    )

    # 1) 3D panel
    (x_min, x_max), (y_min, y_max) = compute_axis_bounds(
        vac if show_vacuum_reference else act,
        act,
        tgt,
    )
    ax3d = fig.add_subplot(1, 3, 1, projection="3d", facecolor=palette.bg_surface)
    if show_vacuum_reference:
        ax3d.plot(vac.x, vac.y, vac.z, linestyle="--", color=palette.reference, linewidth=1.6, label="Sürtünmesiz")
    ax3d.plot(act.x, act.y, act.z, color=palette.accent, linewidth=2.4, label="Yük Yörüngesi")
    ax3d.scatter([rel.x], [rel.y], [rel.z], color=palette.primary, marker="D", s=36, label="Bırakma")
    ax3d.scatter([tgt.x], [tgt.y], [0.0], color=palette.accent, marker="x", s=45, label="Hedef")
    ax3d.set_xlim(x_min, x_max)
    ax3d.set_ylim(y_min, y_max)
    ax3d.set_zlim(0.0, max(rel.z * 1.08, 10.0))
    for axis in (ax3d.xaxis, ax3d.yaxis, ax3d.zaxis):
        axis.pane.set_facecolor(palette.bg_page)
        axis.pane.set_edgecolor(palette.border)
        axis._axinfo["grid"]["color"] = palette.grid_line
    ax3d.set_title("3B Yörünge", color=palette.text_primary, fontsize=10, pad=8)
    ax3d.set_xlabel("Doğu (m)", fontsize=8, color=palette.text_primary)
    ax3d.set_ylabel("Kuzey (m)", fontsize=8, color=palette.text_primary)
    ax3d.set_zlabel("İrtifa (m)", fontsize=8, color=palette.text_primary)
    ax3d.tick_params(colors=palette.text_secondary, labelsize=7.5)
    _style_legend(ax3d, palette, "upper right")

    # 2) Yandan profil paneli
    ax_side = fig.add_subplot(1, 3, 2)
    _style_axis(ax_side, palette)
    heading = scenario.inputs.uav_heading_deg
    vac_s = project_along_heading(vac.x, vac.y, rel, heading)
    act_s = project_along_heading(act.x, act.y, rel, heading)
    tgt_s = project_along_heading((tgt.x,), (tgt.y,), rel, heading)[0]

    if show_vacuum_reference:
        ax_side.plot(vac_s, vac.z, linestyle="--", color=palette.reference, linewidth=1.6, label="Sürtünmesiz")
    ax_side.plot(act_s, act.z, color=palette.accent, linewidth=2.4, label="Yük Yörüngesi")
    ax_side.scatter([0.0, tgt_s], [rel.z, 0.0], color=[palette.primary, palette.accent], zorder=5)
    ax_side.vlines(0.0, 0.0, rel.z, colors=palette.primary, linestyles="dotted", linewidth=1.2)
    ax_side.set_title("Yandan Profil (İrtifa – Menzil)", fontsize=10)
    ax_side.set_xlabel("Rota Mesafesi (m)", fontsize=8.5)
    ax_side.set_ylabel("İrtifa (m)", fontsize=8.5)
    ax_side.set_ylim(bottom=0.0)
    _style_legend(ax_side, palette, "upper right")

    # 3) Kuşbakışı harita paneli
    ax_top = fig.add_subplot(1, 3, 3)
    _style_axis(ax_top, palette)
    cx5, cy5 = circle_points(tgt.x, tgt.y, 5.0)
    cx15, cy15 = circle_points(tgt.x, tgt.y, 15.0)
    ax_top.plot(cx5, cy5, color=palette.border, linewidth=1.0)
    ax_top.plot(cx15, cy15, color=palette.border, linestyle=":", linewidth=1.0)
    if show_vacuum_reference:
        ax_top.plot(vac.x, vac.y, linestyle="--", color=palette.reference, linewidth=1.5, label="Sürtünmesiz")
    ax_top.plot(act.x, act.y, color=palette.accent, linewidth=2.4, label="Yük İzi")
    ax_top.scatter([rel.x], [rel.y], color=palette.primary, marker="D", s=38, zorder=5, label="Bırakma")
    ax_top.scatter([tgt.x], [tgt.y], color=palette.accent, marker="x", s=50, zorder=5, label="Hedef")
    ax_top.set_xlim(x_min, x_max)
    ax_top.set_ylim(y_min, y_max)
    ax_top.set_aspect("equal", adjustable="box")
    ax_top.set_title("Üstten Görünüm (Doğu – Kuzey)", fontsize=10)
    ax_top.set_xlabel("Doğu X (m)", fontsize=8.5)
    ax_top.set_ylabel("Kuzey Y (m)", fontsize=8.5)
    _style_legend(ax_top, palette, "lower right")

    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.93))
    buffer = BytesIO()
    fig.savefig(buffer, format=fmt, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return buffer.getvalue()
