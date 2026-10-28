"""
config.py — Única fuente de verdad para todos los parámetros del simulador.
Reto MAREES 2026 — Fuentes declaradas explícitamente por variable.

Etiquetas de origen (Sección 9 de la Guía):
  'publicada'  → valor tomado de literatura técnica / docs del reto
  'sintética'  → generada/estimada con base en rangos típicos
  'calibrable' → parámetro de ajuste que requiere datos históricos reales
"""

# ─────────────────────────────────────────────
# 1. PARÁMETROS HIDRÁULICOS DE REFERENCIA
# ─────────────────────────────────────────────
Q_MED         = 100.0   # m³/h  — caudal medio diario  [publicada: ecuaciones.tex §5]
Q_PICO        = 150.0   # m³/h  — caudal pico diseño   [publicada: ecuaciones.tex §5]
Q_UMBRAL_LLUVIA = 170.0 # m³/h  — umbral punta hidráulica por lluvia [sintética]

# ─────────────────────────────────────────────
# 2. CALIDAD DEL INFLUENTE (BASE)
# ─────────────────────────────────────────────
DQO_BASE      = 300.0   # mg/L  — DQO media histórica influente  [publicada: ecuaciones.tex §5]
N_NH4_BASE    = 15.0    # mg N/L — Nitrógeno amoniacal típico doméstico [sintética]
BETA_DBO_DQO  = 0.45    # —     — Razón DBO5/DQO efluente tratado [publicada: ecuaciones.tex §3]

# ─────────────────────────────────────────────
# 3. REACTOR UASB (BIOLÓGICO 1 — ANAEROBIO)
# ─────────────────────────────────────────────
ETA_UASB_0    = 0.60    # —     — Eficiencia nominal remoción DQO [publicada: contexto §2.1]
T_UASB_OPT    = 20.0    # °C   — Temperatura óptima operación UASB [publicada]
PH_UASB_OPT   = 7.0     # —     — pH óptimo UASB [publicada]
K_T_UASB      = 0.02    # 1/°C — Sensibilidad térmica η_UASB [sintética/calibrable]
K_PH_UASB     = 0.05    # 1/upH — Sensibilidad pH η_UASB [sintética/calibrable]

# ─────────────────────────────────────────────
# 4. TANQUE AIREADO (BIOLÓGICO 2 — AEROBIO)
# ─────────────────────────────────────────────
A_COEF        = 1.0     # kg O₂/kg DQO  — requerimiento O₂ por DQO oxidada [publicada: ecuaciones.tex §3]
B_COEF        = 4.57    # kg O₂/kg N    — estequiometría nitrificación completa [publicada: ecuaciones.tex §3]
SAE           = 1.5     # kg O₂/kWh     — Eficiencia Estándar de Aireación sopladores [publicada: ecuaciones.tex §5]
ETA_AER_MAX   = 0.80    # —             — Eficiencia aerobia máxima [publicada: ecuaciones.tex §4]
P_MIN         = 6.0     # kW            — Potencia mínima mezcla/suspensión biomasa [publicada: ecuaciones.tex §5]
P_FIJA        = 18.0    # kW            — Potencia fija Escenario A (dimensionada para Q_PICO) [publicada: ecuaciones.tex §5]

# ─────────────────────────────────────────────
# 5. CONTROL ADAPTATIVO (ESCENARIO B)
# ─────────────────────────────────────────────
OD_META       = 2.0     # mg/L  — Consigna de Oxígeno Disuelto [publicada: contexto §4.2]
OD_META_MIN   = 1.5     # mg/L  — Límite inferior rango óptimo OD [publicada: contexto §4.2]
K_P_OD        = 0.15    # —     — Ganancia proporcional lazo OD [calibrable]
GAMMA_OD      = 0.15    # L/mg  — Sensibilidad Phi(t) a caida de OD [calibrable]

# ─────────────────────────────────────────────
# 6. SOFT-SENSOR — EXPONENTES α POR RÉGIMEN
# ─────────────────────────────────────────────
ALPHA_ORDINARIO = 1.0   # —    — Jornada seca normal [publicada: ecuaciones.tex §2.3]
ALPHA_LLUVIA    = -0.5  # —    — Punta hidráulica por lluvia (dilución) [publicada: ecuaciones.tex §2.3]
ALPHA_CHOQUE    = 1.0   # —    — Choque orgánico (Q normal, DQO elevada) [publicada]

# ─────────────────────────────────────────────
# 7. LÍMITES NORMATIVOS (Resolución 0631/2015, Art. 8)
# ─────────────────────────────────────────────
DQO_NORMA     = 180.0   # mg O₂/L — Tramos 1 y 2 [publicada: contexto §3.1]
DBO5_NORMA    = 90.0    # mg O₂/L [publicada: contexto §3.1]
SST_NORMA     = 90.0    # mg/L    [publicada: contexto §3.1]

# ─────────────────────────────────────────────
# 8. COSTOS (Referencia PTAR Salitre / Colombia)
# ─────────────────────────────────────────────
C_KWH         = 650.0    # COP/kWh  — Tarifa industrial Colombia [sintética/referencia Salitre]
C_QUIM        = 4_500.0  # COP/kg   — Costo coagulante/floculante [sintética]
C_LODO        = 120.0    # COP/kg   — Gestión lodos deshidratados [sintética]
C_ADICIONAL_B = 8_000.0  # COP/día  — Mantenimiento instrumentación Escenario B [sintética]

# ─────────────────────────────────────────────
# 9. PARÁMETROS DE LODOS (Módulo secundario)
# ─────────────────────────────────────────────
FACTOR_LODO   = 0.35    # kg lodo seco / kg DQO removida [sintética/calibrable]

# ─────────────────────────────────────────────
# 10. SIMULACIÓN TEMPORAL
# ─────────────────────────────────────────────
N_HORAS       = 24      # horas en el horizonte de evaluación
DELTA_T       = 1.0     # h — paso de tiempo (discreto horario)
