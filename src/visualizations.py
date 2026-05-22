"""
Visualizations — professional Plotly charts. No emojis.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from src.simulation import generate_drift_series

PALETTE = {
    "critical": "#d93025",
    "warning":  "#f59e0b",
    "normal":   "#16a34a",
    "info":     "#2563eb",
    "neutral":  "#6b7a8d",
    "bg":       "#ffffff",
    "grid":     "#f1f5f9",
    "text":     "#1a2332",
}


def _base_layout(**kwargs) -> dict:
    return dict(
        plot_bgcolor=PALETTE["bg"],
        paper_bgcolor=PALETTE["bg"],
        font=dict(size=11, color=PALETTE["text"], family="Inter, system-ui, sans-serif"),
        margin=dict(l=0, r=0, t=30, b=0),
        **kwargs,
    )


def plot_risk_bar(processes: pd.DataFrame) -> go.Figure:
    if processes.empty or "risk_score" not in processes.columns:
        return go.Figure().update_layout(_base_layout(title="No process data"))

    df     = processes.sort_values("risk_score")
    colors = df["risk_score"].apply(
        lambda s: PALETTE["critical"] if s >= 70 else PALETTE["warning"] if s >= 45 else PALETTE["normal"]
    ).tolist()

    fig = go.Figure(go.Bar(
        x=df["risk_score"], y=df["process"],
        orientation="h", marker_color=colors,
        text=df["risk_score"].astype(int), textposition="outside",
        hovertemplate="<b>%{y}</b><br>Risk index: %{x}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(),
        height=280,
        xaxis=dict(range=[0,115], title="Risk index", showgrid=True, gridcolor=PALETTE["grid"]),
        yaxis=dict(title=""),
    )
    return fig


def plot_risk_radar(chemicals: pd.DataFrame) -> go.Figure:
    cats   = ["Toxicity", "Corrosivity", "Flammability", "Reactivity", "Environmental"]
    colors = px.colors.qualitative.Pastel

    fig = go.Figure()
    for i, (_, row) in enumerate(chemicals.iterrows()):
        base = float(row.get("risk_score", 50))
        vals = [min(base*1.0,100), min(base*0.85,100), min(base*0.5,100),
                min(base*0.75,100), min(base*0.65,100)]
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats + [cats[0]],
            fill="toself", name=row.get("name","")[:20],
            line_color=colors[i % len(colors)], opacity=0.6,
        ))
    fig.update_layout(
        **_base_layout(title="Chemical hazard profile — all materials"),
        polar=dict(radialaxis=dict(visible=True, range=[0,100])),
        height=460,
    )
    return fig


def plot_cim_heatmap(cim: pd.DataFrame) -> go.Figure:
    z = cim.applymap(lambda v: 2 if v=="Y" else 0 if v=="N" else 1)
    fig = go.Figure(go.Heatmap(
        z=z.values, x=cim.columns.tolist(), y=cim.index.tolist(),
        colorscale=[[0,"#dcfce7"],[0.5,"#fef3c7"],[1,"#fee2e2"]],
        text=cim.values, texttemplate="%{text}",
        showscale=False, xgap=2, ygap=2,
        hovertemplate="<b>%{y} + %{x}</b><br>Interaction: %{text}<extra></extra>",
    ))
    fig.update_layout(**_base_layout(), height=320)
    return fig


def plot_deviation_timeline(history: dict, parameters: pd.DataFrame) -> go.Figure:
    colors = [PALETTE["info"], PALETTE["critical"], PALETTE["normal"],
              PALETTE["warning"], "#805ad5", "#d69e2e"]
    fig = go.Figure()
    for i, (p_name, vals) in enumerate(history.items()):
        if len(vals) < 2: continue
        fig.add_trace(go.Scatter(
            x=list(range(len(vals))), y=vals,
            name=p_name[:25],
            line=dict(color=colors[i % len(colors)], width=2),
            mode="lines+markers", marker=dict(size=3),
            hovertemplate=f"<b>{p_name}</b><br>Step %{{x}}<br>Value: %{{y:.3f}}<extra></extra>",
        ))
        row = parameters[parameters["parameter"] == p_name]
        if not row.empty:
            r = row.iloc[0]
            fig.add_hrect(y0=float(r.get("soc_min",0)), y1=float(r.get("soc_max",100)),
                          fillcolor=colors[i % len(colors)], opacity=0.05, line_width=0)

    fig.update_layout(
        **_base_layout(),
        height=280, xaxis_title="Time step", yaxis_title="Value",
        legend=dict(orientation="h", y=-0.35, font_size=10),
        margin=dict(l=40,r=20,t=10,b=60),
        xaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]),
        yaxis=dict(showgrid=True, gridcolor=PALETTE["grid"]),
    )
    return fig


def plot_control_chart(
    current_val: float,
    soc_lo: float, soc_hi: float,
    sol_lo: float, sol_hi: float,
    param_name: str, uom: str,
) -> go.Figure:
    span   = sol_hi - sol_lo if sol_hi > sol_lo else abs(current_val) * 0.2 or 10
    series = generate_drift_series(current_val, span, steps=30, noise_pct=0.03)
    steps  = list(range(len(series)))

    # Point colors
    point_colors = []
    for v in series:
        if not (sol_lo <= v <= sol_hi): point_colors.append(PALETTE["critical"])
        elif not (soc_lo <= v <= soc_hi): point_colors.append(PALETTE["warning"])
        else: point_colors.append(PALETTE["normal"])

    fig = go.Figure()
    fig.add_hrect(y0=sol_lo, y1=sol_hi, fillcolor="rgba(254,243,199,0.35)", line_width=0)
    fig.add_hrect(y0=soc_lo, y1=soc_hi, fillcolor="rgba(220,252,231,0.45)", line_width=0)

    fig.add_trace(go.Scatter(
        x=steps, y=series, mode="lines+markers",
        line=dict(color="#94a3b8", width=1.5),
        marker=dict(color=point_colors, size=6),
        hovertemplate=f"Step %{{x}}<br>Value: %{{y:.3f}} {uom}<extra></extra>",
        showlegend=False,
    ))

    for y, label, col in [(sol_lo,"SOL min","#d97706"),(sol_hi,"SOL max","#d97706"),
                           (soc_lo,"SOC min","#16a34a"),(soc_hi,"SOC max","#16a34a")]:
        fig.add_hline(y=y, line_dash="dot", line_color=col, line_width=1,
                      annotation_text=label, annotation_position="right",
                      annotation_font_size=10)

    fig.update_layout(
        **_base_layout(title=f"Control chart — {param_name}"),
        height=230,
        xaxis=dict(title="Reading number", showgrid=True, gridcolor=PALETTE["grid"]),
        yaxis=dict(title=uom, showgrid=True, gridcolor=PALETTE["grid"]),
    )
    return fig


def plot_risk_matrix(processes: pd.DataFrame, parameters: pd.DataFrame) -> go.Figure:
    hazard_types = ["Toxic", "Corrosive", "Flammable", "Pressure/Temp", "Environmental"]
    if processes.empty or parameters.empty:
        return go.Figure().update_layout(title="No data")

    proc_names = processes["process"].tolist()
    matrix     = np.zeros((len(proc_names), len(hazard_types)))
    for i, proc in enumerate(proc_names):
        params = parameters[parameters["process"] == proc]
        base   = params["risk_score"].mean() if not params.empty else 30
        matrix[i] = [min(base*0.95,100), min(base*0.85,100), min(base*0.5,100),
                     min(base*0.80,100), min(base*0.70,100)]

    fig = go.Figure(go.Heatmap(
        z=matrix, x=hazard_types, y=proc_names,
        colorscale=[[0,"#dcfce7"],[0.35,"#fef9c3"],[0.65,"#fde68a"],[1,"#d93025"]],
        text=np.round(matrix,0).astype(int), texttemplate="%{text}",
        colorbar=dict(title="Risk", thickness=14, len=0.8),
        zmin=0, zmax=100, xgap=2, ygap=2,
        hovertemplate="<b>%{y} — %{x}</b><br>Risk score: %{text}<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(title="Process x hazard type risk matrix"),
        height=max(300, len(proc_names)*55),
    )
    return fig


def plot_bow_tie(param_name: str, top_events: list, consequences: list) -> go.Figure:
    """Simplified bow-tie chart for a given hazard."""
    fig = go.Figure()
    cx, cy = 0.5, 0.5

    # Centre node
    fig.add_shape(type="rect", x0=0.42, x1=0.58, y0=0.42, y1=0.58,
                  fillcolor="#fee2e2", line_color="#d93025", line_width=2)
    fig.add_annotation(x=cx, y=cy, text=f"<b>HAZARD<br>{param_name[:15]}</b>",
                       showarrow=False, font=dict(size=9, color="#7f1d1d"))

    n_top = len(top_events)
    for i, cause in enumerate(top_events):
        fy = (i + 1) / (n_top + 1)
        fig.add_shape(type="line", x0=0.15, y0=fy, x1=0.42, y1=cy,
                      line=dict(color="#94a3b8", width=1.2))
        fig.add_annotation(x=0.08, y=fy, text=cause[:18], showarrow=False,
                           font=dict(size=8), xanchor="center")

    n_con = len(consequences)
    for i, conseq in enumerate(consequences):
        fy = (i + 1) / (n_con + 1)
        fig.add_shape(type="line", x0=0.58, y0=cy, x1=0.85, y1=fy,
                      line=dict(color="#94a3b8", width=1.2))
        fig.add_annotation(x=0.92, y=fy, text=conseq[:18], showarrow=False,
                           font=dict(size=8), xanchor="center")

    fig.update_layout(
        **_base_layout(),
        xaxis=dict(visible=False, range=[0,1]),
        yaxis=dict(visible=False, range=[0,1]),
        height=280,
    )
    return fig
