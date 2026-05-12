"""
Generador de PDF profesional del plan de combate.

Diseñado para entrenador y peleador: limpio, técnico, accionable.
"""
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from app.core.config import settings


# Paleta de colores profesional
NAVY = colors.HexColor("#0B1F3A")
RED = colors.HexColor("#C8102E")
GOLD = colors.HexColor("#C9A961")
GREY_DARK = colors.HexColor("#2D2D2D")
GREY_LIGHT = colors.HexColor("#E8E8E8")
WHITE = colors.white


def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=26, textColor=NAVY,
            alignment=TA_CENTER, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"],
            fontName="Helvetica", fontSize=11, textColor=GREY_DARK,
            alignment=TA_CENTER, spaceAfter=20,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"],
            fontName="Helvetica-Bold", fontSize=16, textColor=WHITE,
            backColor=NAVY, borderPadding=8, spaceBefore=18, spaceAfter=10,
            leftIndent=0,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=13, textColor=NAVY,
            spaceBefore=12, spaceAfter=6, borderColor=GOLD,
            borderWidth=0, leftIndent=0,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"],
            fontName="Helvetica-Bold", fontSize=11, textColor=RED,
            spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, textColor=GREY_DARK,
            alignment=TA_JUSTIFY, spaceAfter=6, leading=14,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, textColor=GREY_DARK,
            leftIndent=14, bulletIndent=4, spaceAfter=3, leading=13,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9, textColor=NAVY,
            spaceAfter=2,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, textColor=GREY_DARK,
            alignment=TA_CENTER,
        ),
    }
    return styles


def _bullet_list(items: list[str], styles) -> list:
    """Convierte una lista de strings en flowables con bullets."""
    if not items:
        return [Paragraph("— sin datos —", styles["body"])]
    out = []
    for it in items:
        out.append(Paragraph(f"• {it}", styles["bullet"]))
    return out


def _section_header(text: str, styles) -> Paragraph:
    return Paragraph(text.upper(), styles["h1"])


def _bio_table(bio: dict, styles) -> Table:
    """Tabla limpia con datos bio del peleador."""
    rows = [
        ["Nombre", bio.get("name", "—")],
        ["Disciplina", bio.get("sport", "—")],
        ["País", bio.get("country", "—")],
        ["Récord", bio.get("record", "—")],
        ["Edad", str(bio.get("age", "—"))],
        ["Peso", f"{bio.get('weight_kg', '—')} kg" if bio.get("weight_kg") else "—"],
        ["División", bio.get("division", "—")],
        ["Estatura", f"{bio.get('height_cm', '—')} cm" if bio.get("height_cm") else "—"],
        ["Alcance", f"{bio.get('reach_cm', '—')} cm" if bio.get("reach_cm") else "—"],
        ["Guardia", bio.get("stance", "—")],
        ["Experiencia", f"{bio.get('years_experience', '—')} años" if bio.get("years_experience") else "—"],
    ]
    tbl = Table(rows, colWidths=[1.4 * inch, 2.6 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GREY_LIGHT),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.white),
    ]))
    return tbl


def _plan_box(plan: dict, label: str, styles) -> KeepTogether:
    """Caja visual para Plan A/B/C."""
    flowables = [
        Paragraph(f"{label}: {plan.get('name', '—')}", styles["h3"]),
        Paragraph(f"<b>Idea central:</b> {plan.get('core_idea', '—')}", styles["body"]),
        Paragraph(f"<b>Ejecución:</b> {plan.get('execution', '—')}", styles["body"]),
    ]
    if plan.get("trigger"):
        flowables.append(Paragraph(f"<b>Cuándo activarlo:</b> {plan['trigger']}", styles["body"]))
    if plan.get("kpis"):
        flowables.append(Paragraph("<b>KPIs (cómo medir si funciona):</b>", styles["label"]))
        flowables.extend(_bullet_list(plan["kpis"], styles))
    flowables.append(Spacer(1, 6))
    return KeepTogether(flowables)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY_DARK)
    canvas.drawString(0.75 * inch, 0.4 * inch, "Combat Analyzer Pro")
    canvas.drawCentredString(letter[0] / 2, 0.4 * inch, f"Página {doc.page}")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.4 * inch,
                           datetime.utcnow().strftime("%Y-%m-%d"))
    canvas.restoreState()


