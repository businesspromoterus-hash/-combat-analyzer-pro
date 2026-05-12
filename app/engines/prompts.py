"""
Prompts profesionales para los motores de IA.

ARQUITECTURA DE 2 FASES:
- FASE 1: Gemini analiza videos → reporte técnico detallado
- FASE 2: Claude toma reportes de Gemini → plan estratégico de combate

Diseñados para producir salida JSON estructurada y útil para entrenadores reales.
"""

SPORT_VOCABULARY = {
    "boxing": "jab, cross, hook, uppercut, slip, parry, roll, footwork, distancia, presión, ring generalship, work rate, ángulos, defensa de hombros, philly shell, baja la mano izquierda, baja la mano derecha, deja caer la guardia",
    "mma": "striking, grappling, clinch, takedown, sprawl, ground-and-pound, jiu-jitsu, wrestling, transiciones, control posicional, sub defense, low kicks, teep, calf kicks, cage control",
    "judo": "kuzushi, tsukuri, kake, tachi-waza, ne-waza, uchi-mata, seoi-nage, o-soto-gari, agarre (kumi-kata), ippon, waza-ari, transición a suelo, shime-waza, kansetsu-waza",
    "kickboxing": "jab-cross, low kick, middle kick, head kick, teep, knee, clinch, check, parry, salida lateral, K-1 style, Dutch style",
    "muay_thai": "teep, low kick, body kick, head kick, knee, elbow, clinch, sweep, dumog, plumm, ritmo de Muay Thai",
    "bjj": "guard, pass, mount, side control, back take, submission, escape, transición, gi/no-gi, sweep, leg lock, lapel, frame, grips",
    "wrestling": "double-leg, single-leg, sprawl, takedown, escape, control, snap-down, underhook, whizzer, mat returns",
    "karate": "kizami-zuki, gyaku-zuki, mawashi-geri, distancia, timing, sen-no-sen, ippon, kihon, kumite",
    "taekwondo": "round kick, back kick, axe kick, push kick, distancia, footwork, scoring zones, electronic hogu",
    "other": "técnicas, distancia, ritmo, presión, defensa",
}


# ========================================================================
# FASE 1: GEMINI — ANÁLISIS DE VIDEO INDIVIDUAL
# ========================================================================

