# Contexto y Estrategia de Solución — Reto MAREES: "Cada gota cuenta" (Blue Onion Lab 2026)

## 1. El Problema Central y la Meta de la Hackatón

### 1.1. El Fenómeno Físico y Operativo
En una Planta de Tratamiento de Aguas Residuales (PTAR) municipal, el agua cruda que ingresa desde el alcantarillado (**influente**) cambia constantemente a lo largo de las 24 horas del día:
* **Variabilidad horaria (Curva de "doble joroba"):** Existen valles pronunciados en la madrugada (00:00 a 05:00 h, con caudales y cargas del $55\text{ \%} - 65\text{ \%}$ respecto a la media) y dos picos marcados: uno en la mañana (08:00 a 10:00 h) y otro más alto en la tarde/noche (17:00 a 19:00 h, alcanzando $140\text{ \%} - 150\text{ \%}$ de la referencia).
* **El problema de la operación estática (Escenario A - Línea Base):** Muchas plantas operan con consignas fijas o preprogramadas dimensionadas para soportar las horas pico. Esto provoca que en las horas valle se **sobre-airee** el agua (desperdiciando electricidad) o se dosifiquen insumos innecesarios, mientras que ante perturbaciones extremas el sistema puede quedar corto y comprometer la calidad del agua vertida al río.

### 1.2. La Pregunta Retadora y Meta Aspiracional
> *¿Es posible tratar aguas residuales con un **25 % menos de costos operativos específicos ($\text{COP/m}^3$)**, tomando mejores decisiones frente a los cambios del agua que ingresa y sin comprometer la calidad del agua que devolvemos al ambiente?*

* **Naturaleza del 25 %:** Es una **meta aspiracional de diseño**, no eliminatoria. El jurado evalúa el rigor matemático, la trazabilidad de los datos y la coherencia física/química/biológica de las decisiones, por encima de cifras infladas sin sustento.
* **Nivel exigido (Nivel 2 - Simulación Adaptativa):** Desarrollar un prototipo conceptual o computacional que compare bajo las mismas entradas el **Escenario A (Línea Base Fija)** frente al **Escenario B (Propuesta Adaptativa)**.

---

## 2. El Proceso de Referencia (Arquitectura Tipo PTAR Tunja)

El sistema toma como referencia un prestador de servicio público de alcantarillado con la arquitectura operativa documentada para **Tunja (Boyacá)**, compuesta por una línea de agua en serie y una línea lateral de lodos:

1. **ENTRADA (Influente):** Ingresa agua residual doméstica/municipal con variaciones en Caudal ($Q$), carga orgánica ($\text{DQO}$, $\text{DBO}_5$), Sólidos Suspendidos Totales ($\text{SST}$), Nitrógeno amoniacal ($\text{N-NH}_4^+$), $\text{pH}$, Temperatura ($T$) y Alcalinidad.
2. **PRETRATAMIENTO (Preliminar):** Rejas de cribado, desarenado y trampas de grasas. Retiene sólidos gruesos y arena. *(Variables clave: Caudal $Q$, frecuencia de limpieza, pérdidas de carga).*
3. **BIOLÓGICO 1 (Reactor UASB):** Reactor Anaerobio de Flujo Ascendente con Manto de Lodos. Microorganismos anaerobios (sin oxígeno) degradan entre el $55\text{ \%}$ y $65\text{ \%}$ de la materia orgánica inicial sin gastar electricidad en aireación y generando biogás como subproducto. *(Variables clave: Carga orgánica, temperatura $T$, $\text{pH}$ y estabilidad).*
4. **BIOLÓGICO 2 (Etapa Aerobia / Tanque Aireado):** Recibe la **carga orgánica remanente** que sale del UASB y el nitrógeno amoniacal. Bacterias aerobias heterótrofas y nitrificantes oxidan los contaminantes usando el oxígeno inyectado por **sopladores eléctricos industriales**. *(Variables clave: Oxígeno Disuelto $\text{OD}$, intensidad/tiempo de aireación y potencia eléctrica en $\text{kW}$).*
5. **SEPARACIÓN (Clarificador / Sedimentación Secundaria):** Separa por gravedad el agua limpia de los flóculos biológicos (biomasa). *(Variables clave: $\text{SST}$ de salida, recirculación/purga de lodos y dosificación contingente de coagulantes/floculantes).*
6. **SALIDA (Efluente):** Descarga a cuerpo de agua superficial cumpliendo límites legales.
7. **LÍNEA DE SUBPRODUCTOS (Lodos):** Extracción, espesamiento, deshidratación y disposición o aprovechamiento de lodos. *(Variables clave: Cantidad de lodos en $\text{kg}$ y costos asociados).*

