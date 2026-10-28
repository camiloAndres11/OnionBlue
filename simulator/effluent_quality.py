"""
effluent_quality.py — Módulo 3
Verificación matemática de calidad del efluente (Resolución 0631/2015).

Ecuaciones implementadas (ecuaciones.tex §4):
  η_aer(t)       = η_aer_max · min(1, S_O2(t) / R_O2(t))
  L_salida(t)    = L_rem(t) · (1 - η_aer(t))
  DQO_salida(t)  = 1000 · L_salida(t) / Q(t)
  DBO5_salida(t) = β · DQO_salida(t)
  SST_salida(t)  = estimado proporcional a L_salida (modelo simplificado)

Restricciones duras (Tramos 1 y 2):
  DQO_salida ≤ 180 mg/L
  DBO5_salida ≤ 90 mg/L
  SST_salida  ≤ 90 mg/L
"""

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as cfg


def eficiencia_aerobia(S_O2: np.ndarray,
                       R_O2: np.ndarray,
                       eta_max: float = cfg.ETA_AER_MAX) -> np.ndarray:
    """
    η_aer(t) = η_aer_max · min(1, S_O2(t) / R_O2(t))

    Cuando S_O2 ≥ R_O2 → η_aer = η_aer_max (eficiencia máxima)
    Cuando S_O2 < R_O2 → η_aer < η_aer_max (déficit de oxígeno)
    """
    ratio = np.where(R_O2 > 0, S_O2 / R_O2, 1.0)
    return eta_max * np.minimum(1.0, ratio)


def concentracion_salida(L_rem: np.ndarray,
                         eta_aer: np.ndarray,
                         Q: np.ndarray,
                         beta: float = cfg.BETA_DBO_DQO) -> dict:
    """
    Calcula concentraciones de DQO y DBO5 en el efluente.

    DQO_salida(t) = DQO_est(t) · (1-η_UASB) · (1-η_aer(t))
    equivalente a: 1000 · L_rem(t) · (1-η_aer(t)) / Q(t)

    DBO5_salida(t) = β · DQO_salida(t)
    """
    L_salida    = L_rem * (1.0 - eta_aer)
    DQO_salida  = np.where(Q > 0, 1000.0 * L_salida / Q, 0.0)
    DBO5_salida = beta * DQO_salida

    # SST estimado: proporcional a la carga no removida (modelo simplificado)
    # SST ≈ 0.7 · DQO_salida (relación empírica típica en efluentes secundarios)
    SST_salida  = 0.70 * DQO_salida

    return {
        "L_salida":    L_salida,     # kg DQO/h [ESTIMADA]
        "DQO_salida":  DQO_salida,   # mg/L [ESTIMADA]
        "DBO5_salida": DBO5_salida,  # mg/L [ESTIMADA]
        "SST_salida":  SST_salida,   # mg/L [ESTIMADA — modelo simplificado]
    }


def verificar_norma(DQO: np.ndarray,
                    DBO5: np.ndarray,
                    SST: np.ndarray) -> dict:
    """
    Verifica cumplimiento hora a hora de la Resolución 0631/2015, Art. 8.

    Retorna
    -------
    dict con arrays booleanos por parámetro y resumen global.
    """
    cumple_DQO  = DQO  <= cfg.DQO_NORMA
    cumple_DBO5 = DBO5 <= cfg.DBO5_NORMA
    cumple_SST  = SST  <= cfg.SST_NORMA
    cumple_todo = cumple_DQO & cumple_DBO5 & cumple_SST

    return {
        "cumple_DQO":  cumple_DQO,
        "cumple_DBO5": cumple_DBO5,
        "cumple_SST":  cumple_SST,
        "cumple_todo": cumple_todo,
        "horas_cumplimiento": int(cumple_todo.sum()),
        "pct_cumplimiento":   100.0 * cumple_todo.mean(),
    }


def run(L_rem: np.ndarray,
        Q: np.ndarray,
        S_O2_A: np.ndarray,
        S_O2_B: np.ndarray,
        R_O2: np.ndarray) -> dict:
    """
    Ejecuta verificación de calidad para Escenario A y B.
    """
    eta_A = eficiencia_aerobia(S_O2_A, R_O2)
    eta_B = eficiencia_aerobia(S_O2_B, R_O2)

    efluente_A = concentracion_salida(L_rem, eta_A, Q)
    efluente_B = concentracion_salida(L_rem, eta_B, Q)

    norma_A = verificar_norma(efluente_A["DQO_salida"],
                               efluente_A["DBO5_salida"],
                               efluente_A["SST_salida"])
    norma_B = verificar_norma(efluente_B["DQO_salida"],
                               efluente_B["DBO5_salida"],
                               efluente_B["SST_salida"])

    return {
        "eta_aer_A":   eta_A,
        "eta_aer_B":   eta_B,
        "efluente_A":  efluente_A,
        "efluente_B":  efluente_B,
        "norma_A":     norma_A,
        "norma_B":     norma_B,
    }