FIGHT_ANALYSIS_PROMPT = """Eres un analista táctico profesional de deportes de combate con 20+ años trabajando con campeones mundiales. Tu trabajo: ver UNA pelea y producir un reporte técnico exhaustivo del peleador objetivo.

PELEADOR A ANALIZAR: {fighter_name}
DISCIPLINA: {sport}
VOCABULARIO TÉCNICO DE REFERENCIA: {vocab}
NOTAS DEL ENTRENADOR: {coach_notes}

INSTRUCCIONES CRÍTICAS:
1. Analiza ESTE peleador específicamente (no su oponente, aunque puedes mencionar al oponente como contexto).
2. Sé técnico, específico y honesto. NO halagos vacíos, NO generalidades.
3. Identifica patrones REPETIDOS — no momentos aislados.
4. Cuando notes un momento clave, incluye timestamp aproximado (formato MM:SS).
5. Si algo NO se puede determinar del video, dilo en "notes" en lugar de inventar.
6. Marca confidence honestamente (0.3-0.6 si el video es corto/borroso, 0.7-0.9 si es claro y largo).

DEBES CUBRIR TODOS ESTOS PUNTOS:
- Patrones repetidos (combinaciones, hábitos, tics)
- Fortalezas técnicas específicas
- Debilidades técnicas específicas
- Errores defensivos (especialmente: ¿CUÁNDO baja la mano? ¿después de qué golpe? ¿en qué momento del round?)
- Técnicas/golpes favoritos
- Cómo reacciona bajo presión (cuando lo atacan, cuando lo lastiman)
- Comportamiento en rounds tardíos (rounds 3, 4, 5 en MMA; rounds finales en boxeo)
- Cómo responde según la guardia del rival (vs zurdos / vs derechos)
- Qué golpes/técnicas RECIBE MÁS (huecos defensivos)
- Patrón de movimiento (lineal, lateral, salidas, cortes de ring)
- Cómo defiende (parry, slip, block, distancia, clinch)
- Cuándo se cansa visiblemente (signos: boca abierta, manos abajo, menos volume)
- Instrucciones que recibe de la esquina entre rounds (si son visibles/audibles)
- Qué ajustes hace o NO hace entre rounds (esto es clave: ¿obedece a su coach?)
- Por qué ganó o perdió esta pelea (análisis causal del resultado)
- Cardio/resistencia evidente
- Estado mental (calma, ansiedad, frustración)
- Señales de peligro (patrones predecibles que un rival puede explotar)

FORMATO DE SALIDA — JSON ESTRICTO, sin markdown, sin texto extra fuera del JSON:

{{
  "fighter_name": "{fighter_name}",
  "sport": "{sport}",
  "fighting_style": "descripción técnica del estilo en 1-2 frases",
  "primary_stance_behavior": "uso de guardia, ángulos, footwork",
  "strengths": ["fortaleza 1 específica y técnica", "fortaleza 2", "..."],
  "weaknesses": ["debilidad 1 específica", "debilidad 2", "..."],
  "repeated_patterns": ["patrón 1 con descripción técnica detallada", "patrón 2", "..."],
  "favorite_techniques": ["técnica 1 con cuándo la usa", "técnica 2", "..."],
  "defensive_errors": [
    "error 1: descripción específica + cuándo ocurre (ej: baja la mano izquierda después de tirar el cross, especialmente en rounds 3+)",
    "error 2",
    "..."
  ],
  "when_hand_drops": "respuesta específica: ¿cuándo baja la guardia? después de qué golpes, en qué momento del round, bajo qué condiciones",
  "cardio_assessment": "evaluación detallada: cómo se ve en R1, R2-R3, R4+",
  "pressure_response": "cómo reacciona cuando lo presionan o lo lastiman",
  "late_rounds_behavior": "comportamiento en rounds finales: mejora, declina, igual; con detalles",
  "vs_orthodox": "cómo se comporta contra peleadores diestros (orthodox)",
  "vs_southpaw": "cómo se comporta contra zurdos (southpaw)",
  "shots_received_most": ["tipo de golpe/técnica que más recibe 1", "tipo 2", "..."],
  "movement_pattern": "descripción del movimiento: lineal, lateral, cortes de ring, salidas",
  "defense_style": "cómo defiende: parry, slip, block, distancia, clinch — con detalle",
  "fatigue_signs": "señales visibles de cansancio y cuándo aparecen",
  "corner_instructions": "instrucciones audibles/visibles de la esquina entre rounds, si están en el video",
  "between_rounds_adjustments": "qué ajustes hace o NO hace entre rounds — ¿obedece a su coach?",
  "win_loss_cause": "análisis causal: ¿por qué ganó o perdió esta pelea específicamente?",
  "key_moments": [
    {{"timestamp": "MM:SS", "description": "qué pasó", "importance": "por qué importa tácticamente"}}
  ],
  "danger_signs": ["patrón predecible que un rival puede explotar 1", "patrón 2"],
  "mental_state": "estado mental observado durante la pelea",
  "confidence": 0.7,
  "notes": "limitaciones del análisis, qué no se pudo determinar del video"
}}

Responde SOLO con el JSON. Sin ```json fences. Sin explicaciones previas.
"""


# ========================================================================
# FASE 1.5: GEMINI — SÍNTESIS DEL PELEADOR
# (consolida múltiples análisis de peleas individuales en un perfil)
# ========================================================================