---

## 3. Marco Normativo Colombiano y Referentes Internacionales

### 3.1. Límites Legales de Salida (Resolución 0631 de 2015, Art. 8)
La norma regula **el efluente (salida)**, no la entrada. Según la carga másica de la planta ($\text{kg/d}$ de $\text{DBO}_5$), el agua tratada nunca debe superar:

| Parámetro | Unidad | Tramo 1 ($\le 625\text{ kg/d}$) | Tramo 2 ($> 625\text{ a }\le 3.000\text{ kg/d}$) | Tramo 3 ($> 3.000\text{ kg/d}$) |
| :--- | :--- | :---: | :---: | :---: |
| **pH** | Unidades | $6,0 - 9,0$ | $6,0 - 9,0$ | $6,0 - 9,0$ |
| **DQO** | $\text{mg O}_2\text{/L}$ | $180$ | $180$ | $150$ |
| **$\text{DBO}_5$** | $\text{mg O}_2\text{/L}$ | $90$ | $90$ | $70$ |
| **SST** | $\text{mg/L}$ | $90$ | $90$ | $70$ |
| **Sólidos sedimentables** | $\text{mL/L}$ | $5$ | $5$ | $5$ |
| **Grasas y aceites** | $\text{mg/L}$ | $20$ | $20$ | $10$ |

*(Adicionalmente existen parámetros de "Análisis y reporte" como Nitrógeno amoniacal, Nitratos, Nitritos, Fósforo total, Ortofosfatos y SAAM).*

### 3.2. Uso Correcto de los 4 Referentes de la Guía (Prohibido mezclarlos en una planta ficticia)
* **Tunja (Boyacá):** Define la **arquitectura del proceso** (Preliminar $\rightarrow$ UASB $\rightarrow$ Aireación $\rightarrow$ Clarificador). No tiene datos públicos horarios abiertos, por lo que los datos simulados deben declararse como *sintéticos fundamentados*.
* **PTAR Salitre (Bogotá, 2024):** Referencia de costos en Colombia (Personal: $\$17,19\text{ mil M COP}$; Energía: $\$13,77\text{ mil M COP}$; Químicos: $\$8,39\text{ mil M COP}$). Muestra que energía y químicos son los rubros variables más atacables.
* **Polonia (Estudio 2025):** Referencia de **consumo eléctrico específico** a nivel planta: rango de $0,92\text{ a }1,20\text{ kWh/m}^3$ (promedio $1,04\text{ kWh/m}^3$), con cobertura de $18,1\text{ \% a }68,4\text{ \%}$ mediante biogás.
* **Reino Unido (Severn Trent, Jacobs 2018):** Referencia de distribución porcentual de costos locales: Personal ($41,4\text{ \%}$), Electricidad ($39,2\text{ \%}$), Contratación ($8,7\text{ \%}$), Químicos ($7,4\text{ \%}$) y Materiales ($3,3\text{ \%}$).

---

## 4. Qué Queremos Hacer: Estrategia de Solución del Equipo

### 4.1. Delimitación de la Frontera del Sistema
Siguiendo la directriz de la Sección 8 de la guía, **delimitamos la frontera de optimización al bloque de Tratamiento Secundario Aerobio (Tanque Aireado) + Dosificación Química Contingente en Clarificación**, considerando el efecto previo del Reactor UASB:
* **¿Por qué esta frontera?** El personal ($41,4\text{ \%}$ del costo total de una PTAR) es un costo fijo que no varía hora a hora. En cambio, la **aireación eléctrica** en el reactor aerobio y la **dosificación de reactivos** son los mayores costos variables horarios. Al declarar explícitamente esta frontera, podemos demostrar una reducción cercana o superior al **25 % en el $\text{CEO}$ ($\text{COP/m}^3$)** de este subsistema de forma 100 % transparente y físicamente real.

