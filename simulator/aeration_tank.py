"""
aeration_tank.py — Módulo 2b
Tanque Aireado (Biológico 2) — Control de sopladores eléctricos.

Implementa la LEY DE CONTROL DE POTENCIA para ambos escenarios:

  Escenario A (Línea Base — Fija):
    P_A(t) = P_fija = 18 kW  (constante 24 h)
    → Dimensionada para el pico de Q. Sobre-airea en horas valle.

  Escenario B (Propuesta Adaptativa — VFD + Control OD):
    P_B(t) = max(P_min, R_O2(t)/SAE · [1 + k_p·(OD_meta - OD(t))])
    → Ajusta potencia a la demanda real + corrección feedback OD.

Ecuaciones implementadas (ecuaciones.tex §3.3):
  R_O2(t)     = a·L_rem(t) + b·L_N(t)
  S_O2(t)     = P(t) · SAE
  OD_modelo(t) = f(S_O2, R_O2)  — balance simplificado en estado cuasi-estacionario
"""

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as cfg


def demanda_oxigeno(L_rem: np.ndarray,
                    L_N: np.ndarray,
                    a: float = cfg.A_COEF,
                    b: float = cfg.B_COEF) -> np.ndarray:
    """
    Tasa horaria de oxígeno requerido [kg O₂/h].
    R_O2(t) = a·L_rem(t) + b·L_N(t)

    a = 1.0  kg O₂/kg DQO  (oxidación carbonácea)
    b = 4.57 kg O₂/kg N    (nitrificación completa — estequiometría NH4+ + 2O2)
    """
    return a * L_rem + b * L_N


def potencia_escenario_A(n_horas: int = cfg.N_HORAS,
                          P_fija: float = cfg.P_FIJA) -> np.ndarray:
    """
    Escenario A: potencia constante para todas las horas.
    P_A(t) = P_fija  [kW]  — dimensionada para Q_pico

    NOTA: Si P_fija < demanda real en pico, el sistema queda en déficit.
    En el Escenario A real de una PTAR, P_fija se dimensiona para el pico
    histórico y se mantiene constante. Esto se recalcula en run() con el
    verdadero máximo de R_O2.
    """
    return np.full(n_horas, P_fija)


def od_modelo(P: np.ndarray,
              R_O2: np.ndarray,
              SAE: float    = cfg.SAE,
              OD_meta: float = cfg.OD_META) -> np.ndarray:
    """
    Modelo simplificado de OD en estado cuasi-estacionario.
    Cuando S_O2 >= R_O2 el reactor está bien abastecido → OD tiende a OD_meta.
    Cuando S_O2 < R_O2 hay déficit → OD cae proporcionalmente.

    OD(t) = OD_meta · min(1, S_O2(t) / R_O2(t))
    Esto garantiza OD ≤ OD_meta cuando hay suministro exacto,
    y OD < OD_meta cuando hay déficit de O2.
    """
    S_O2 = P * SAE
    ratio = np.where(R_O2 > 0, S_O2 / R_O2, 1.0)
    OD   = OD_meta * np.minimum(1.0, ratio)
    return np.clip(OD, 0.0, 5.0)


def potencia_escenario_B(R_O2: np.ndarray,
                          SAE: float    = cfg.SAE,
                          P_min: float  = cfg.P_MIN,
                          OD_meta: float = cfg.OD_META,
                          k_p: float    = cfg.K_P_OD,
                          n_iter: int   = 3) -> tuple[np.ndarray, np.ndarray]:
    """
    Escenario B: potencia adaptativa con lazo cerrado OD.

    La ley de control calcula la potencia necesaria para satisfacer
    exactamente la demanda de oxígeno, con una corrección proporcional
    al error de OD. El resultado es SIEMPRE ≤ P_fija excepto en picos.

    P_B(t) = max(P_min, R_O2(t)/SAE · [1 + k_p·(OD_meta - OD(t))])

    Dado que OD_modelo = OD_meta · min(1, S_O2/R_O2):
    - Si P_B = R_O2/SAE exactamente → OD = OD_meta → error = 0 → estable.
    - El k_p solo actúa cuando hay déficit (OD < OD_meta), empujando P_B al alza.
    - Limitamos la corrección a un máximo del 20% sobre la demanda base.

    Retorna
    -------
    P_B     : array potencia adaptativa [kW]
    OD_ctrl : array OD resultante con control [mg/L]
    """
    # Potencia base exactamente proporcional a la demanda
    P_base_demanda = R_O2 / SAE

    # Primera estimación: sin corrección
    P_B = np.maximum(P_min, P_base_demanda)

    for _ in range(n_iter):
        OD_est = od_modelo(P_B, R_O2, SAE, OD_meta)
        error  = OD_meta - OD_est  # > 0 si hay déficit, ≤ 0 si hay exceso
        # Corrección SOLO al alza (si hay déficit), limitada al 20%
        correccion = np.clip(k_p * error, -0.10, 0.20)
        P_B = np.maximum(P_min, P_base_demanda * (1.0 + correccion))

    OD_ctrl = od_modelo(P_B, R_O2, SAE, OD_meta)
    return P_B, OD_ctrl


def suministro_oxigeno(P: np.ndarray,
                        SAE: float = cfg.SAE) -> np.ndarray:
    """S_O2(t) = P(t) · SAE  [kg O₂/h]"""
    return P * SAE


def run(L_rem: np.ndarray,
        L_N: np.ndarray) -> dict:
    """
    Ejecuta ambos escenarios para los mismos inputs de carga.

    Retorna
    -------
    dict con todos los arrays horarios para A y B.
    """
    R_O2 = demanda_oxigeno(L_rem, L_N)

    # ── Escenario A ──────────────────────────────────────────────────────────
    P_A    = potencia_escenario_A(len(L_rem))
    S_O2_A = suministro_oxigeno(P_A)
    OD_A   = od_modelo(P_A, R_O2)

    # ── Escenario B ──────────────────────────────────────────────────────────
    P_B, OD_B = potencia_escenario_B(R_O2)
    S_O2_B    = suministro_oxigeno(P_B)

    # ── Métricas de sobre-aireación ───────────────────────────────────────────
    sobre_aireacion_A = np.maximum(0.0, S_O2_A - R_O2)  # kg O₂/h desperdiciados en A
    sobre_aireacion_B = np.maximum(0.0, S_O2_B - R_O2)  # kg O₂/h desperdiciados en B

    return {
        "R_O2":           R_O2,            # kg O₂/h — demanda real [ESTIMADA]
        # Escenario A
        "P_A":            P_A,             # kW [PUBLICADA/FIJA]
        "S_O2_A":         S_O2_A,          # kg O₂/h [ESTIMADA]
        "OD_A":           OD_A,            # mg/L [ESTIMADA]
        "sobre_aire_A":   sobre_aireacion_A,# kg O₂/h desperdiciados [ESTIMADA]
        # Escenario B
        "P_B":            P_B,             # kW [ESTIMADA — control adaptativo]
        "S_O2_B":         S_O2_B,          # kg O₂/h [ESTIMADA]
        "OD_B":           OD_B,            # mg/L [ESTIMADA]
        "sobre_aire_B":   sobre_aireacion_B,# kg O₂/h [ESTIMADA]
    }