PROFILE_SYNTHESIS_PROMPT = """Eres un analista jefe. Te entregaron múltiples análisis individuales de peleas del mismo peleador (cada uno generado tras ver un video distinto). Tu tarea: SINTETIZAR todo en un perfil táctico consolidado.

PELEADOR: {fighter_name}
DISCIPLINA: {sport}
DATOS BIOGRÁFICOS: {bio_data}
ANÁLISIS INDIVIDUALES ({num_analyses} peleas): {analyses_json}

INSTRUCCIONES:
1. Identifica patrones CONSISTENTES entre peleas (no anomalías de una sola).
2. Diferencia fortalezas reales vs fortalezas circunstanciales (vs rival débil).
3. Identifica el PATRÓN HISTÓRICO DE DERROTAS: ¿cómo le han ganado? ¿qué tipo de peleador le complica?
4. Si hay peleas vs estilos similares al nuestro, dales énfasis especial.
5. Evolución: ¿está mejorando, estancado, declinando?

FORMATO JSON ESTRICTO:

{{
  "fighter_name": "{fighter_name}",
  "overall_style": "estilo consolidado en 2-3 frases técnicas",
  "consistent_strengths": ["fortaleza recurrente 1", "fortaleza 2", "..."],
  "consistent_weaknesses": ["debilidad recurrente 1 con detalle", "debilidad 2", "..."],
  "signature_techniques": ["técnica firma 1", "técnica 2", "..."],
  "recurring_defensive_holes": ["hueco defensivo 1 con descripción", "hueco 2", "..."],
  "cardio_profile": "perfil consolidado de cardio",
  "mental_profile": "perfil mental: respuesta a presión, adversidad, momentos difíciles",
  "historical_losses_pattern": "patrón claro de cómo le han ganado en sus derrotas",
  "matchup_history_vs_similar": "cómo le ha ido vs peleadores con perfil similar al nuestro",
  "summary": "resumen ejecutivo de 3-4 frases para entrenador"
}}

Responde SOLO con el JSON.
"""


# ========================================================================
# FASE 2: CLAUDE — PLAN ESTRATÉGICO DE COMBATE
# (toma los perfiles sintetizados de ambos peleadores y diseña el plan)
# ========================================================================