### 4.2. Arquitectura de Control Híbrida: Soft-Sensor (Feedforward) + Control OD (Feedback)
El problema técnico principal para un sistema de control en una PTAR es que la $\text{DQO}$ y la $\text{DBO}_5$ son **variables de laboratorio** (tardan entre horas y 5 días en medirse) y no están disponibles en tiempo real cada hora. Nuestra solución integra tres módulos lógicos:

1. **Módulo 1 — Soft-Sensor de Carga Orgánica Instantánea (*Feedforward*):**
   Usa variables que sí se miden en línea cada hora (Caudal $Q(t)$, $\text{pH}$, Temperatura $T$ y turbidez/conductividad) para estimar en tiempo real la concentración de $\text{DQO}_{\text{est}}(t)$ y la carga orgánica entrante $L_{\text{DQO}}(t)$ antes de tener resultados de laboratorio.
2. **Módulo 2 — Modulación Adaptativa de Sopladores en Tanque Aireado (*Feedback con OD*):**
   Calcula la carga remanente tras el UASB y ajusta cada hora la potencia eléctrica ($P_{\text{prop}}(t)$ en $\text{kW}$) y el flujo de aire ($\text{m}^3\text{/h}$) de los sopladores usando variadores de frecuencia (VFD), corrigiendo en lazo cerrado con la lectura del sensor en línea de **Oxígeno Disuelto ($\text{OD}$)** para mantenerlo en su consigna óptima ($1,5 - 2,0\text{ mg/L}$) sin sobre-airear en horas valle.
3. **Módulo 3 — Dosificación Química por Umbrales (Solo en Perturbaciones):**
   En lugar de mantener bombas dosificadoras encendidas por rutina, la dosis de químicos ($\text{kg/h}$) se mantiene en $0$ durante la jornada ordinaria (donde la biología basta) y **solo se activa automáticamente** cuando el sistema detecta una **Punta Hidráulica** (riesgo de lavado de $\text{SST}$ en el clarificador) o un **Choque de Carga / Caída de Alcalinidad-pH**.

---

## 5. Formulación Matemática del Modelo de Simulación

### Paso 1: Estimación de Carga de Entrada mediante Soft-Sensor
La concentración estimada de $\text{DQO}$ en el instante $t$ se modela con un exponente de régimen $\alpha$ y un factor correctivo por choques de carga detectados en sensores en línea ($\text{pH}$ / caída de $\text{OD}$):

$$\text{DQO}_{\text{est}}(t) = \text{DQO}_{\text{base}} \times \left( \frac{Q(t)}{Q_{\text{med}}} \right)^\alpha \times f_{\text{choque}}(\Delta \text{pH}, \Delta \text{OD})$$

* **Régimen 1 (Jornada Ordinaria):** $\alpha \in [0,7 \, , \, 1,0]$ (la concentración sube y baja acompañando el caudal doméstico).
* **Régimen 2 (Punta Hidráulica por lluvia, cuando $Q(t) > Q_{\text{umbral\_lluvia}}$):** $\alpha < 0$ (ej. $\alpha = -0,5$, reflejando la dilución por agua lluvia).
* **Régimen 3 (Incremento de carga orgánica/nitrogenada sin aumento de caudal):** El factor $f_{\text{choque}} > 1$ se activa al detectar una caída brusca en el $\text{OD}$ del reactor o desviación de $\text{pH}$/conductividad.

La carga orgánica horaria entrante ($\text{kg DQO/h}$) es:

$$L_{\text{DQO}}(t) = \frac{Q(t) \times \text{DQO}_{\text{est}}(t)}{1000}$$

### Paso 2: Filtro del Reactor Anaerobio UASB (Biológico 1)
El reactor UASB remueve una fracción $\eta_{\text{UASB}}$ (típico $\approx 0,60$, modulada ligeramente por la Temperatura $T$ y el $\text{pH}$). La carga remanente que pasa al Tanque Aireado es:

$$L_{\text{rem}}(t) = L_{\text{DQO}}(t) \times \left( 1 - \eta_{\text{UASB}}(T, \text{pH}) \right)$$

### Paso 3: Demanda de Oxígeno y Potencia Eléctrica en Tanque Aireado (Biológico 2)
La demanda horaria de oxígeno ($\text{kg O}_2\text{/h}$) suma la oxidación de materia orgánica remanente y la nitrificación del nitrógeno amoniacal ($L_{\text{N}}(t)$):

