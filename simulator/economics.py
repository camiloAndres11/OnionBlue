"""
economics.py — Módulo 4
Función objetivo económica: Costo Operativo Específico (CEO) en COP/m³.

Ecuación implementada (ecuaciones.tex §5, ec. CEO):
  CEO = [Σ(P(t)·Δt·C_kWh + D_quim(t)·Δt·C_quim + M_lodo(t)·C_lodo) + C_adicional]
        / [Σ Q(t)·Δt]

Módulo de dosificación química (Módulo 3 de la guía):
  - Solo se activa cuando: Q > Q_umbral_lluvia (punta hidráulica) O
                           DQO_salida > DQO_norma × 0.85 (alerta de calidad)
  - Dosis coagulante: 30 mg/L aplicado al caudal en esas horas
"""

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as cfg


def dosificacion_quimica(Q: np.ndarray,
                          DQO_salida: np.ndarray,
                          lluvia: np.ndarray,
                          dosis_mg_L: float = 30.0) -> np.ndarray:
    """
    D_quim(t) [kg/h] — solo cuando hay punta hidráulica o riesgo normativo.
    Dosis de coagulante = 30 mg/L sobre el caudal afectado.

    Condición de activación (OR):
      a) Evento de lluvia (punta hidráulica)
      b) DQO_salida > 85% del límite normativo (alerta preventiva)
    """
    alerta_calidad = DQO_salida > (cfg.DQO_NORMA * 0.85)
    activo = lluvia | alerta_calidad
    # Dosis [kg/h] = Q [m³/h] · dosis [mg/L] · 1000 [L/m³] / 1e6 [mg/kg]
    D_quim = np.where(activo, Q * dosis_mg_L / 1000.0, 0.0)
    return D_quim


def masa_lodos(L_DQO_removida: np.ndarray,
               factor_lodo: float = cfg.FACTOR_LODO) -> np.ndarray:
    """
    Producción horaria de lodos deshidratados [kg/h].
    M_lodo(t) = factor_lodo · L_DQO_removida(t)
    factor_lodo = 0.35 kg lodo seco / kg DQO removida [SINTÉTICO]
    """
    return factor_lodo * L_DQO_removida


def costo_horario(P: np.ndarray,
                   D_quim: np.ndarray,
                   M_lodo: np.ndarray,
                   C_kWh:  float = cfg.C_KWH,
                   C_quim: float = cfg.C_QUIM,
                   C_lodo: float = cfg.C_LODO,
                   dt:     float = cfg.DELTA_T) -> np.ndarray:
    """
    Costo horario [COP/h] para cada escenario.
    Costo(t) = P(t)·Δt·C_kWh + D_quim(t)·Δt·C_quim + M_lodo(t)·C_lodo
    """
    costo_elec  = P       * dt * C_kWh
    costo_quim  = D_quim  * dt * C_quim
    costo_lodos = M_lodo  * C_lodo
    return costo_elec + costo_quim + costo_lodos, costo_elec, costo_quim, costo_lodos


def calcular_CEO(P: np.ndarray,
                  Q: np.ndarray,
                  DQO_salida: np.ndarray,
                  L_DQO_removida: np.ndarray,
                  lluvia: np.ndarray,
                  C_adicional: float = 0.0) -> dict:
    """
    Calcula el CEO diario y los vectores de costo horario.

    Parámetros
    ----------
    C_adicional : COP/día extra de instrumentación (Escenario B lo incluye)

    Retorna
    -------
    dict con CEO [COP/m³], costos horarios desglosados y métricas energéticas.
    """
    D_quim = dosificacion_quimica(Q, DQO_salida, lluvia)
    M_lodo = masa_lodos(L_DQO_removida)

    costo_total_h, costo_elec_h, costo_quim_h, costo_lodo_h = costo_horario(
        P, D_quim, M_lodo
    )

    V_total = np.sum(Q * cfg.DELTA_T)           # m³/día
    E_total = np.sum(P * cfg.DELTA_T)            # kWh/día
    costo_dia = np.sum(costo_total_h) + C_adicional

    CEO = costo_dia / V_total if V_total > 0 else 0.0

    # Consumo específico de energía [kWh/m³]
    esp_energia = E_total / V_total if V_total > 0 else 0.0

    return {
        "CEO":             CEO,              # COP/m³  [CALCULADA]
        "E_total":         E_total,          # kWh/día [CALCULADA]
        "esp_energia":     esp_energia,      # kWh/m³  [CALCULADA]
        "V_total":         V_total,          # m³/día  [CALCULADA]
        "costo_dia":       costo_dia,        # COP/día [CALCULADA]
        "D_quim":          D_quim,           # kg/h    [CALCULADA]
        "M_lodo":          M_lodo,           # kg/h    [CALCULADA]
        "costo_total_h":   costo_total_h,    # COP/h   [CALCULADA]
        "costo_elec_h":    costo_elec_h,     # COP/h   [CALCULADA]
        "costo_quim_h":    costo_quim_h,     # COP/h   [CALCULADA]
        "costo_lodo_h":    costo_lodo_h,     # COP/h   [CALCULADA]
    }


def run(Q: np.ndarray,
        P_A: np.ndarray, P_B: np.ndarray,
        DQO_A: np.ndarray, DQO_B: np.ndarray,
        L_DQO_rem_A: np.ndarray, L_DQO_rem_B: np.ndarray,
        lluvia: np.ndarray) -> dict:
    """
    Ejecuta el módulo económico para ambos escenarios.
    Escenario B incluye C_adicional por instrumentación.
    """
    econ_A = calcular_CEO(P_A, Q, DQO_A, L_DQO_rem_A, lluvia,
                           C_adicional=0.0)
    econ_B = calcular_CEO(P_B, Q, DQO_B, L_DQO_rem_B, lluvia,
                           C_adicional=cfg.C_ADICIONAL_B)

    # Métricas de ahorro
    ahorro_CEO_pct    = 100.0 * (econ_A["CEO"] - econ_B["CEO"]) / econ_A["CEO"] \
                        if econ_A["CEO"] > 0 else 0.0
    ahorro_E_pct      = 100.0 * (econ_A["E_total"] - econ_B["E_total"]) / econ_A["E_total"] \
                        if econ_A["E_total"] > 0 else 0.0
    ahorro_E_kwh      = econ_A["E_total"] - econ_B["E_total"]

    return {
        "econ_A":           econ_A,
        "econ_B":           econ_B,
        "ahorro_CEO_pct":   ahorro_CEO_pct,   # %   [CALCULADA]
        "ahorro_E_pct":     ahorro_E_pct,     # %   [CALCULADA]
        "ahorro_E_kwh":     ahorro_E_kwh,     # kWh [CALCULADA]
    }

