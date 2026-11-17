"""Üstten görünüm haritası (Plotly): İHA rotası, rüzgar vektörü, bırakma ve hedef."""

import plotly.graph_objects as go
from src.ui.theme import ThemePalette
from src.visualization.geometry import circle_points, compute_axis_bounds
from src.visualization.schemas import DropScenarioView


def build_topdown_figure(
    scenario: DropScenarioView,
    palette: ThemePalette,
    show_vacuum_reference: bool = False,
) -> go.Figure:
    """Kuşbakışı ENU düzleminde rota, rüzgar ve hedef halkalarını çizer."""
    fig = go.Figure()
    vac = scenario.vacuum_trajectory
    act = scenario.actual_trajectory
    rel = scenario.release_solution.release_point
    tgt = scenario.release_solution.target_point

    (x_min, x_max), (y_min, y_max) = compute_axis_bounds(
        vac if show_vacuum_reference else act,
        act,
        tgt,
    )

    # Hedef çevresi referans halkaları (5 m ve 15 m)
    for radius, dash, label in [(5.0, "solid", "5 m Yarıçap"), (15.0, "dot", "15 m Yarıçap")]:
        cx, cy = circle_points(tgt.x, tgt.y, radius)
        fig.add_trace(
            go.Scatter(
                x=cx,
                y=cy,
                mode="lines",
                name=label,
                showlegend=False,
                line=dict(color=palette.border, width=1.4, dash=dash),
                hoverinfo="skip",
            )
        )

    # İHA yaklaşma hattı
    fig.add_trace(
        go.Scatter(
            x=[p.x for p in scenario.uav_track],
            y=[p.y for p in scenario.uav_track],
            mode="lines",
            name="İHA Rotası",
            line=dict(color=palette.text_secondary, width=2, dash="dot"),
        )
    )

    if show_vacuum_reference:
        fig.add_trace(
            go.Scatter(
                x=vac.x,
                y=vac.y,
                mode="lines",
                name="Sürtünmesiz (Vakum)",
                line=dict(color=palette.reference, width=2.2, dash="dash"),
            )
        )

    # Yük izi
    fig.add_trace(
        go.Scatter(
            x=act.x,
            y=act.y,
            mode="lines",
            name="Yük İzi",
            line=dict(color=palette.accent, width=3.5),
        )
    )

    if show_vacuum_reference:
        vac_label = "" if scenario.drift_from_vacuum_m < 3.0 else "Sürtünmesiz"
        tgt_pos = "top center" if tgt.y >= vac.impact_point.y else "bottom center"
        vac_pos = "bottom center" if vac.impact_point.y <= tgt.y else "top center"
        fig.add_trace(
            go.Scatter(
                x=[rel.x, vac.impact_point.x, tgt.x],
                y=[rel.y, vac.impact_point.y, tgt.y],
                mode="markers+text",
                text=["Bırakma", vac_label, "Hedef"],
                textposition=["top left", vac_pos, tgt_pos],
                marker=dict(
                    size=[11, 9, 12],
                    color=[palette.primary, palette.reference, palette.accent],
                    symbol=["diamond", "circle-open", "x"],
                ),
                showlegend=False,
                hovertemplate="%{text}<br>Doğu: %{x:.1f} m<br>Kuzey: %{y:.1f} m<extra></extra>",
            )
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=[rel.x, tgt.x],
                y=[rel.y, tgt.y],
                mode="markers+text",
                text=["Bırakma", "Hedef"],
                textposition=["top left", "top center"],
                marker=dict(
                    size=[11, 12],
                    color=[palette.primary, palette.accent],
                    symbol=["diamond", "x"],
                ),
                showlegend=False,
                hovertemplate="%{text}<br>Doğu: %{x:.1f} m<br>Kuzey: %{y:.1f} m<extra></extra>",
            )
        )

    # Rüzgar yönü ve şiddeti oku (sol üst köşede temiz gösterge)
    wx, wy = scenario.wind_vector_mps
    w_speed = scenario.inputs.wind_speed_mps
    span = x_max - x_min
    anchor_x = x_min + span * 0.14
    anchor_y = y_max - span * 0.14
    if w_speed > 0.05:
        arrow_len = span * 0.12
        ux, uy = wx / w_speed, wy / w_speed
        fig.add_annotation(
            x=anchor_x + ux * arrow_len,
            y=anchor_y + uy * arrow_len,
            ax=anchor_x,
            ay=anchor_y,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowsize=1.2,
            arrowwidth=2.5,
            arrowcolor=palette.wind_color,
        )
    fig.add_annotation(
        x=anchor_x,
        y=anchor_y - span * 0.06,
        text=f"Rüzgar: {w_speed:.1f} m/s",
        showarrow=False,
        font=dict(size=11, color=palette.wind_color),
        bgcolor=palette.bg_surface,
        bordercolor=palette.border,
        borderwidth=1,
        borderpad=3,
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
            title="Doğu X (m)",
            range=[x_min, x_max],
            gridcolor=palette.grid_line,
            zerolinecolor=palette.border,
        ),
        yaxis=dict(
            title="Kuzey Y (m)",
            range=[y_min, y_max],
            scaleanchor="x",
            scaleratio=1,
            gridcolor=palette.grid_line,
            zerolinecolor=palette.border,
        ),
    )
    return fig
