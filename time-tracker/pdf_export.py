"""PDF-Export für Zeiterfassung.

Exportiert den Vormonat (nicht fakturiert) gegliedert nach Kunde → Projekt,
mit Aufgaben, Notizen, Einzelzeiten und Gesamtsummen.
"""
from datetime import date
from typing import List, Dict, Optional
from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

import database as db
from models import TimeEntry


def _last_month_range():
    today = date.today()
    first_this = date(today.year, today.month, 1)
    import datetime as dt
    lm_end = first_this - dt.timedelta(days=1)
    lm_start = lm_end.replace(day=1)
    return lm_start.isoformat(), lm_end.isoformat()


def _format_hours(minutes: int) -> str:
    """Dezimalstunden mit deutschem Komma, z.B. 75 Min → '1,25 Std.'"""
    h = minutes / 60
    if h == int(h):
        return f"{int(h)} Std."
    return f"{h:.2f}".replace(".", ",") + " Std."


def export_pdf(
    filepath: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    only_not_invoiced: bool = True,
    parent_widget=None,
):
    """Erstellt das PDF. Wenn kein Zeitraum angegeben, wird der Vormonat verwendet."""
    if not date_from or not date_to:
        date_from, date_to = _last_month_range()

    entries = db.get_time_entries(date_from, date_to)
    if only_not_invoiced:
        entries = [e for e in entries if not e.invoiced]

    if not entries:
        if parent_widget:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(parent_widget, "Export", "Keine nicht-fakturierten Einträge im gewählten Zeitraum.")
        return

    # ── Dokument ──────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle("normal", fontName="Helvetica", fontSize=9, leading=13)
    style_bold = ParagraphStyle("bold", fontName="Helvetica-Bold", fontSize=9, leading=13)
    style_h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=4)
    style_h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12, leading=16, spaceBefore=12, spaceAfter=2)
    style_h3 = ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=10, leading=14, spaceBefore=8, spaceAfter=2)
    style_meta = ParagraphStyle("meta", fontName="Helvetica", fontSize=9, textColor=colors.grey, leading=13)
    style_right = ParagraphStyle("right", fontName="Helvetica-Bold", fontSize=9, alignment=TA_RIGHT)

    story = []

    # Titel
    story.append(Paragraph("Zeiterfassung – Leistungsnachweis", style_h1))
    from datetime import datetime
    df_fmt = datetime.strptime(date_from, "%Y-%m-%d").strftime("%d.%m.%Y")
    dt_fmt = datetime.strptime(date_to, "%Y-%m-%d").strftime("%d.%m.%Y")
    story.append(Paragraph(f"Zeitraum: {df_fmt} – {dt_fmt}", style_meta))
    if only_not_invoiced:
        story.append(Paragraph("Nur nicht fakturierte Einträge", style_meta))
    story.append(Spacer(1, 8*mm))

    # ── Gruppieren: Kunde → Projekt → Einträge ────────────────────────────
    by_customer: Dict[int, Dict] = {}
    for e in entries:
        if e.customer_id not in by_customer:
            by_customer[e.customer_id] = {
                "name": e.customer_name or "Unbekannt",
                "number": e.customer_number or "",
                "projects": {},
                "total": 0,
            }
        customer_data = by_customer[e.customer_id]
        customer_data["total"] += e.duration_minutes
        if e.project_id not in customer_data["projects"]:
            customer_data["projects"][e.project_id] = {
                "name": e.project_name or "Unbekannt",
                "entries": [],
                "total": 0,
            }
        project_data = customer_data["projects"][e.project_id]
        project_data["entries"].append(e)
        project_data["total"] += e.duration_minutes

    grand_total = sum(e.duration_minutes for e in entries)

    # ── Inhalt pro Kunde ──────────────────────────────────────────────────
    for cid, cdata in sorted(by_customer.items(), key=lambda x: x[1]["number"]):
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2c3e50")))
        story.append(Paragraph(
            f"Kunde: {cdata['number']} – {cdata['name']}",
            style_h2
        ))

        for pid, pdata in pdata_sorted(cdata["projects"]):
            story.append(Paragraph(f"Projekt: {pdata['name']}", style_h3))

            # Tabelle mit Einträgen
            table_data = [[
                Paragraph("<b>Datum</b>", style_bold),
                Paragraph("<b>Beginn</b>", style_bold),
                Paragraph("<b>Ende</b>", style_bold),
                Paragraph("<b>Aufgabe</b>", style_bold),
                Paragraph("<b>Notiz</b>", style_bold),
                Paragraph("<b>Dauer</b>", style_bold),
            ]]

            for e in sorted(pdata["entries"], key=lambda x: x.start_time):
                start_dt = datetime.fromisoformat(e.start_time)
                end_dt = datetime.fromisoformat(e.end_time)
                table_data.append([
                    Paragraph(start_dt.strftime("%d.%m.%Y"), style_normal),
                    Paragraph(start_dt.strftime("%H:%M"), style_normal),
                    Paragraph(end_dt.strftime("%H:%M"), style_normal),
                    Paragraph(e.task_name or "–", style_normal),
                    Paragraph(e.note or "", style_normal),
                    Paragraph(_format_hours(e.duration_minutes), style_right),
                ])

            # Projekt-Summe
            table_data.append([
                Paragraph("", style_normal),
                Paragraph("", style_normal),
                Paragraph("", style_normal),
                Paragraph("", style_normal),
                Paragraph("<b>Projektsumme:</b>", style_bold),
                Paragraph(f"<b>{_format_hours(pdata['total'])}</b>", style_right),
            ])

            col_widths = [25*mm, 16*mm, 16*mm, 35*mm, None, 22*mm]
            t = Table(table_data, colWidths=col_widths, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor("#f5f6fa"), colors.white]),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ecf0f1")),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (5, 0), (5, -1), "RIGHT"),
                ("ALIGN", (1, 0), (2, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#bdc3c7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t)
            story.append(Spacer(1, 3*mm))

        # Kundensumme
        story.append(Table(
            [[
                Paragraph(f"Gesamtsumme Kunde {cdata['name']}:", style_bold),
                Paragraph(f"<b>{_format_hours(cdata['total'])}</b>", style_right),
            ]],
            colWidths=[140*mm, 22*mm]
        ))
        story.append(Spacer(1, 6*mm))

    # ── Gesamtsumme ───────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2c3e50")))
    story.append(Spacer(1, 2*mm))
    story.append(Table(
        [[
            Paragraph("GESAMTSUMME ALLE KUNDEN:", style_h2),
            Paragraph(f"<b>{_format_hours(grand_total)}</b>",
                      ParagraphStyle("gt", fontName="Helvetica-Bold", fontSize=12, alignment=TA_RIGHT)),
        ]],
        colWidths=[140*mm, 22*mm]
    ))

    doc.build(story)


def pdata_sorted(projects_dict):
    return sorted(projects_dict.items(), key=lambda x: x[1]["name"])
