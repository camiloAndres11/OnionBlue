"""
data_generator.py — Módulo 0
Genera los perfiles horarios sintéticos de entrada para los 3 sub-escenarios:
  S1 — Jornada Ordinaria Seca
  S2 — Punta Hidráulica por Lluvia
  S3 — Choque de Carga Orgánica/Nitrogenada

Todos los datos son SINTÉTICOS FUNDAMENTADOS en los rangos típicos
documentados en contexto_y_estrategia_reto_marees.md (curva "doble joroba")
y en los parámetros de referencia del archivo ecuaciones.tex.
"""

import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import config as cfg


# ─────────────────────────────────────────────────────────────────────────────
# Perfil de caudal base — curva "doble joroba" municipal (24 factores horarios)
# Fuente: contexto §1.1 — vallles 55-65%, picos 140-150% de Q_med
# ─────────────────────────────────────────────────────────────────────────────
FACTOR_Q_BASE = np.array([
    0.57, 0.55, 0.56, 0.58, 0.62, 0.75,   # 00-05 h  Valle nocturno
    0.88, 1.05, 1.28, 1.35, 1.20, 1.10,   # 06-11 h  Rampa + Pico matutino
    1.05, 1.00, 0.98, 1.02, 1.08, 1.42,   # 12-17 h  Meseta + inicio pico vespertino
    1.50, 1.45, 1.30, 1.15, 0.95, 0.78,   # 18-23 h  Pico vespertino + rampa bajada
])

# Factor de carga orgánica horaria (correlacionado con actividad urbana)
FACTOR_DQO_BASE = np.array([
    0.65, 0.62, 0.63, 0.65, 0.70, 0.80,
    0.92, 1.10, 1.25, 1.30, 1.15, 1.05,
    1.00, 0.98, 0.97, 1.00, 1.05, 1.35,
    1.45, 1.40, 1.25, 1.10, 0.95, 0.80,
])

# Factor N-NH4 (similar a DQO con ligero retardo)
FACTOR_N_BASE = np.array([
    0.70, 0.68, 0.68, 0.70, 0.74, 0.82,
    0.94, 1.08, 1.22, 1.28, 1.12, 1.04,
    1.00, 0.98, 0.97, 1.00, 1.05, 1.32,
    1.42, 1.38, 1.22, 1.08, 0.94, 0.78,
])

HORAS = np.arange(cfg.N_HORAS)


def _temperatura_horaria():
    """Perfil de temperatura diurno típico (SINTÉTICO). Oscila ~14-22°C."""
    T_media = 18.0
    T_amp   = 4.0
    return T_media + T_amp * np.sin(np.pi * (HORAS - 6) / 12)


def _ph_horario():
    """pH con leve variación circadiana alrededor de 7.2 (SINTÉTICO)."""
    return 7.2 + 0.15 * np.sin(2 * np.pi * HORAS / 24)


def generar_escenario_s1():
    """
    S1 — Jornada Ordinaria Seca.
    α = ALPHA_ORDINARIO = 1.0, sin eventos especiales.
    """
    Q    = cfg.Q_MED * FACTOR_Q_BASE
    DQO  = cfg.DQO_BASE * FACTOR_DQO_BASE
    N    = cfg.N_NH4_BASE * FACTOR_N_BASE
    T    = _temperatura_horaria()
    pH   = _ph_horario()
    alfa = np.full(cfg.N_HORAS, cfg.ALPHA_ORDINARIO)
    phi  = np.ones(cfg.N_HORAS)          # sin choque
    lluvia = np.zeros(cfg.N_HORAS, dtype=bool)

    return _construir_df("S1 — Jornada Ordinaria Seca", Q, DQO, N, T, pH, alfa, phi, lluvia)


