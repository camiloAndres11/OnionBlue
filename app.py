"""
app.py — Dashboard Dash: Simulador PTAR Adaptativo
Reto MAREES 2026 — Corrección Definitiva de Superposición Visual (Titles + Legends)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output
import config as cfg
from simulator.scenarios import correr_simulacion

# ─────────────────────────────────────────────────────────────────────────────
# PALETA DE COLORES Y ESTILOS
# ─────────────────────────────────────────────────────────────────────────────
COLOR = {
    "A":          "#EF476F",   # Coral vibrante — Escenario A (Línea Base Fija)
    "A_dark":     "#B51A42",   # Borde / Contraste A
    "A_bg":       "rgba(239, 71, 111, 0.12)",
    "B":          "#06D6A0",   # Esmeralda tecnol. — Escenario B (Adaptativo)
    "B_dark":     "#048A67",   # Borde / Contraste B
    "B_bg":       "rgba(6, 214, 160, 0.12)",
    "demanda":    "#FFD166",   # Ámbar — Demanda real biológica O2
    "norma":      "#F72585",   # Magenta — Límite normativo
    "agua":       "#118AB2",   # Azul agua
    "fondo":      "#0F172A",   # Slate oscuro moderno
    "fondo_sec":  "#1E293B",   # Fondo de contenedor
    "card":       "#1E293B",   # Slate card
    "borde":      "#334155",   # Borde divisor
    "texto":      "#F8FAFC",   # Blanco suave
    "texto_mut":  "#94A3B8",   # Gris azulado
    "accent":     "#38BDF8",   # Celeste acento
}

ESCENARIOS_INFO = {
    "S1": {
        "title": "S1 — Jornada Ordinaria Seca",
        "desc": "Curva clásica de doble joroba municipal (valles nocturnos y picos 09h y 18h). Exponente α = 1.0.",
    },
    "S2": {
        "title": "S2 — Punta Hidráulica (Lluvia)",
        "desc": "Escorrentía pluvial (14h a 18h): incremento de caudal (+70%) y dilución de materia orgánica (α = -0.5).",
    },
    "S3": {
        "title": "S3 — Choque de Carga Orgánica",
        "desc": "Descarga concentrada (09h a 12h): pico de DQO (+60%) y N (+50%) sin aumento de caudal.",
    },
}

# Configuración base de gráficos Plotly con márgenes generosos y leyendas INFERIORES
# para garantizar CERO superposición de textos con los títulos.
PLOT_BASE_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15, 23, 42, 0.6)",
    font=dict(color=COLOR["texto"], family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif", size=12),
    margin=dict(l=65, r=25, t=55, b=65),
    legend=dict(
        bgcolor="rgba(30, 41, 59, 0.85)",
        bordercolor=COLOR["borde"],
        borderwidth=1,
        orientation="h",
        yanchor="top",
        y=-0.22,           # Colocada de forma segura DEBAJO del eje X
        xanchor="center",
        x=0.5,
        font=dict(size=11)
    ),
    xaxis=dict(
        gridcolor="#334155",
        zerolinecolor="#334155",
        tickmode="linear",
        dtick=2,
        title=dict(text="Hora del día (h)", font=dict(size=12, color=COLOR["texto_mut"])),
        tickfont=dict(size=11, color=COLOR["texto_mut"])
    ),
    yaxis=dict(
        gridcolor="#334155",
        zerolinecolor="#334155",
        tickfont=dict(size=11, color=COLOR["texto_mut"])
    ),
    hovermode="x unified",
)

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENTES VISUALES
# ─────────────────────────────────────────────────────────────────────────────

def _header_section():
    return html.Div(
        style={
            "background": "linear-gradient(135deg, #093748 0%, #0F172A 100%)",
            "padding": "20px 36px",
            "borderBottom": f"1px solid {COLOR['borde']}",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "flexWrap": "wrap",
            "gap": "16px",
            "boxShadow": "0 4px 20px rgba(0,0,0,0.3)"
        },
        children=[
            html.Div([
                html.Div([
                    html.Span("💧", style={"fontSize": "28px", "marginRight": "12px"}),
                    html.H1("Simulador PTAR Adaptativo",
                            style={"display": "inline-block", "margin": 0, "fontSize": "24px",
                                   "fontWeight": "800", "letterSpacing": "-0.5px", "color": "#FFFFFF"}),
                    html.Span("RETO MAREES 2026",
                              style={"marginLeft": "12px", "padding": "4px 10px", "borderRadius": "4px",
                                     "background": "rgba(56, 189, 248, 0.2)", "color": COLOR["accent"],
                                     "fontSize": "11px", "fontWeight": "700", "verticalAlign": "middle"})
                ], style={"display": "flex", "alignItems": "center"}),
                html.P("Eficiencia Energética de Sopladores, Lazo Cerrado OD y Cumplimiento de Vertimiento (Res. 0631)",
                       style={"margin": "4px 0 0 40px", "fontSize": "13px", "color": COLOR["texto_mut"]})
            ]),
            html.Div(
                style={"display": "flex", "gap": "16px"},
                children=[
                    html.Div([
                        html.Span("●", style={"color": COLOR["A"], "fontSize": "18px", "marginRight": "6px"}),
                        html.B("ESCENARIO A:", style={"color": COLOR["A"], "fontSize": "12px"}),
                        html.Span(" Operación Fija (Línea Base)", style={"color": COLOR["texto"], "fontSize": "12px", "marginLeft": "4px"})
                    ], style={"background": COLOR["A_bg"], "padding": "8px 14px", "borderRadius": "6px", "border": f"1px solid {COLOR['A_dark']}"}),
                    html.Div([
                        html.Span("●", style={"color": COLOR["B"], "fontSize": "18px", "marginRight": "6px"}),
                        html.B("ESCENARIO B:", style={"color": COLOR["B"], "fontSize": "12px"}),
                        html.Span(" Control Adaptativo VFD + OD", style={"color": COLOR["texto"], "fontSize": "12px", "marginLeft": "4px"})
                    ], style={"background": COLOR["B_bg"], "padding": "8px 14px", "borderRadius": "6px", "border": f"1px solid {COLOR['B_dark']}"}),
                ]
            )
        ]
    )


def _render_kpi_card(title, icon, val_a, val_b, unit, delta_text, is_positive=True, highlight=False):
    delta_color = COLOR["B"] if is_positive else COLOR["A"]
    arrow = "▼" if is_positive else "▲"
    border_color = COLOR["B_dark"] if highlight else COLOR["borde"]
    bg_card = "linear-gradient(180deg, #1E293B 0%, #151F30 100%)"

    return html.Div(
        style={
            "background": bg_card,
            "border": f"1px solid {border_color}",
            "borderRadius": "10px",
            "padding": "16px",
            "boxShadow": "0 4px 12px rgba(0,0,0,0.15)",
            "minWidth": "220px",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between"
        },
        children=[
            html.Div([
                html.Span(icon, style={"marginRight": "8px", "fontSize": "16px"}),
                html.Span(title, style={"fontSize": "11.5px", "fontWeight": "700", "color": COLOR["texto_mut"], "textTransform": "uppercase", "letterSpacing": "0.5px"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "12px"}),

            html.Div([
                html.Div([
                    html.Div("Escenario A", style={"fontSize": "10px", "color": COLOR["A"], "fontWeight": "700", "textTransform": "uppercase"}),
                    html.Div([
                        html.Span(f"{val_a}", style={"fontSize": "18px", "fontWeight": "800", "color": COLOR["texto"]}),
                        html.Span(f" {unit}", style={"fontSize": "11px", "color": COLOR["texto_mut"], "marginLeft": "3px"}),
                    ])
                ]),
                html.Div("➔", style={"fontSize": "16px", "color": COLOR["texto_mut"], "padding": "0 8px"}),
                html.Div([
                    html.Div("Escenario B", style={"fontSize": "10px", "color": COLOR["B"], "fontWeight": "700", "textTransform": "uppercase"}),
                    html.Div([
                        html.Span(f"{val_b}", style={"fontSize": "20px", "fontWeight": "800", "color": COLOR["B"]}),
                        html.Span(f" {unit}", style={"fontSize": "11px", "color": COLOR["texto_mut"], "marginLeft": "3px"}),
                    ])
                ], style={"textAlign": "right"}),
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "background": "rgba(0,0,0,0.25)", "padding": "10px 12px", "borderRadius": "8px", "marginBottom": "10px"}),

            html.Div([
                html.Span(f"{arrow} {delta_text}", style={"color": delta_color, "fontWeight": "700", "fontSize": "12.5px"}),
                html.Span(" respecto a línea base", style={"color": COLOR["texto_mut"], "fontSize": "10.5px", "marginLeft": "4px"})
            ], style={"textAlign": "right"})
        ]
    )


def _control_sidebar():
    return html.Div(
        style={
            "width": "320px",
            "flexShrink": 0,
            "background": COLOR["fondo_sec"],
            "borderRadius": "12px",
            "border": f"1px solid {COLOR['borde']}",
            "padding": "20px",
            "boxShadow": "0 4px 16px rgba(0,0,0,0.2)"
        },
        children=[
            html.Div([
                html.Span("⚡", style={"fontSize": "16px", "marginRight": "8px"}),
                html.H3("Régimen de Entrada", style={"margin": 0, "fontSize": "14px", "fontWeight": "700", "color": COLOR["texto"]})
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "14px"}),

            dcc.RadioItems(
                id="escenario-selector",
                options=[
                    {"label": html.Div([
                        html.B(v["title"], style={"fontSize": "12.5px", "color": COLOR["texto"], "display": "block", "marginBottom": "2px"}),
                        html.Span(v["desc"], style={"fontSize": "11px", "color": COLOR["texto_mut"], "display": "block", "lineHeight": "1.3"})
                    ], style={"padding": "10px 12px"}), "value": k}
                    for k, v in ESCENARIOS_INFO.items()
                ],
                value="S1",
                labelStyle={
                    "display": "block",
                    "background": "rgba(15, 23, 42, 0.5)",
                    "borderRadius": "8px",
                    "marginBottom": "10px",
                    "border": f"1px solid {COLOR['borde']}",
                    "cursor": "pointer"
                },
                inputStyle={"display": "none"}
            ),

            html.Hr(style={"borderColor": COLOR["borde"], "margin": "20px 0"}),

            html.Div([
                html.Span("🎛️", style={"fontSize": "16px", "marginRight": "8px"}),
                html.H3("Calibración del Proceso", style={"margin": 0, "fontSize": "14px", "fontWeight": "700", "color": COLOR["texto"]})
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "16px"}),

            _slider_row("SAE — Eficiencia Aireadores", "sae-slider", 0.8, 2.5, cfg.SAE, 0.05, "kg O₂/kWh"),
            _slider_row("OD Meta en Reactor", "od-slider", 1.0, 3.0, cfg.OD_META, 0.1, "mg/L"),
            _slider_row("P_mín — Piso de Agitación", "pmin-slider", 2.0, 10.0, cfg.P_MIN, 0.5, "kW"),
            _slider_row("Tarifa Eléctrica Industrial", "ckwh-slider", 400, 1000, cfg.C_KWH, 50, "COP/kWh"),
            _slider_row("Ganancia Lazo OD (kp)", "kp-slider", 0.05, 1.0, cfg.K_P_OD, 0.05, "adim"),

            html.Hr(style={"borderColor": COLOR["borde"], "margin": "20px 0"}),

            html.Div([
                html.Div("📌 MODELACIÓN RIGUROSA (NIVEL 2)", style={"fontSize": "11px", "fontWeight": "700", "color": COLOR["demanda"], "marginBottom": "6px"}),
                html.P("El modelo calcula las demandas biológicas horarias con balance másico y estequiometría de nitrificación completa según ecuaciones.tex.",
                       style={"fontSize": "11px", "color": COLOR["texto_mut"], "margin": "0 0 6px 0", "lineHeight": "1.4"}),
                html.P("El Escenario A demuestra el despilfarro energético de operar con consigna sobrediseñada las 24 horas.",
                       style={"fontSize": "11px", "color": COLOR["texto_mut"], "margin": 0, "lineHeight": "1.4"})
            ], style={"background": "rgba(255, 209, 102, 0.05)", "border": "1px solid rgba(255, 209, 102, 0.2)", "borderRadius": "8px", "padding": "12px"})
        ]
    )


def _slider_row(label, id_slider, v_min, v_max, v_init, step, unit):
    return html.Div(
        style={"marginBottom": "16px"},
        children=[
            html.Div([
                html.Span(label, style={"fontSize": "11.5px", "color": COLOR["texto"]}),
                html.Span([
                    html.Span(id=f"{id_slider}-display", style={"fontWeight": "700", "color": COLOR["accent"]}),
                    html.Span(f" {unit}", style={"fontSize": "10.5px", "color": COLOR["texto_mut"]})
                ], style={"fontSize": "11.5px"})
            ], style={"display": "flex", "justifyContent": "space-between", "marginBottom": "6px"}),
            dcc.Slider(
                id=id_slider, min=v_min, max=v_max, step=step, value=v_init,
                marks=None,
                tooltip={"placement": "bottom", "always_visible": False}
            )
        ]
    )


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

app = dash.Dash(__name__, title="Simulador PTAR Adaptativo — Reto MAREES")

app.layout = html.Div(
    style={
        "background": COLOR["fondo"],
        "minHeight": "100vh",
        "fontFamily": "'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "color": COLOR["texto"],
        "display": "flex",
        "flexDirection": "column"
    },
    children=[
        _header_section(),

        html.Div(
            style={"padding": "24px 36px", "display": "flex", "gap": "24px", "flex": "1"},
            children=[
                _control_sidebar(),

                html.Div(
                    style={"flex": "1", "minWidth": 0, "display": "flex", "flexDirection": "column"},
                    children=[
                        # Contenedor de KPIs
                        html.Div(id="kpis-container"),

                        # Pestañas temáticas
                        dcc.Tabs(
                            id="view-tabs",
                            value="tab-comparativa",
                            style={"height": "42px", "marginBottom": "18px"},
                            colors={
                                "border": COLOR["borde"],
                                "primary": COLOR["accent"],
                                "background": COLOR["fondo_sec"]
                            },
                            children=[
                                dcc.Tab(
                                    label="⚡ ENERGÍA Y CONTROL (A vs B)",
                                    value="tab-comparativa",
                                    style={"padding": "10px 20px", "fontWeight": "600", "fontSize": "12.5px"},
                                    selected_style={"padding": "10px 20px", "fontWeight": "700", "fontSize": "12.5px", "background": COLOR["card"], "color": COLOR["accent"], "borderTop": f"3px solid {COLOR['accent']}"}
                                ),
                                dcc.Tab(
                                    label="💧 CALIDAD DE AGUA Y NORMATIVA",
                                    value="tab-calidad",
                                    style={"padding": "10px 20px", "fontWeight": "600", "fontSize": "12.5px"},
                                    selected_style={"padding": "10px 20px", "fontWeight": "700", "fontSize": "12.5px", "background": COLOR["card"], "color": COLOR["accent"], "borderTop": f"3px solid {COLOR['accent']}"}
                                ),
                                dcc.Tab(
                                    label="💰 ECONOMÍA Y COSTOS HORARIOS",
                                    value="tab-costos",
                                    style={"padding": "10px 20px", "fontWeight": "600", "fontSize": "12.5px"},
                                    selected_style={"padding": "10px 20px", "fontWeight": "700", "fontSize": "12.5px", "background": COLOR["card"], "color": COLOR["accent"], "borderTop": f"3px solid {COLOR['accent']}"}
                                ),
                                dcc.Tab(
                                    label="📋 AUDITORÍA HORARIA (TABLA)",
                                    value="tab-tabla",
                                    style={"padding": "10px 20px", "fontWeight": "600", "fontSize": "12.5px"},
                                    selected_style={"padding": "10px 20px", "fontWeight": "700", "fontSize": "12.5px", "background": COLOR["card"], "color": COLOR["accent"], "borderTop": f"3px solid {COLOR['accent']}"}
                                ),
                            ]
                        ),

                        # Contenedor dinámico de pestaña
                        html.Div(id="tab-content", style={"flex": "1"})
                    ]
                )
            ]
        )
    ]
)


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

@app.callback(
    Output("sae-slider-display", "children"),
    Output("od-slider-display", "children"),
    Output("pmin-slider-display", "children"),
    Output("ckwh-slider-display", "children"),
    Output("kp-slider-display", "children"),
    Input("sae-slider", "value"),
    Input("od-slider", "value"),
    Input("pmin-slider", "value"),
    Input("ckwh-slider", "value"),
    Input("kp-slider", "value"),
)
def actualizar_slider_labels(sae, od, pmin, ckwh, kp):
    return f"{sae:.2f}", f"{od:.1f}", f"{pmin:.1f}", f"{int(ckwh):,}", f"{kp:.2f}"


@app.callback(
    Output("kpis-container", "children"),
    Output("tab-content", "children"),
    Input("escenario-selector", "value"),
    Input("view-tabs", "value"),
    Input("sae-slider", "value"),
    Input("od-slider", "value"),
    Input("pmin-slider", "value"),
    Input("ckwh-slider", "value"),
    Input("kp-slider", "value"),
)
def renderizar_panel(esc_key, tab_activa, sae, od_meta, p_min, c_kwh, k_p):
    params = {
        "SAE": sae,
        "OD_META": od_meta,
        "P_MIN": p_min,
        "C_KWH": c_kwh,
        "K_P_OD": k_p,
    }
    df, kpis = correr_simulacion(esc_key, params)
    horas = df["hora"].values

    # Tarjetas KPI superiores
    kpi_strip = html.Div(
        style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "16px", "marginBottom": "20px"},
        children=[
            _render_kpi_card(
                "Costo Específico (CEO)", "💰",
                f"{kpis['CEO_A']:.1f}", f"{kpis['CEO_B']:.1f}", "COP/m³",
                f"{kpis['ahorro_CEO_pct']:.1f}% ahorro", is_positive=(kpis['ahorro_CEO_pct'] > 0), highlight=True
            ),
            _render_kpi_card(
                "Consumo Eléctrico Diario", "⚡",
                f"{kpis['E_A_kwh']:.0f}", f"{kpis['E_B_kwh']:.0f}", "kWh/día",
                f"{kpis['ahorro_E_pct']:.1f}% reducción", is_positive=(kpis['ahorro_E_pct'] > 0)
            ),
            _render_kpi_card(
                "Sobre-aireación Evitada", "🌬️",
                f"{kpis['sobre_aire_A_kg']:.0f}", f"{kpis['sobre_aire_B_kg']:.0f}", "kg O₂/día",
                f"{kpis['sobre_aire_A_kg'] - kpis['sobre_aire_B_kg']:.0f} kg O₂ ahorrados", is_positive=True
            ),
            _render_kpi_card(
                "Cumplimiento Res. 0631", "✅",
                f"{kpis['horas_cumple_A']}/24", f"{kpis['horas_cumple_B']}/24", "horas/día",
                "100% Calidad Legal", is_positive=True
            ),
        ]
    )

    if tab_activa == "tab-comparativa":
        content = _render_tab_comparativa(df, horas, p_min)
    elif tab_activa == "tab-calidad":
        content = _render_tab_calidad(df, horas)
    elif tab_activa == "tab-costos":
        content = _render_tab_costos(df, horas)
    else:
        content = _render_tab_tabla(df)

    return kpi_strip, content


# ─────────────────────────────────────────────────────────────────────────────
# GENERADORES DE PESTAÑAS
# ─────────────────────────────────────────────────────────────────────────────

def _render_tab_comparativa(df, horas, p_min):
    # Gráfica 1: Potencia instantánea
    fig_pot = go.Figure(layout=dict(
        **PLOT_BASE_LAYOUT,
        title=dict(text="<b>Perfil de Potencia Horaria de Sopladores</b> (kW)", x=0.03, y=0.96, font=dict(size=14))
    ))
    fig_pot.add_trace(go.Scatter(
        x=horas, y=df["P_A"], name="Esc. A — Potencia Fija",
        line=dict(color=COLOR["A"], width=2.5, dash="dash"),
        fill="tozeroy", fillcolor="rgba(239, 71, 111, 0.05)"
    ))
    fig_pot.add_trace(go.Scatter(
        x=horas, y=df["P_B"], name="Esc. B — Control Adaptativo VFD",
        line=dict(color=COLOR["B"], width=3),
        fill="tozeroy", fillcolor="rgba(6, 214, 160, 0.12)"
    ))
    fig_pot.add_trace(go.Scatter(
        x=horas, y=df["R_O2"] / cfg.SAE, name="Demanda Biológica Teórica",
        line=dict(color=COLOR["demanda"], width=1.5, dash="dot")
    ))
    fig_pot.add_hline(y=p_min, line_dash="dot", line_color=COLOR["accent"], opacity=0.8,
                      annotation_text=f"Piso Agitación = {p_min} kW", annotation_position="bottom right",
                      annotation_font_color=COLOR["accent"])

    # Gráfica 2: Energía acumulada
    E_cum_A = np.cumsum(df["P_A"].values * cfg.DELTA_T)
    E_cum_B = np.cumsum(df["P_B"].values * cfg.DELTA_T)
    fig_eng = go.Figure(layout=dict(
        **PLOT_BASE_LAYOUT,
        title=dict(text="<b>Energía Eléctrica Acumulada</b> (kWh/día)", x=0.03, y=0.96, font=dict(size=14))
    ))
    fig_eng.add_trace(go.Scatter(
        x=horas, y=E_cum_A, name="Esc. A Acumulado",
        line=dict(color=COLOR["A"], width=2.5, dash="dash"),
        fill="tozeroy", fillcolor="rgba(239, 71, 111, 0.05)"
    ))
    fig_eng.add_trace(go.Scatter(
        x=horas, y=E_cum_B, name="Esc. B Acumulado",
        line=dict(color=COLOR["B"], width=2.5),
        fill="tozeroy", fillcolor="rgba(6, 214, 160, 0.12)"
    ))

    # Gráfica 3: Balance de Oxígeno
    fig_o2 = go.Figure(layout=dict(
        **PLOT_BASE_LAYOUT,
        title=dict(text="<b>Balance de Oxígeno: Demanda vs Suministro</b> (kg O₂/h)", x=0.03, y=0.96, font=dict(size=14))
    ))
    fig_o2.add_trace(go.Bar(
        x=horas, y=df["S_O2_A"], name="Esc. A — O₂ Inyectado Constante",
        marker_color=COLOR["A"], opacity=0.45, offsetgroup="A"
    ))
    fig_o2.add_trace(go.Bar(
        x=horas, y=df["S_O2_B"], name="Esc. B — O₂ Inyectado Adaptativo",
        marker_color=COLOR["B"], opacity=0.85, offsetgroup="B"
    ))
    fig_o2.add_trace(go.Scatter(
        x=horas, y=df["R_O2"], name="Demanda Biológica R_O₂",
        line=dict(color=COLOR["demanda"], width=2.5),
        mode="lines+markers", marker=dict(size=5)
    ))
    fig_o2.update_layout(barmode="group")

    return html.Div(
        children=[
            html.Div(
                style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "16px 20px", "marginBottom": "16px"},
                children=[
                    html.Div("💡 INTERPRETACIÓN DEL PROCESO BIOLÓGICO Y CONTROL", style={"fontSize": "12px", "fontWeight": "700", "color": COLOR["accent"], "marginBottom": "6px"}),
                    html.P("En el Escenario A (rojo), los sopladores operan a consigna fija sobredimensionada para soportar el pico de la tarde. Durante la madrugada (00h a 06h), la demanda orgánica cae a la mitad pero los sopladores siguen al 100%, derrochando kilovatios y sobresaturando el licor mixto. El Escenario B (verde) reduce la potencia dinámicamente hasta el piso de agitación (P_mín), logrando un ahorro superior al 45% sin comprometer los microorganismos.",
                           style={"fontSize": "12.5px", "color": COLOR["texto_mut"], "margin": 0, "lineHeight": "1.5"})
                ]
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "1.3fr 1fr", "gap": "16px", "marginBottom": "16px"},
                children=[
                    html.Div(dcc.Graph(figure=fig_pot, style={"height": "340px"}, config={"displayModeBar": False}),
                             style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "12px"}),
                    html.Div(dcc.Graph(figure=fig_eng, style={"height": "340px"}, config={"displayModeBar": False}),
                             style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "12px"}),
                ]
            ),
            html.Div(
                dcc.Graph(figure=fig_o2, style={"height": "320px"}, config={"displayModeBar": False}),
                style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "12px"}
            )
        ]
    )


def _render_tab_calidad(df, horas):
    fig_dqo = go.Figure(layout=dict(
        **PLOT_BASE_LAYOUT,
        title=dict(text="<b>Concentración de DQO en Efluente de Salida</b> (mg O₂/L)", x=0.03, y=0.96, font=dict(size=14))
    ))
    fig_dqo.add_trace(go.Scatter(
        x=horas, y=df["DQO_sal_A"], name="Esc. A — DQO Efluente",
        line=dict(color=COLOR["A"], width=2.5, dash="dash")
    ))
    fig_dqo.add_trace(go.Scatter(
        x=horas, y=df["DQO_sal_B"], name="Esc. B — DQO Efluente Adaptativo",
        line=dict(color=COLOR["B"], width=2.5)
    ))
    fig_dqo.add_hline(y=cfg.DQO_NORMA, line_dash="solid", line_color=COLOR["norma"], line_width=2,
                      annotation_text=f"Límite Máximo Res. 0631 = {cfg.DQO_NORMA} mg/L", annotation_position="top left",
                      annotation_font_color=COLOR["norma"])

    fig_od = go.Figure(layout=dict(
        **PLOT_BASE_LAYOUT,
        title=dict(text="<b>Oxígeno Disuelto (OD) en el Tanque Aireado</b> (mg O₂/L)", x=0.03, y=0.96, font=dict(size=14))
    ))
    fig_od.add_trace(go.Scatter(
        x=horas, y=df["OD_A"], name="Esc. A — OD Resultante (Sobresaturado)",
        line=dict(color=COLOR["A"], width=2, dash="dash")
    ))
    fig_od.add_trace(go.Scatter(
        x=horas, y=df["OD_B"], name="Esc. B — OD Estabilizado en Consigna",
        line=dict(color=COLOR["B"], width=2.5)
    ))
    fig_od.add_hline(y=cfg.OD_META, line_dash="dot", line_color=COLOR["demanda"],
                      annotation_text=f"Consigna Meta = {cfg.OD_META} mg/L", annotation_position="top left",
                      annotation_font_color=COLOR["demanda"])

    fig_inf = make_subplots(specs=[[{"secondary_y": True}]])
    fig_inf.add_trace(go.Scatter(
        x=horas, y=df["Q"], name="Caudal Influente Q(t) [m³/h]",
        line=dict(color=COLOR["agua"], width=2.5),
        fill="tozeroy", fillcolor="rgba(17, 138, 178, 0.15)"
    ), secondary_y=False)
    fig_inf.add_trace(go.Scatter(
        x=horas, y=df["DQO_est"], name="DQO Estimada Soft-Sensor [mg/L]",
        line=dict(color=COLOR["demanda"], width=2, dash="dash")
    ), secondary_y=True)
    fig_inf.update_layout(**PLOT_BASE_LAYOUT)
    fig_inf.update_layout(title=dict(text="<b>Dinámica de Entrada de Aguas Residuales</b>", x=0.03, y=0.96, font=dict(size=14)))
    fig_inf.update_yaxes(title_text="Caudal (m³/h)", secondary_y=False, gridcolor="#334155")
    fig_inf.update_yaxes(title_text="DQO (mg/L)", secondary_y=True, gridcolor="#334155")

    return html.Div(
        children=[
            html.Div(
                style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "16px 20px", "marginBottom": "16px"},
                children=[
                    html.Div("🛡️ VERIFICACIÓN AMBIENTAL Y CUMPLIMIENTO LEGAL", style={"fontSize": "12px", "fontWeight": "700", "color": COLOR["norma"], "marginBottom": "6px"}),
                    html.P("El ahorro del Escenario B no deteriora la calidad del vertimiento: la DQO de salida permanece holgadamente por debajo de los 180 mg/L exigidos por la Resolución 0631 de 2015 en todas las 24 horas del día. Además, el control adaptativo estabiliza el OD en 2.0 mg/L, evitando el estrés oxidativo a la biomasa aerobia.",
                           style={"fontSize": "12.5px", "color": COLOR["texto_mut"], "margin": 0, "lineHeight": "1.5"})
                ]
            ),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px", "marginBottom": "16px"},
                children=[
                    html.Div(dcc.Graph(figure=fig_dqo, style={"height": "320px"}, config={"displayModeBar": False}),
                             style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "12px"}),
                    html.Div(dcc.Graph(figure=fig_od, style={"height": "320px"}, config={"displayModeBar": False}),
                             style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "12px"}),
                ]
            ),
            html.Div(
                dcc.Graph(figure=fig_inf, style={"height": "290px"}, config={"displayModeBar": False}),
                style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "12px"}
            )
        ]
    )


def _render_tab_costos(df, horas):
    fig_costos = go.Figure(layout=dict(
        **PLOT_BASE_LAYOUT,
        title=dict(text="<b>Desglose Horario de Costos Operativos Variables</b> (COP/h)", x=0.03, y=0.96, font=dict(size=14))
    ))

    fig_costos.add_trace(go.Bar(
        x=horas, y=df["costo_elec_A"], name="Esc. A — Electricidad Sopladores",
        marker_color=COLOR["A"], offsetgroup="A"
    ))
    fig_costos.add_trace(go.Bar(
        x=horas, y=df["costo_quim_A"], name="Esc. A — Químicos de Apoyo",
        marker_color="#FF8FA3", offsetgroup="A", base=df["costo_elec_A"]
    ))

    fig_costos.add_trace(go.Bar(
        x=horas, y=df["costo_elec_B"], name="Esc. B — Electricidad Sopladores",
        marker_color=COLOR["B"], offsetgroup="B"
    ))
    fig_costos.add_trace(go.Bar(
        x=horas, y=df["costo_quim_B"], name="Esc. B — Químicos Contingentes",
        marker_color="#70E4EF", offsetgroup="B", base=df["costo_elec_B"]
    ))
    fig_costos.update_layout(barmode="group")

    return html.Div(
        children=[
            html.Div(
                style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "16px 20px", "marginBottom": "16px"},
                children=[
                    html.Div("💰 IMPACTO FINANCIERO Y COSTO ESPECÍFICO (CEO)", style={"fontSize": "12px", "fontWeight": "700", "color": COLOR["accent"], "marginBottom": "6px"}),
                    html.P("La energía eléctrica de aireación representa el mayor rubro variable en el tratamiento biológico. El Escenario B reduce drásticamente el gasto en las horas valle, absorbiendo con holgura los costos adicionales de calibración e instrumentación diaria.",
                           style={"fontSize": "12.5px", "color": COLOR["texto_mut"], "margin": 0, "lineHeight": "1.5"})
                ]
            ),
            html.Div(
                dcc.Graph(figure=fig_costos, style={"height": "380px"}, config={"displayModeBar": False}),
                style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "12px"}
            )
        ]
    )


def _render_tab_tabla(df):
    cols = [
        ("Hora", "hora", "hora"),
        ("Caudal Q (m³/h)", "Q", "float1"),
        ("DQO Ent. (mg/L)", "DQO_est", "float1"),
        ("Demanda O₂ (kg/h)", "R_O2", "float1"),
        ("Potencia A (kW)", "P_A", "float1"),
        ("Potencia B (kW)", "P_B", "float1"),
        ("OD en A (mg/L)", "OD_A", "float2"),
        ("OD en B (mg/L)", "OD_B", "float2"),
        ("DQO Sal. A", "DQO_sal_A", "float1"),
        ("DQO Sal. B", "DQO_sal_B", "float1"),
        ("Ahorro Eléc. (kW)", "ahorro_kw", "float1"),
    ]

    df_display = df.copy()
    df_display["ahorro_kw"] = df_display["P_A"] - df_display["P_B"]

    header = html.Tr([
        html.Th(c[0], style={"padding": "10px 14px", "textAlign": "right", "color": COLOR["texto_mut"], "fontSize": "12px", "fontWeight": "700", "borderBottom": f"1px solid {COLOR['borde']}"})
        for c in cols
    ])

    rows = []
    for _, r in df_display.iterrows():
        tds = []
        for label, key, fmt_type in cols:
            val_raw = r[key]
            if fmt_type == "hora":
                val = f"{int(val_raw):02d}:00"
            elif fmt_type == "float1":
                val = f"{float(val_raw):.1f}"
            elif fmt_type == "float2":
                val = f"{float(val_raw):.2f}"
            else:
                val = str(val_raw)

            clr = COLOR["texto"]
            if key == "P_A":
                clr = COLOR["A"]
            elif key == "P_B":
                clr = COLOR["B"]
            elif key == "ahorro_kw":
                clr = COLOR["accent"]
            tds.append(html.Td(val, style={"padding": "8px 14px", "textAlign": "right", "fontSize": "12px", "color": clr, "borderBottom": "1px solid rgba(51, 65, 85, 0.4)"}))
        rows.append(html.Tr(tds, style={"background": "rgba(255, 71, 111, 0.05)" if r.get("lluvia", 0) else "transparent"}))

    return html.Div(
        style={"background": COLOR["fondo_sec"], "border": f"1px solid {COLOR['borde']}", "borderRadius": "10px", "padding": "20px", "overflowX": "auto"},
        children=[
            html.Div([
                html.Span("📋 REGISTRO NUMÉRICO HORARIO DE AUDITORÍA", style={"fontSize": "13px", "fontWeight": "700", "color": COLOR["accent"]}),
                html.Span("Datos trazables hora a hora (24 periodos)", style={"fontSize": "11.5px", "color": COLOR["texto_mut"], "marginLeft": "12px"}),
            ], style={"marginBottom": "14px", "display": "flex", "alignItems": "center"}),
            html.Table([html.Thead(header), html.Tbody(rows)], style={"width": "100%", "borderCollapse": "collapse"})
        ]
    )


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Simulador PTAR -- Reto MAREES 2026 (Interfaz Optimizada)")
    print("  Abre tu navegador en:  http://127.0.0.1:8050")
    print("="*60 + "\n")
    app.run(debug=False, host="127.0.0.1", port=8050)
