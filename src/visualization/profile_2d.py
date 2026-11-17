"""Yandan düşüş profili (Plotly): İrtifa - rota mesafesi ve bırakma uzaklığı."""

import plotly.graph_objects as go
from src.ui.theme import ThemePalette
from src.visualization.geometry import format_lead_distance, project_along_heading
from src.visualization.schemas import DropScenarioView


def build_side_profile_figure(
    scenario: DropScenarioView,
    palette: ThemePalette,
    show_vacuum_reference: bool = False,
) -> go.Figure:
    """İHA uçuş ekseni boyunca yandan düşüş profilini ve kaç metre önce bırakıldığını çizer."""
    fig = go.Figure()
    rel = scenario.release_solution.release_point
    tgt = scenario.release_solution.target_point
    heading = scenario.inputs.uav_heading_deg

    vac_s = project_along_heading(scenario.vacuum_trajectory.x, scenario.vacuum_trajectory.y, rel, heading)
    act_s = project_along_heading(scenario.actual_trajectory.x, scenario.actual_trajectory.y, rel, heading)
    tgt_s = project_along_heading((tgt.x,), (tgt.y,), rel, heading)[0]
    track_s = project_along_heading(
        tuple(p.x for p in scenario.uav_track),
        tuple(p.y for p in scenario.uav_track),
        rel,
        heading,
    )

    # İHA uçuş hattı
    fig.add_trace(
        go.Scatter(
            x=track_s,
            y=[p.z for p in scenario.uav_track],
            mode="lines",
            name="İHA Uçuş İrtifası",
            line=dict(color=palette.text_secondary, width=2, dash="dot"),
        )
    )

    if show_vacuum_reference:
        fig.add_trace(
            go.Scatter(
                x=vac_s,
                y=scenario.vacuum_trajectory.z,
                mode="lines",
                name="Sürtünmesiz (Vakum)",
                line=dict(color=palette.reference, width=2.5, dash="dash"),
                hovertemplate="Rota Mesafesi: %{x:.1f} m<br>İrtifa: %{y:.1f} m<extra>Sürtünmesiz</extra>",
            )
        )

    # Yük yörüngesi
    fig.add_trace(
        go.Scatter(
            x=act_s,
            y=scenario.actual_trajectory.z,
            mode="lines",
            name="Yük Yörüngesi",
            line=dict(color=palette.accent, width=3.5),
            hovertemplate="Rota Mesafesi: %{x:.1f} m<br>İrtifa: %{y:.1f} m<extra>Yük Yörüngesi</extra>",
        )
    )

    # Bırakma noktası & düşey referans
    fig.add_shape(
        type="line",
        x0=0.0,
        y0=0.0,
        x1=0.0,
        y1=rel.z,
        line=dict(color=palette.primary, width=1.5, dash="dash"),
    )

    if show_vacuum_reference:
        vac_gap_s = abs(vac_s[-1] - tgt_s)
        vac_text = "" if vac_gap_s < 3.0 else "Sürtünmesiz Düşüş"
        marker_positions = (
            ["top right", "top left", "top right"]
            if vac_s[-1] >= tgt_s
            else ["top right", "top right", "top left"]
        )
        fig.add_trace(
            go.Scatter(
                x=[0.0, tgt_s, vac_s[-1]],
                y=[rel.z, 0.0, 0.0],
                mode="markers+text",
                text=["Bırakma", "Hedef", vac_text],
                textposition=marker_positions,
                marker=dict(
                    size=[11, 11, 9],
                    color=[palette.primary, palette.accent, palette.reference],
                    symbol=["diamond", "x", "circle-open"],
                ),
                showlegend=False,
                hovertemplate="%{text}<br>Mesafe: %{x:.1f} m<br>İrtifa: %{y:.1f} m<extra></extra>",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=[0.0, tgt_s],
                y=[rel.z, 0.0],
                mode="markers+text",
                text=["Bırakma", "Hedef"],
                textposition=["top right", "top center"],
                marker=dict(
                    size=[11, 11],
                    color=[palette.primary, palette.accent],
                    symbol=["diamond", "x"],
                ),
                showlegend=False,
                hovertemplate="%{text}<br>Mesafe: %{x:.1f} m<br>İrtifa: %{y:.1f} m<extra></extra>",
            )
        )

    # 7.3 Bırakma mesafesi ölçüm oku (zemin seviyesinin hemen altında/üstünde)
    lead_y = max(rel.z * 0.08, 4.0)
    fig.add_annotation(
        x=tgt_s,
        y=lead_y,
        ax=0.0,
        ay=lead_y,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.1,
        arrowwidth=2,
        arrowcolor=palette.primary,
    )
    fig.add_annotation(
        x=0.5 * tgt_s,
        y=lead_y,
        text=format_lead_distance(scenario.release_solution.lead_distance_m),
        showarrow=False,
        yshift=14,
        font=dict(size=12, color=palette.primary),
        bgcolor=palette.bg_surface,
        bordercolor=palette.border,
        borderwidth=1,
        borderpad=4,
    )

    fig.update_layout(
        template=palette.plotly_template,
        paper_bgcolor=palette.bg_surface,
        plot_bgcolor=palette.bg_page,
        font=dict(family="IBM Plex Sans, sans-serif", color=palette.text_primary, size=12),
        margin=dict(l=16, r=16, t=36, b=16),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0, bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(
            title="Rota Boyunca Yatay Mesafe (m)",
            gridcolor=palette.grid_line,
            zerolinecolor=palette.border,
        ),
        yaxis=dict(
            title="İrtifa (m)",
            gridcolor=palette.grid_line,
            zerolinecolor=palette.border,
            rangemode="tozero",
        ),
    )
    return fig
