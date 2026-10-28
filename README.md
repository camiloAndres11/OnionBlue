# 🌊 Simulador PTAR Adaptativo — Reto MAREES: "Cada gota cuenta" (Blue Onion Lab 2026)

Prototipo computacional y matemático (Nivel 2) para la optimización energética en Plantas de Tratamiento de Aguas Residuales (PTAR) con arquitectura de referencia tipo **Tunja (Boyacá)**:
$$\text{Pretratamiento} \longrightarrow \text{Reactor UASB} \longrightarrow \text{Tanque Aireado (Sopladores)} \longrightarrow \text{Clarificador Secundario}$$

---

## 🎯 Objetivo del Proyecto

Demostrar la viabilidad técnica, matemática y económica de reducir más de un **25 % en el Costo Operativo Específico ($\text{CEO}$ en $\text{COP/m}^3$)** mediante una arquitectura de control adaptativo híbrida (**Soft-Sensor Feedforward + Lazo Cerrado Feedback de Oxígeno Disuelto**) sin comprometer el cumplimiento de los límites de vertimiento de la **Resolución 0631 de 2015**.

### Comparativa de Escenarios
* **Escenario A (Línea Base Fija):** Operación estática convencional. Sopladores operan a potencia fija constante dimensionada para el pico horario ($P_{\text{base}} = \max_t (R_{\text{O}_2}/\text{SAE})$), provocando sobre-aireación masiva y derroche eléctrico en horas valle.
* **Escenario B (Propuesta Adaptativa):** Modulación horaria de potencia eléctrica con Variadores de Frecuencia (VFD), piso mecánico de seguridad de agitación ($P_{\text{mín}} = 6\text{ kW}$) y estabilización en consigna de $\text{OD} = 2.0\text{ mg/L}$.

---

## 📊 Resultados Clave de la Simulación

| Sub-escenario de Prueba | $\text{CEO}$ Esc. A ($\text{COP/m}^3$) | $\text{CEO}$ Esc. B ($\text{COP/m}^3$) | Ahorro en $\text{CEO}$ | Reducción de Energía | Cumplimiento Res. 0631 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **S1 — Jornada Ordinaria Seca** | $191.2$ | $102.5$ | **▼ 46.4 %** | **▼ 49.3 %** | **24 / 24 h (100 %)** |
| **S2 — Punta Hidráulica (Lluvia)** | $204.1$ | $134.7$ | **▼ 34.0 %** | **▼ 47.7 %** | **24 / 24 h (100 %)** |
| **S3 — Choque de Carga Orgánica** | $208.6$ | $110.0$ | **▼ 47.3 %** | **▼ 50.1 %** | **24 / 24 h (100 %)** |

---

## 🛠️ Arquitectura del Repositorio

```text
├── docs/                                 # Documentación y sustento teórico
│   ├── contexto_y_estrategia_reto_marees.md
│   ├── ecuaciones.tex                    # Deducción matemática y formulación física
│   └── Guía Reto MAREES...pdf
├── simulator/                            # Núcleo de cálculo y balance másico
│   ├── data_generator.py                 # Perfiles horarios sintéticos fundamentados
│   ├── soft_sensor.py                    # Estimador no lineal de DQO (Feedforward)
│   ├── uasb.py                           # Remoción anaerobia previa (~60%)
│   ├── aeration_tank.py                  # Leyes de control de potencia y demanda de O₂
│   ├── effluent_quality.py               # Verificación normativa Res. 0631
│   ├── economics.py                      # Balance financiero y cálculo del CEO
│   └── scenarios.py                      # Orquestador A vs B
├── config.py                             # Parámetros calibrables y constantes físicas
├── app.py                                # Dashboard interactivo en Plotly Dash
├── requirements.txt                      # Dependencias del proyecto
└── README.md
```

---

## 🚀 Instalación y Puesta en Marcha

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/camiloAndres11/OnionBlue.git
   cd OnionBlue
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el simulador interactivo:**
   ```bash
   python app.py
   ```

4. **Abrir en el navegador:**
   Visita [`http://127.0.0.1:8050`](http://127.0.0.1:8050) para interactuar con los escenarios, sliders de calibración, visualizaciones dinámicas y la tabla de auditoría horaria.