$$R_{\text{O}_2}(t) = \left[ a \times L_{\text{rem}}(t) \right] + \left[ b \times L_{\text{N}}(t) \right]$$

*(Constantes estequiométricas típicas: $a \approx 1,0\text{ kg O}_2\text{/kg DQO}$; $b \approx 4,57\text{ kg O}_2\text{/kg N}$).*

Dada una eficiencia estándar de transferencia de los aireadores $\text{SAE}$ ($\text{kg O}_2\text{/kWh}$, típico $\approx 1,5\text{ kg O}_2\text{/kWh}$) y una potencia mínima de agitación $P_{\text{min}}$ para evitar sedimentación de biomasa:
* **Potencia en Escenario A (Línea Base Fija):** $P_{\text{base}}(t) = P_{\text{fija}}$ (constante las 24 h).
* **Potencia en Escenario B (Propuesta Adaptativa):**
  $$P_{\text{prop}}(t) = \max\left( P_{\text{min}}, \, \frac{R_{\text{O}_2}(t)}{\text{SAE}} \times \left[ 1 + k_{\text{OD}} \cdot (\text{OD}_{\text{meta}} - \text{OD}_{\text{medido}}(t)) \right] \right)$$

### Paso 4: Verificación Numérica de Calidad de Salida (Efluente)
La eficiencia biológica del tanque aireado depende del balance de oxígeno suministrado:

$$\eta_{\text{aerobio}}(t) = \eta_{\text{max}} \times \min\left( 1, \, \frac{P(t) \times \text{SAE}}{R_{\text{O}_2}(t)} \right)$$

La concentración de salida hacia el cuerpo receptor ($\text{mg O}_2\text{/L}$) es:

$$\text{DQO}_{\text{salida}}(t) = \frac{L_{\text{rem}}(t) \times \left( 1 - \eta_{\text{aerobio}}(t) \right) \times 1000}{Q(t)}$$

*(Restricción dura en cada hora $t$: $\text{DQO}_{\text{salida}}(t) \le 180\text{ mg/L}$, $\text{DBO}_{5\text{, salida}}(t) \le 90\text{ mg/L}$, $\text{SST}_{\text{salida}}(t) \le 90\text{ mg/L}$).*

### Paso 5: Métrica Económica Oficial de la Hackatón ($\text{CEO}$)
Integrando electricidad, reactivos químicos, gestión de lodos y costos adicionales de instrumentación/mantenimiento en las 24 horas:

$$\text{CEO} \, (\text{COP/m}^3) = \frac{\sum_{t=1}^{24} \left[ \text{Costo}_{\text{elec}}(t) + \text{Costo}_{\text{quím}}(t) + \text{Costo}_{\text{lodos/mant}}(t) \right]}{\sum_{t=1}^{24} Q(t)}$$

$$\text{Optimización de costo (\%)} = 100 \times \frac{\text{CEO}_{\text{base}} - \text{CEO}_{\text{propuesta}}}{\text{CEO}_{\text{base}}}$$

---

## 6. Checklist de Entregables Obligatorios (Secciones 6, 9 y 10 de la Guía)

Para asegurar el puntaje máximo frente al jurado, la simulación y presentación deben incluir:
- [ ] **Tres situaciones de prueba:** 1) Jornada ordinaria, 2) Punta hidráulica (lluvia), y 3) Incremento brusco de carga orgánica o nitrogenada.
- [ ] **Etiquetado de datos:** Marcar cada variable explícitamente como *medida, publicada, estimada o sintética* (sin atribuir datos sintéticos como mediciones reales de Tunja).
- [ ] **Mapa del proceso:** Diagrama ubicando el Soft-Sensor en la entrada/UASB y los actuadores en el Tanque Aireado y Clarificador.
- [ ] **Contabilización de efectos secundarios:** Incluir el costo extra puntual cuando el Escenario B sube la aireación al máximo o activa coagulantes durante las horas de perturbación, así como el costo de mantenimiento de la instrumentación.
- [ ] **Declaración de limitaciones:** Explicitar que es una simulación matemática de Nivel 2 (no validación industrial) y detallar la hoja de ruta para calibrar el exponente $\alpha$ con datos históricos en una PTAR real.