def generar_escenario_s2():
    """
    S2 — Punta Hidráulica por Lluvia.
    Entre las 14:00 y 18:00 hay un evento de lluvia:
      - Q sube ~70% adicional (dilución)
      - α = ALPHA_LLUVIA = -0.5 (DQO se diluye con el agua pluvial)
    """
    Q   = cfg.Q_MED * FACTOR_Q_BASE.copy()
    DQO = cfg.DQO_BASE * FACTOR_DQO_BASE.copy()
    N   = cfg.N_NH4_BASE * FACTOR_N_BASE.copy()
    T   = _temperatura_horaria()
    pH  = _ph_horario()
    alfa = np.full(cfg.N_HORAS, cfg.ALPHA_ORDINARIO)
    phi  = np.ones(cfg.N_HORAS)
    lluvia = np.zeros(cfg.N_HORAS, dtype=bool)

    # Evento de lluvia h=14..18: Q sube, DQO se diluye
    horas_lluvia = slice(14, 19)
    Q[horas_lluvia] *= 1.70        # Q aumenta 70 % por escorrentía
    DQO[horas_lluvia] *= 0.55      # DQO se diluye significativamente
    N[horas_lluvia]   *= 0.55
    alfa[horas_lluvia] = cfg.ALPHA_LLUVIA
    lluvia[horas_lluvia] = True

    return _construir_df("S2 — Punta Hidráulica (Lluvia)", Q, DQO, N, T, pH, alfa, phi, lluvia)


def generar_escenario_s3():
    """
    S3 — Choque de Carga Orgánica / Nitrogenada.
    Entre las 09:00 y 12:00 llega una descarga industrial concentrada:
      - Q no varía significativamente
      - DQO sube ×1.6 y N-NH4 sube ×1.5
      - Φ(t) > 1 (activado por caída de OD en el reactor)
    """
    Q   = cfg.Q_MED * FACTOR_Q_BASE.copy()
    DQO = cfg.DQO_BASE * FACTOR_DQO_BASE.copy()
    N   = cfg.N_NH4_BASE * FACTOR_N_BASE.copy()
    T   = _temperatura_horaria()
    pH  = _ph_horario() - 0.3      # Ligera caída de pH por descarga ácida
    alfa = np.full(cfg.N_HORAS, cfg.ALPHA_ORDINARIO)
    phi  = np.ones(cfg.N_HORAS)
    lluvia = np.zeros(cfg.N_HORAS, dtype=bool)

    # Choque orgánico h=9..12
    horas_choque = slice(9, 13)
    DQO[horas_choque] *= 1.60
    N[horas_choque]   *= 1.50
    phi[horas_choque]  = 1.30     # Φ > 1: sensor OD detecta déficit
    # Leve caída de pH en choque (activa alerta)
    pH[horas_choque]  -= 0.2

    return _construir_df("S3 — Choque Carga Orgánica/Nitrogenada", Q, DQO, N, T, pH, alfa, phi, lluvia)


def _construir_df(nombre, Q, DQO, N, T, pH, alfa, phi, lluvia):
    """Empaqueta los arrays en un DataFrame estándar de 24 filas."""
    df = pd.DataFrame({
        "hora":     HORAS,
        "Q":        Q,            # m³/h
        "DQO_real": DQO,          # mg/L  (dato de laboratorio — SINTÉTICO)
        "N_NH4":    N,            # mg N/L (SINTÉTICO)
        "T":        T,            # °C    (SINTÉTICO)
        "pH":       pH,           # —     (SINTÉTICO)
        "alpha":    alfa,         # —     (PUBLICADA: régimen soft-sensor)
        "phi":      phi,          # —     (ESTIMADA: factor choque)
        "lluvia":   lluvia,       # bool  (SINTÉTICO: evento)
    })
    df.attrs["escenario"] = nombre
    return df


# Registro de todos los sub-escenarios disponibles
ESCENARIOS = {
    "S1": generar_escenario_s1,
    "S2": generar_escenario_s2,
    "S3": generar_escenario_s3,
}


if __name__ == "__main__":
    for key, fn in ESCENARIOS.items():
        df = fn()
        print(f"\n=== {df.attrs['escenario']} ===")
        print(df[["hora", "Q", "DQO_real", "N_NH4", "T", "phi"]].to_string(index=False))

