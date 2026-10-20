from io import BytesIO
import os
import tempfile
from xml.sax.saxutils import escape

import qrcode
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from .verification import verification_url


def _qr(data, temporales):
    archivo = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    archivo.close()
    temporales.append(archivo.name)
    qrcode.make(data).save(archivo.name, format="PNG")
    return Image(archivo.name, width=28 * mm, height=28 * mm)


def generar_pdf(orden, reporte):
    buffer = BytesIO()
    temporales = []
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Reporte {reporte.numero}",
    )
    estilos = getSampleStyleSheet()
    pequeño = ParagraphStyle("Pequeño", parent=estilos["Normal"], fontSize=8, leading=10)
    items = list(orden.items.select_related("examen", "validado_por"))
    validador = next((item.validado_por for item in items if item.validado_por), None)

    historia = [
        Paragraph("LabCore — Informe de resultados", estilos["Title"]),
        Spacer(1, 4 * mm),
        Paragraph(
            f"Orden <b>{orden.numero}</b> · Reporte <b>{reporte.numero}</b> · "
            f"Fecha {orden.fecha:%d/%m/%Y}",
            estilos["Normal"],
        ),
        Paragraph(
            f"Paciente: <b>{escape(orden.paciente.nombre_completo) if orden.paciente else 'Sin paciente'}</b> · "
            f"Cliente: <b>{escape(orden.cliente.nombre) if orden.cliente else 'Particular'}</b>",
            estilos["Normal"],
        ),
        Spacer(1, 6 * mm),
    ]

    filas = [["Examen", "Resultado", "Bandera"]]
    for item in items:
        filas.append(
            [
                f"{item.examen.codigo} — {item.examen.nombre}",
                item.resultado or "—",
                item.bandera or "",
            ]
        )
    tabla = Table(filas, colWidths=[100 * mm, 45 * mm, 25 * mm], repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#116b70")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cddce1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f8f9")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    historia += [
        tabla,
        Spacer(1, 8 * mm),
        Paragraph(
            f"Validado por: <b>{escape(validador.get_full_name() or validador.username) if validador else 'Pendiente'}</b>",
            estilos["Normal"],
        ),
        Spacer(1, 6 * mm),
        _qr(verification_url(reporte), temporales),
        Spacer(1, 3 * mm),
        Paragraph(
            "Documento generado por LabCore. Verifique la autenticidad con el código QR.",
            pequeño,
        ),
    ]
    try:
        documento.build(historia)
    finally:
        for ruta in temporales:
            os.unlink(ruta)
    return ContentFile(buffer.getvalue(), name=f"{reporte.numero}.pdf")
