"""
scenarios.py — Orquestador principal
Conecta todos los módulos y devuelve un DataFrame unificado con
los resultados de Escenario A y B para un sub-escenario dado.

Columnas del DataFrame de salida (una fila por hora):
  hora, Q, DQO_est, DQO_real, N_NH4, T, pH, alpha, phi, lluvia,
  L_DQO, L_N, eta_UASB, L_rem,
  R_O2,
  P_A, S_O2_A, OD_A, sobre_aire_A, eta_aer_A,
    DQO_sal_A, DBO5_sal_A, SST_sal_A, cumple_A,
    costo_elec_A_h, costo_quim_A_h, costo_lodo_A_h, costo_total_A_h,
  P_B, S_O2_B, OD_B, sobre_aire_B, eta_aer_B,
    DQO_sal_B, DBO5_sal_B, SST_sal_B, cumple_B,
    costo_elec_B_h, costo_quim_B_h, costo_lodo_B_h, costo_total_B_h,
  D_quim_A, D_quim_B, M_lodo_A, M_lodo_B
"""

import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from simulator import data_generator as dg
from simulator import soft_sensor    as ss
from simulator import uasb
from simulator import aeration_tank  as at
from simulator import effluent_quality as eq
from simulator import economics      as ec
import config as cfg


def correr_simulacion(escenario_key: str = "S1",
                       params: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """
    Ejecuta la simulación completa para un sub-escenario (S1/S2/S3).

    Parámetros
    ----------
    escenario_key : 'S1', 'S2' o 'S3'
    params        : dict con overrides de config (para sliders del dashboard)
                    Claves soportadas: SAE, OD_meta, P_min, k_p, C_kWh, P_fija

    Retorna
    -------
    df_resultado : DataFrame de 24 filas con todas las variables
    kpis         : dict con métricas resumen (para tarjetas KPI del dashboard)
    """
    # ── 0. Aplicar overrides de parámetros (desde sliders del dashboard) ─────
    cfg_local = _config_con_overrides(params or {})

    # ── 1. Generar datos de entrada ───────────────────────────────────────────
    df = dg.ESCENARIOS[escenario_key]()
    Q      = df["Q"].values
    T      = df["T"].values
    pH     = df["pH"].values
    N_NH4  = df["N_NH4"].values
    lluvia = df["lluvia"].values

    # ── 2. Soft-Sensor (Módulo 1) ─────────────────────────────────────────────
    out_ss = ss.run(df)
    DQO_est = out_ss["DQO_est"]
    L_DQO   = out_ss["L_DQO"]
    L_N     = out_ss["L_N"]
    phi_calc = out_ss["phi_calc"]

    # ── 3. UASB (Módulo 2a) ───────────────────────────────────────────────────
    out_uasb = uasb.run(L_DQO, T, pH)
    L_rem    = out_uasb["L_rem"]
    eta_UASB = out_uasb["eta_UASB"]

    # ── 4. Tanque Aireado (Módulo 2b) ─────────────────────────────────────────
    # Recompute con parámetros locales si hay overrides
    R_O2 = at.demanda_oxigeno(L_rem, L_N, cfg_local["A_COEF"], cfg_local["B_COEF"])

    # P_fija del Escenario A se dimensiona para cubrir el pico real de R_O2
    # (esto es exactamente lo que hace una planta real: sobredimensionar para el pico)
    P_fija_real = max(cfg_local["P_FIJA"],
                      float(R_O2.max() / cfg_local["SAE"]))

    P_A    = at.potencia_escenario_A(len(Q), P_fija_real)
    S_O2_A = at.suministro_oxigeno(P_A, cfg_local["SAE"])
    OD_A   = at.od_modelo(P_A, R_O2, cfg_local["SAE"], cfg_local["OD_META"])
    sobre_aire_A = np.maximum(0.0, S_O2_A - R_O2)

    P_B, OD_B = at.potencia_escenario_B(R_O2, cfg_local["SAE"],
                                          cfg_local["P_MIN"],
                                          cfg_local["OD_META"],
                                          cfg_local["K_P_OD"])
    S_O2_B    = at.suministro_oxigeno(P_B, cfg_local["SAE"])
    sobre_aire_B = np.maximum(0.0, S_O2_B - R_O2)

    # ── 5. Calidad de efluente (Módulo 3) ─────────────────────────────────────
    out_eq = eq.run(L_rem, Q, S_O2_A, S_O2_B, R_O2)
    eta_aer_A  = out_eq["eta_aer_A"]
    eta_aer_B  = out_eq["eta_aer_B"]
    ef_A = out_eq["efluente_A"]
    ef_B = out_eq["efluente_B"]
    nA   = out_eq["norma_A"]
    nB   = out_eq["norma_B"]

    # ── 6. Economía (Módulo 4) ────────────────────────────────────────────────
    L_DQO_rem_A = L_rem * eta_aer_A   # kg DQO efectivamente removida en aireado A
    L_DQO_rem_B = L_rem * eta_aer_B

    # Recompute con C_kWh local si fue cambiado
    out_ec = _economics_con_params(
        Q, P_A, P_B,
        ef_A["DQO_salida"], ef_B["DQO_salida"],
        L_DQO_rem_A, L_DQO_rem_B,
        lluvia, cfg_local
    )
    econ_A = out_ec["econ_A"]
    econ_B = out_ec["econ_B"]

    # ── 7. Ensamblar DataFrame ─────────────────────────────────────────────────
    df_res = pd.DataFrame({
        "hora":         np.arange(cfg.N_HORAS),
        # Entrada
        "Q":            Q,
        "DQO_est":      DQO_est,
        "DQO_real":     df["DQO_real"].values,
        "N_NH4":        N_NH4,
        "T":            T,
        "pH":           pH,
        "phi":          phi_calc,
        "lluvia":       lluvia.astype(int),
        # Módulo 1 + 2a
        "L_DQO":        L_DQO,
        "L_N":          L_N,
        "eta_UASB":     eta_UASB,
        "L_rem":        L_rem,
        # Demanda O2
        "R_O2":         R_O2,
        # ── Escenario A ──
        "P_A":          P_A,
        "S_O2_A":       S_O2_A,
        "OD_A":         OD_A,
        "sobre_aire_A": sobre_aire_A,
        "eta_aer_A":    eta_aer_A,
        "DQO_sal_A":    ef_A["DQO_salida"],
        "DBO5_sal_A":   ef_A["DBO5_salida"],
        "SST_sal_A":    ef_A["SST_salida"],
        "cumple_A":     nA["cumple_todo"].astype(int),
        "costo_elec_A": econ_A["costo_elec_h"],
        "costo_quim_A": econ_A["costo_quim_h"],
        "costo_lodo_A": econ_A["costo_lodo_h"],
        "costo_tot_A":  econ_A["costo_total_h"],
        "D_quim_A":     econ_A["D_quim"],
        "M_lodo_A":     econ_A["M_lodo"],
        # ── Escenario B ──
        "P_B":          P_B,
        "S_O2_B":       S_O2_B,
        "OD_B":         OD_B,
        "sobre_aire_B": sobre_aire_B,
        "eta_aer_B":    eta_aer_B,
        "DQO_sal_B":    ef_B["DQO_salida"],
        "DBO5_sal_B":   ef_B["DBO5_salida"],
        "SST_sal_B":    ef_B["SST_salida"],
        "cumple_B":     nB["cumple_todo"].astype(int),
        "costo_elec_B": econ_B["costo_elec_h"],
        "costo_quim_B": econ_B["costo_quim_h"],
        "costo_lodo_B": econ_B["costo_lodo_h"],
        "costo_tot_B":  econ_B["costo_total_h"],
        "D_quim_B":     econ_B["D_quim"],
        "M_lodo_B":     econ_B["M_lodo"],
    })

    df_res.attrs["escenario"] = df.attrs["escenario"]

    # ── 8. KPIs resumen ───────────────────────────────────────────────────────
    kpis = {
        "escenario":         df.attrs["escenario"],
        # Energía
        "E_A_kwh":           round(econ_A["E_total"], 1),
        "E_B_kwh":           round(econ_B["E_total"], 1),
        "ahorro_E_kwh":      round(out_ec["ahorro_E_kwh"], 1),
        "ahorro_E_pct":      round(out_ec["ahorro_E_pct"], 1),
        # Costos
        "CEO_A":             round(econ_A["CEO"], 2),
        "CEO_B":             round(econ_B["CEO"], 2),
        "ahorro_CEO_pct":    round(out_ec["ahorro_CEO_pct"], 1),
        "ahorro_CEO_COP_m3": round(econ_A["CEO"] - econ_B["CEO"], 2),
        # Calidad
        "horas_cumple_A":    nA["horas_cumplimiento"],
        "horas_cumple_B":    nB["horas_cumplimiento"],
        # Sobre-aireación
        "sobre_aire_A_kg":   round(float(sobre_aire_A.sum()), 1),
        "sobre_aire_B_kg":   round(float(sobre_aire_B.sum()), 1),
        # Energía específica
        "esp_E_A":           round(econ_A["esp_energia"], 3),
        "esp_E_B":           round(econ_B["esp_energia"], 3),
        # Volumen tratado
        "V_dia_m3":          round(econ_A["V_total"], 0),
    }

    return df_res, kpis


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────────────────────

def _config_con_overrides(params: dict) -> dict:
    """Devuelve dict con valores de config, aplicando overrides del dashboard."""
    return {
        "SAE":     params.get("SAE",     cfg.SAE),
        "OD_META": params.get("OD_META", cfg.OD_META),
        "P_MIN":   params.get("P_MIN",   cfg.P_MIN),
        "P_FIJA":  params.get("P_FIJA",  cfg.P_FIJA),
        "K_P_OD":  params.get("K_P_OD",  cfg.K_P_OD),
        "C_KWH":   params.get("C_KWH",   cfg.C_KWH),
        "A_COEF":  cfg.A_COEF,
        "B_COEF":  cfg.B_COEF,
    }


def _economics_con_params(Q, P_A, P_B, DQO_A, DQO_B,
                           L_rem_A, L_rem_B, lluvia, cfg_local):
    """Corre economics con C_kWh potencialmente overrideado."""
    D_quim_A = ec.dosificacion_quimica(Q, DQO_A, lluvia)
    D_quim_B = ec.dosificacion_quimica(Q, DQO_B, lluvia)
    M_lodo_A = ec.masa_lodos(L_rem_A)
    M_lodo_B = ec.masa_lodos(L_rem_B)

    def _ceo(P, D_q, M_l, C_adic):
        tot, e, q, l = ec.costo_horario(P, D_q, M_l,
                                         C_kWh=cfg_local["C_KWH"],
                                         C_quim=cfg.C_QUIM,
                                         C_lodo=cfg.C_LODO)
        V = float(np.sum(Q * cfg.DELTA_T))
        E = float(np.sum(P * cfg.DELTA_T))
        costo_dia = float(np.sum(tot)) + C_adic
        return {
            "CEO":           costo_dia / V if V > 0 else 0,
            "E_total":       E,
            "esp_energia":   E / V if V > 0 else 0,
            "V_total":       V,
            "costo_dia":     costo_dia,
            "D_quim":        D_q,
            "M_lodo":        M_l,
            "costo_total_h": tot,
            "costo_elec_h":  e,
            "costo_quim_h":  q,
            "costo_lodo_h":  l,
        }

    econ_A = _ceo(P_A, D_quim_A, M_lodo_A, 0.0)
    econ_B = _ceo(P_B, D_quim_B, M_lodo_B, cfg.C_ADICIONAL_B)

    ahorro_CEO = 100*(econ_A["CEO"]-econ_B["CEO"])/econ_A["CEO"] if econ_A["CEO"]>0 else 0
    ahorro_E   = 100*(econ_A["E_total"]-econ_B["E_total"])/econ_A["E_total"] if econ_A["E_total"]>0 else 0

    return {
        "econ_A":         econ_A,
        "econ_B":         econ_B,
        "ahorro_CEO_pct": ahorro_CEO,
        "ahorro_E_pct":   ahorro_E,
        "ahorro_E_kwh":   econ_A["E_total"] - econ_B["E_total"],
    }


if __name__ == "__main__":
    for key in ["S1", "S2", "S3"]:
        df, kpis = correr_simulacion(key)
        print(f"\n{'='*60}")
        print(f"  {kpis['escenario']}")
        print(f"{'='*60}")
        print(f"  CEO A:          {kpis['CEO_A']:.2f} COP/m³")
        print(f"  CEO B:          {kpis['CEO_B']:.2f} COP/m³")
        print(f"  Ahorro CEO:     {kpis['ahorro_CEO_pct']:.1f}%")
        print(f"  Energía A:      {kpis['E_A_kwh']:.1f} kWh/día")
        print(f"  Energía B:      {kpis['E_B_kwh']:.1f} kWh/día")
        print(f"  Ahorro Energía: {kpis['ahorro_E_pct']:.1f}%")
        print(f"  Sobre-aire A:   {kpis['sobre_aire_A_kg']:.1f} kg O₂/día desperdiciados")
        print(f"  Cumplimiento A: {kpis['horas_cumple_A']}/24 h")
        print(f"  Cumplimiento B: {kpis['horas_cumple_B']}/24 h")
