"""
soft_sensor.py — Módulo 1
Estimador en línea de carga orgánica instantánea (Feedforward).
Implementa la ecuación general del Soft-Sensor con exponente α y factor Φ(t).

Ecuaciones implementadas (ecuaciones.tex §2.3):
  DQO_est(t) = DQO_base · (Q(t)/Q_med)^α · Φ(t)
  Φ(t)       = 1 + γ_OD · max(0, OD_meta - OD(t))
  L_DQO(t)   = Q(t) · DQO_est(t) / 1000
  L_N(t)     = Q(t) · N_NH4(t)   / 1000
"""

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as cfg


def estimar_dqo(Q: np.ndarray,
                DQO_base: float = cfg.DQO_BASE,
                Q_med: float    = cfg.Q_MED,
                alpha: np.ndarray | float = cfg.ALPHA_ORDINARIO,
                phi: np.ndarray | float   = 1.0) -> np.ndarray:
    """
    Calcula la concentración estimada de DQO en cada hora.

    Parámetros
    ----------
    Q       : array (m³/h) — caudal horario medido en línea
    alpha   : scalar o array — exponente de elasticidad caudal-concentración
    phi     : scalar o array — factor corrector por choque de carga (≥ 1)

    Retorna
    -------
    DQO_est : array (mg/L)  [etiqueta: ESTIMADA]
    """
    ratio = Q / Q_med
    # Evitar ratio=0 en exponentes negativos
    ratio = np.where(ratio <= 0, 1e-6, ratio)
    DQO_est = DQO_base * (ratio ** alpha) * phi
    # Clip físico: DQO no puede ser negativa ni irrealmente alta
    return np.clip(DQO_est, 10.0, 2000.0)


def calcular_phi(OD_medido: np.ndarray,
                 OD_meta: float   = cfg.OD_META,
                 gamma_OD: float  = cfg.GAMMA_OD) -> np.ndarray:
    """
    Factor Φ(t): amplificador de carga cuando el sensor OD detecta déficit.
    Φ(t) = 1 + γ_OD · max(0, OD_meta - OD(t))

    En Escenario A (sin sensor), OD_medido = OD_meta → Φ = 1.0 siempre.
    En Escenario B, OD_medido varía con la carga real.
    """
    deficit = np.maximum(0.0, OD_meta - OD_medido)
    return 1.0 + gamma_OD * deficit


def calcular_cargas(Q: np.ndarray,
                    DQO_est: np.ndarray,
                    N_NH4: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Carga orgánica L_DQO (kg DQO/h) y nitrogenada L_N (kg N/h).

    L_DQO(t) = Q(t) · DQO_est(t) / 1000
    L_N(t)   = Q(t) · N_NH4(t)   / 1000

    Demostración dimensional: [m³/h] · [mg/L] / 1000 = [kg/h]
    """
    L_DQO = Q * DQO_est / 1000.0
    L_N   = Q * N_NH4   / 1000.0
    return L_DQO, L_N


def run(df_input, OD_medido: np.ndarray | None = None) -> dict:
    """
    Ejecuta el módulo completo sobre un DataFrame de entrada.

    Parámetros
    ----------
    df_input  : DataFrame de data_generator con columnas Q, DQO_real, N_NH4, alpha, phi
    OD_medido : array de OD (mg/L) medido en el reactor — None usa OD_meta fijo

    Retorna
    -------
    dict con arrays: DQO_est, phi_calculado, L_DQO, L_N
    """
    Q      = df_input["Q"].values
    N_NH4  = df_input["N_NH4"].values
    alpha  = df_input["alpha"].values
    phi_in = df_input["phi"].values   # factor phi del sub-escenario

    if OD_medido is None:
        # Sin sensor → Φ = valor del escenario (choque pre-definido)
        phi_calc = phi_in
    else:
        phi_calc = calcular_phi(OD_medido) * phi_in  # combinación feedforward + feedback

    DQO_est       = estimar_dqo(Q, alpha=alpha, phi=phi_calc)
    L_DQO, L_N    = calcular_cargas(Q, DQO_est, N_NH4)

    return {
        "DQO_est":      DQO_est,       # mg/L  [ESTIMADA]
        "phi_calc":     phi_calc,       # —     [ESTIMADA]
        "L_DQO":        L_DQO,         # kg DQO/h [ESTIMADA]
        "L_N":          L_N,           # kg N/h   [ESTIMADA]
    }

