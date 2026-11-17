"""3D etkileşimli yörünge grafiği (Plotly): Vakum vs. sürtünmeli+rüzgarlı düşüş."""

import plotly.graph_objects as go
from src.ui.theme import ThemePalette
from src.visualization.geometry import compute_axis_bounds
from src.visualization.schemas import DropScenarioView, TrajectorySeries


def _trajectory_hover_text(series: TrajectorySeries) -> list[str]:
    return [
        (
            f"<b>{series.label}</b><br>"
            f"t: {t:.2f} s<br>"
            f"Doğu (X): {x:.1f} m<br>"
            f"Kuzey (Y): {y:.1f} m<br>"
            f"İrtifa (Z): {z:.1f} m<br>"
            f"Hız: {spd:.1f} m/s"
        )
        for x, y, z, t, spd in zip(series.x, series.y, series.z, series.t, series.speed)
    ]


def build_3d_figure(
    scenario: DropScenarioView,
    palette: ThemePalette,
    show_vacuum_reference: bool | None = None,
) -> go.Figure:
    """3B ENU uzayında yörünge, bırakma noktası ve hedef/düşüş noktasını çizer."""
    show_vac = (scenario.scenario_mode == "7.2") if show_vacuum_reference is None else show_vacuum_reference
    impact_label = (
        "Hedef"
        if scenario.scenario_mode == "7.3"
        else ("7.2 Düşüş" if scenario.scenario_mode == "7.2" else "7.1 Düşüş")
    )

    fig = go.Figure()
    vac = scenario.vacuum_trajectory
    act = scenario.actual_trajectory
    rel = scenario.release_solution.release_point
    tgt = scenario.release_solution.target_point

    # İHA uçuş rotası
    fig.add_trace(
        go.Scatter3d(
            x=[p.x for p in scenario.uav_track],
            y=[p.y for p in scenario.uav_track],
            z=[p.z for p in scenario.uav_track],
            mode="lines",
            name="İHA Rotası",
            line=dict(color=palette.text_secondary, width=3, dash="dot"),
            hovertemplate="İHA Uçuş Hattı<br>İrtifa: %{z:.1f} m<extra></extra>",
        )
    )

    # İsteğe bağlı sürtünmesiz (7.1) referans eğrisi
    if show_vac:
        fig.add_trace(
            go.Scatter3d(
                x=vac.x,
                y=vac.y,
                z=vac.z,
                mode="lines",
                name=vac.label,
                line=dict(color=palette.reference, width=3, dash="dash"),
                text=_trajectory_hover_text(vac),
                hoverinfo="text",
            )
        )

    # Yük yörüngesi
    fig.add_trace(
        go.Scatter3d(
            x=act.x,
            y=act.y,
            z=act.z,
            mode="lines",
            name=act.label,
            line=dict(color=palette.accent, width=5),
            text=_trajectory_hover_text(act),
            hoverinfo="text",
        )
    )

    # Yerdeki iz düşümü (3B derinlik algısı için)
    fig.add_trace(
        go.Scatter3d(
            x=act.x,
            y=act.y,
            z=[0.0] * len(act.x),
            mode="lines",
            name="Yörünge Zemin İzdüşümü",
            line=dict(color=palette.primary, width=2, dash="dot"),
            opacity=0.45,
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Bırakma noktasından zemine dikey kılavuz çizgisi
    fig.add_trace(
        go.Scatter3d(
            x=[rel.x, rel.x],
            y=[rel.y, rel.y],
            z=[rel.z, 0.0],
            mode="lines",
            name="Bırakma Düşey Hattı",
            line=dict(color=palette.primary, width=2, dash="dash"),
            opacity=0.65,
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Kritik noktalar
    fig.add_trace(
        go.Scatter3d(
            x=[rel.x],
            y=[rel.y],
            z=[rel.z],
            mode="markers",
            name="Bırakma Noktası",
            showlegend=False,
            marker=dict(size=7, color=palette.primary, symbol="diamond"),
            hovertemplate=(
                f"<b>Bırakma Noktası</b><br>"
                f"X: {rel.x:.1f} m, Y: {rel.y:.1f} m, Z: {rel.z:.1f} m<extra></extra>"
            ),
        )
    )

    if show_vac:
        fig.add_trace(
            go.Scatter3d(
                x=[vac.impact_point.x],
                y=[vac.impact_point.y],
                z=[0.0],
                mode="markers",
                name="Sürtünmesiz Düşüş",
                showlegend=False,
                marker=dict(size=6, color=palette.reference, symbol="circle-open", line=dict(width=2)),
                hovertemplate=(
                    f"<b>7.1 Vakum Düşüş Noktası</b><br>"
                    f"X: {vac.impact_point.x:.1f} m, Y: {vac.impact_point.y:.1f} m<extra></extra>"
                ),
            )
        )

    fig.add_trace(
        go.Scatter3d(
            x=[tgt.x],
            y=[tgt.y],
            z=[0.0],
            mode="markers",
            name=impact_label,
            showlegend=False,
            marker=dict(size=8, color=palette.accent, symbol="x"),
            hovertemplate=(
                f"<b>{impact_label}</b><br>"
                f"X: {tgt.x:.1f} m, Y: {tgt.y:.1f} m<extra></extra>"
            ),
        )
    )

    axis_style = dict(
        backgroundcolor=palette.bg_page,
        gridcolor=palette.grid_line,
        zerolinecolor=palette.border,
        showbackground=True,
        color=palette.text_secondary,
    )

    (x_min, x_max), (y_min, y_max) = compute_axis_bounds(
        vac if show_vac else act,
        act,
        tgt,
    )

    fig.update_layout(
        template=palette.plotly_template,
        paper_bgcolor=palette.bg_surface,
        plot_bgcolor=palette.bg_surface,
        font=dict(family="IBM Plex Sans, sans-serif", color=palette.text_primary, size=12),
        margin=dict(l=8, r=8, t=36, b=8),
        height=520,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0.0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
        ),
        scene=dict(
            xaxis=dict(title="Doğu X (m)", range=[x_min, x_max], **axis_style),
            yaxis=dict(title="Kuzey Y (m)", range=[y_min, y_max], **axis_style),
            zaxis=dict(title="İrtifa Z (m)", range=[0.0, max(rel.z * 1.08, 10.0)], **axis_style),
            aspectmode="manual",
            aspectratio=dict(x=1.25, y=1.1, z=0.85),
            camera=dict(eye=dict(x=1.45, y=-1.55, z=0.85)),
        ),
    )
    return fig