def generate_fight_plan_pdf(
    plan_data: dict,
    our_bio: dict,
    opponent_bio: dict,
    output_path: Path,
) -> Path:
    """
    Genera PDF profesional del plan de combate.
    Devuelve el path del PDF generado.
    """
    styles = _build_styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        title="Plan de Combate - Combat Analyzer Pro",
        author="Combat Analyzer Pro",
    )

    story: list[Any] = []

    # ========== PORTADA ==========
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("PLAN DE COMBATE", styles["title"]))
    story.append(Paragraph(
        f"{our_bio.get('name', '—')}  vs  {opponent_bio.get('name', '—')}",
        styles["subtitle"],
    ))
    story.append(Paragraph(
        f"Disciplina: {our_bio.get('sport', '—').upper()}", styles["subtitle"]
    ))
    story.append(HRFlowable(width="60%", thickness=2, color=GOLD,
                            hAlign="CENTER", spaceBefore=10, spaceAfter=10))
    story.append(Paragraph(
        f"Reporte generado: {datetime.utcnow().strftime('%d/%m/%Y')}",
        styles["small"],
    ))
    story.append(Paragraph("Documento confidencial — uso interno del equipo",
                           styles["small"]))
    story.append(PageBreak())

    # ========== RESUMEN EJECUTIVO ==========
    story.append(_section_header("Resumen Ejecutivo", styles))
    story.append(Paragraph(plan_data.get("executive_summary", "—"), styles["body"]))
    story.append(Spacer(1, 12))

    # ========== PERFILES DE PELEADORES ==========
    story.append(_section_header("Perfiles", styles))

    story.append(Paragraph("Nuestro Peleador", styles["h2"]))
    story.append(_bio_table(our_bio, styles))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Oponente", styles["h2"]))
    story.append(_bio_table(opponent_bio, styles))
    story.append(PageBreak())

    # ========== CRUCE DE ESTILOS ==========
    story.append(_section_header("Cruce de Estilos", styles))
    sm = plan_data.get("style_matchup", {})
    story.append(Paragraph(f"<b>Nuestro estilo:</b> {sm.get('our_style', '—')}", styles["body"]))
    story.append(Paragraph(f"<b>Su estilo:</b> {sm.get('their_style', '—')}", styles["body"]))
    story.append(Paragraph(f"<b>Choque clave:</b> {sm.get('key_clash', '—')}", styles["body"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Asimetrías Físicas", styles["h2"]))
    pm = plan_data.get("physical_matchup", {})
    for k_label, k_field in [("Estatura", "height"), ("Alcance", "reach"),
                              ("Edad/Experiencia", "age_experience"),
                              ("Guardia", "stance"),
                              ("Implicaciones", "implications")]:
        story.append(Paragraph(f"<b>{k_label}:</b> {pm.get(k_field, '—')}", styles["body"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Ventajas Tácticas", styles["h2"]))
    story.extend(_bullet_list(plan_data.get("tactical_advantages", []), styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Riesgos Tácticos", styles["h2"]))
    story.extend(_bullet_list(plan_data.get("tactical_risks", []), styles))
    story.append(PageBreak())

    # ========== PLANES A / B / C ==========
    story.append(_section_header("Planes de Combate", styles))
    if plan_data.get("plan_a"):
        story.append(_plan_box(plan_data["plan_a"], "PLAN A", styles))
    if plan_data.get("plan_b"):
        story.append(_plan_box(plan_data["plan_b"], "PLAN B", styles))
    if plan_data.get("plan_c"):
        story.append(_plan_box(plan_data["plan_c"], "PLAN C (EMERGENCIA)", styles))
    story.append(PageBreak())

    # ========== ESTRATEGIA POR ROUNDS ==========
    story.append(_section_header("Estrategia por Round", styles))
    for r in plan_data.get("rounds_strategy", []):
        story.append(Paragraph(f"Round {r.get('round', '?')}: {r.get('focus', '')}",
                               styles["h3"]))
        story.append(Paragraph("<b>Hacer:</b>", styles["label"]))
        story.extend(_bullet_list(r.get("do", []), styles))
        story.append(Paragraph("<b>Evitar:</b>", styles["label"]))
        story.extend(_bullet_list(r.get("avoid", []), styles))
        story.append(Spacer(1, 8))
    story.append(PageBreak())

    # ========== TÉCNICAS Y MOMENTOS ==========
    story.append(_section_header("Tácticas Específicas", styles))

    story.append(Paragraph("Técnicas Recomendadas", styles["h2"]))
    story.extend(_bullet_list(plan_data.get("recommended_techniques", []), styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Técnicas a Evitar", styles["h2"]))
    story.extend(_bullet_list(plan_data.get("techniques_to_avoid", []), styles))
    story.append(Spacer(1, 6))

    for label, field in [("Cuándo presionar", "when_to_press"),
                          ("Cuándo salir", "when_to_exit"),
                          ("Cuándo amarrar/clinchar", "when_to_clinch"),
                          ("Aproximación ofensiva", "attack_approach"),
                          ("Aproximación defensiva", "defense_approach")]:
        story.append(Paragraph(label, styles["h3"]))
        story.append(Paragraph(plan_data.get(field, "—"), styles["body"]))

    story.append(PageBreak())

    # ========== PLAN DEL RIVAL + CONTRAMEDIDAS ==========
    story.append(_section_header("Plan Probable del Rival", styles))
    olp = plan_data.get("opponent_likely_plan", {})
    story.append(Paragraph(f"<b>Su plan principal:</b> {olp.get('their_main_plan', '—')}",
                           styles["body"]))
    story.append(Paragraph(f"<b>Su plan de respaldo:</b> {olp.get('their_backup_plan', '—')}",
                           styles["body"]))
    story.append(Paragraph("<b>Debilidades nuestras que intentarán explotar:</b>",
                           styles["label"]))
    story.extend(_bullet_list(olp.get("their_target_weaknesses_of_ours", []), styles))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Contramedidas", styles["h2"]))
    cm_rows = [["Si el rival hace…", "Nuestra respuesta"]]
    for cm in plan_data.get("countermeasures", []):
        cm_rows.append([cm.get("if_opponent_does", "—"), cm.get("our_response", "—")])
    if len(cm_rows) > 1:
        cm_tbl = Table(cm_rows, colWidths=[3.2 * inch, 3.2 * inch], repeatRows=1)
        cm_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, GREY_LIGHT),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ]))
        story.append(cm_tbl)
    story.append(PageBreak())

    # ========== SPARRINGS ==========
    story.append(_section_header("Perfiles de Sparring Recomendados", styles))
    sp_rows = [["Perfil", "Por qué simula al rival", "Prioridad"]]
    for sp in plan_data.get("sparring_profiles", []):
        sp_rows.append([
            sp.get("type", "—"),
            sp.get("why", "—"),
            sp.get("priority", "—").upper(),
        ])
    if len(sp_rows) > 1:
        sp_tbl = Table(sp_rows, colWidths=[2.0 * inch, 3.6 * inch, 0.9 * inch], repeatRows=1)
        sp_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), RED),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, GREY_LIGHT),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ]))
        story.append(sp_tbl)
    story.append(PageBreak())

    # ========== CAMPAMENTO ==========
    story.append(_section_header("Plan de Campamento", styles))
    cp = plan_data.get("camp_plan", {})
    for label, field in [("Físico", "physical"), ("Técnico", "technical"),
                          ("Táctico", "tactical"), ("Enfoque general (8-12 semanas)", "focus")]:
        story.append(Paragraph(label, styles["h3"]))
        story.append(Paragraph(cp.get(field, "—"), styles["body"]))
        story.append(Spacer(1, 4))

    # ========== CIERRE ==========
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Este reporte es una herramienta táctica. La ejecución, ajustes en vivo "
        "y juicio del entrenador en esquina son irreemplazables.",
        styles["small"],
    ))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output_path


def generate_pdf_for_plan(plan_record, our_bio: dict, opponent_bio: dict) -> Path:
    """Wrapper conveniente: genera el PDF y devuelve el path."""
    filename = f"plan_{plan_record.id}_{plan_record.our_fighter_id}_vs_{plan_record.opponent_id}.pdf"
    output = settings.reports_path / filename
    return generate_fight_plan_pdf(
        plan_data=plan_record.plan,
        our_bio=our_bio,
        opponent_bio=opponent_bio,
        output_path=output,
    )
