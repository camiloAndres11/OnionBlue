"""
uasb.py — Módulo 2a
Reactor Anaerobio de Flujo Ascendente (UASB) — Biológico 1.
Remueve fracción η_UASB de la carga orgánica SIN consumo eléctrico de aireación.

Ecuaciones implementadas (ecuaciones.tex §3.1):
  η_UASB(t) = η_UASB,0 · f_T(T) · f_pH(pH)
  L_rem(t)  = L_DQO(t) · (1 - η_UASB(t))
"""

import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config as cfg


def factor_temperatura(T: np.ndarray,
                       T_opt: float   = cfg.T_UASB_OPT,
                       k_T: float     = cfg.K_T_UASB) -> np.ndarray:
    """
    f_T(T) = 1 - k_T · |T - T_opt|
    Reduce η_UASB cuando T se aleja del óptimo operativo.
    Clamped en [0.7, 1.0] para mantener plausibilidad física.
    """
    f = 1.0 - k_T * np.abs(T - T_opt)
    return np.clip(f, 0.70, 1.0)


def factor_ph(pH: np.ndarray,
              pH_opt: float  = cfg.PH_UASB_OPT,
              k_pH: float    = cfg.K_PH_UASB) -> np.ndarray:
    """
    f_pH(pH) = 1 - k_pH · |pH - pH_opt|
    Penaliza η_UASB fuera del rango neutro.
    Clamped en [0.75, 1.0].
    """
    f = 1.0 - k_pH * np.abs(pH - pH_opt)
    return np.clip(f, 0.75, 1.0)


def eficiencia_uasb(T: np.ndarray,
                    pH: np.ndarray,
                    eta0: float = cfg.ETA_UASB_0) -> np.ndarray:
    """
    Eficiencia de remoción horaria del UASB.
    η_UASB(t) = η_UASB,0 · f_T(T) · f_pH(pH)

    Retorna array de eficiencias [0.0, 1.0] [etiqueta: ESTIMADA]
    """
    fT  = factor_temperatura(T)
    fPH = factor_ph(pH)
    return eta0 * fT * fPH


def carga_remanente(L_DQO: np.ndarray,
                    T: np.ndarray,
                    pH: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Carga orgánica remanente que pasa al Tanque Aireado.
    L_rem(t) = L_DQO(t) · (1 - η_UASB(t))

    Retorna
    -------
    L_rem   : array (kg DQO/h) [ESTIMADA]
    eta_arr : array η_UASB horario [ESTIMADA]
    """
    eta_arr = eficiencia_uasb(T, pH)
    L_rem   = L_DQO * (1.0 - eta_arr)
    return L_rem, eta_arr


def run(L_DQO: np.ndarray,
        T: np.ndarray,
        pH: np.ndarray) -> dict:
    """Interfaz estándar del módulo UASB."""
    L_rem, eta_arr = carga_remanente(L_DQO, T, pH)
    return {
        "L_rem":     L_rem,      # kg DQO/h — carga al tanque aireado [ESTIMADA]
        "eta_UASB":  eta_arr,    # — eficiencia horaria UASB [ESTIMADA]
    }