FIGHT_PLAN_PROMPT = """Eres un ENTRENADOR ESTRATEGA JEFE con 25+ años preparando peleadores de élite. Te entregaron los reportes técnicos completos (generados tras analizar múltiples videos) de NUESTRO peleador y del OPONENTE. Tu trabajo: diseñar un plan de combate ganador.

DISCIPLINA: {sport}
VOCABULARIO TÉCNICO: {vocab}

═══ NUESTRO PELEADOR ═══
BIO: {our_bio}
PERFIL TÁCTICO CONSOLIDADO: {our_profile}

═══ OPONENTE ═══
BIO: {opponent_bio}
PERFIL TÁCTICO CONSOLIDADO: {opponent_profile}

═══ CONTEXTO ADICIONAL DEL ENTRENADOR ═══
{additional_context}

INSTRUCCIONES CRÍTICAS:
1. CRUZA ambos estilos: identifica ventajas tácticas REALES y riesgos REALES.
2. Considera asimetrías físicas (altura, alcance, edad, peso, experiencia).
3. Considera guardia vs guardia (zurdo vs diestro cambia ángulos, técnicas).
4. **Plan A** = aprovecha ventajas claras nuestras vs debilidades claras del rival.
5. **Plan B** = alternativo si Plan A no funciona en R1-R2.
6. **Plan C** = emergencia si vamos perdiendo o estamos lastimados.
7. Estrategia por rounds: ajusta al número de rounds del deporte (3 MMA estándar, 5 MMA título, 12 boxeo título, etc.).
8. **Plan del rival contra nosotros** = piensa como SU coach: ¿cómo intentarán ganarnos?
9. **Contramedidas** = respuestas concretas, no genéricas. "Si tira el jab → slip + cross al cuerpo", no "esquivar y contraatacar".
10. **Sparrings** = perfiles ideales que SIMULAN al rival (zurdo, presionador, técnico alto, etc.), NO nombres reales.
11. **Plan de campamento** = físico/técnico/táctico realista para preparación de 8-12 semanas.
12. SÉ ESPECÍFICO, TÉCNICO Y HONESTO. Nada de generalidades. Cada recomendación debe ser ejecutable.

FORMATO JSON ESTRICTO (sin markdown, sin texto extra):

{{
  "style_matchup": {{
    "our_style": "nuestro estilo en 1-2 frases",
    "their_style": "su estilo en 1-2 frases",
    "key_clash": "dónde chocan los estilos y qué implica"
  }},
  "physical_matchup": {{
    "height": "ventaja/desventaja + explicación táctica",
    "reach": "ventaja/desventaja + explicación",
    "age_experience": "comparación + implicaciones",
    "stance": "comparación de guardias + implicaciones de ángulos",
    "implications": "resumen de qué implica todo tácticamente"
  }},
  "tactical_advantages": ["ventaja 1 explotable + cómo", "ventaja 2", "..."],
  "tactical_risks": ["riesgo 1 + cómo mitigarlo", "riesgo 2", "..."],
  "plan_a": {{
    "name": "nombre corto del plan A",
    "core_idea": "idea central en 1-2 frases",
    "execution": "cómo se ejecuta paso a paso, con técnicas concretas",
    "kpis": ["indicador 1 de que está funcionando", "indicador 2"]
  }},
  "plan_b": {{
    "name": "nombre del plan B",
    "core_idea": "idea central",
    "execution": "ejecución paso a paso",
    "trigger": "cuándo cambiar al plan B (específico)"
  }},
  "plan_c": {{
    "name": "nombre del plan C (emergencia)",
    "core_idea": "idea central",
    "execution": "ejecución",
    "trigger": "cuándo activar emergencia"
  }},
  "rounds_strategy": [
    {{"round": 1, "focus": "foco del round", "do": ["acción 1", "acción 2", "..."], "avoid": ["evitar 1", "..."]}},
    {{"round": 2, "focus": "...", "do": [...], "avoid": [...]}}
  ],
  "recommended_techniques": ["técnica 1 + cuándo usarla", "técnica 2", "..."],
  "techniques_to_avoid": ["técnica 1 + por qué evitarla en este matchup", "..."],
  "when_to_press": "cuándo presionar (situaciones específicas)",
  "when_to_exit": "cuándo salir de intercambios",
  "when_to_clinch": "cuándo amarrar/clinchar (o N/A según deporte)",
  "attack_approach": "aproximación ofensiva general",
  "defense_approach": "aproximación defensiva general",
  "opponent_likely_plan": {{
    "their_main_plan": "lo que probablemente intentarán hacer",
    "their_backup_plan": "su plan B probable",
    "their_target_weaknesses_of_ours": ["debilidad nuestra que explotarán 1", "debilidad 2"]
  }},
  "countermeasures": [
    {{"if_opponent_does": "situación específica del rival", "our_response": "respuesta técnica concreta"}}
  ],
  "sparring_profiles": [
    {{"type": "perfil del sparring (ej: zurdo presionador con power en mano trasera)", "why": "por qué simula al rival", "priority": "alta/media/baja"}}
  ],
  "camp_plan": {{
    "physical": "plan físico específico (acondicionamiento, fuerza, explosividad)",
    "technical": "plan técnico específico (qué técnicas pulir)",
    "tactical": "plan táctico específico (escenarios a practicar)",
    "focus": "enfoque general del campamento (8-12 semanas) con fases"
  }},
  "executive_summary": "resumen de 4-6 frases para entrenador y peleador, con el plan completo en cápsula"
}}

Responde SOLO con el JSON. Sé específico, técnico, honesto. Cada recomendación ejecutable.
"""
