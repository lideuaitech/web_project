from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

import os
import uuid


class PDFExporter:

    def __init__(self, df, summary):

        self.df = df
        self.summary = summary

    def export(self):

        # =========================
        # CREATE EXPORTS FOLDER
        # =========================

        if not os.path.exists("exports"):
            os.makedirs("exports")

        filename = (
            f"exports/{uuid.uuid4()}.pdf"
        )

        # =========================
        # PDF DOC
        # =========================

        doc = SimpleDocTemplate(filename)

        styles = getSampleStyleSheet()

        elements = []

        # =========================
        # TITLE
        # =========================

        title = Paragraph(
            "Lideu AI Analytics Report",
            styles["Title"]
        )

        elements.append(title)

        elements.append(Spacer(1, 20))

        # =========================
        # TABLE
        # =========================

        data = [list(self.df.columns)]

        for row in self.df.values:
            data.append(list(row))

        table = Table(data)

        table.setStyle(TableStyle([

            ("BACKGROUND", (0, 0), (-1, 0), colors.black),

            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

            ("GRID", (0, 0), (-1, -1), 1, colors.grey),

            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

        ]))

        elements.append(table)

        elements.append(Spacer(1, 25))

        # =========================
        # SUMMARY
        # =========================

        summary_title = Paragraph(
            "<b>AI Insight Summary</b>",
            styles["Heading2"]
        )

        elements.append(summary_title)

        elements.append(Spacer(1, 10))

        summary_text = Paragraph(
            self.summary,
            styles["BodyText"]
        )

        elements.append(summary_text)

        # =========================
        # BUILD PDF
        # =========================

        doc.build(elements)

        return filename