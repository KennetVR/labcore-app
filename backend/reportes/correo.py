from django.conf import settings
from django.core.mail import EmailMessage


def enviar_reporte_por_correo(orden, reporte, destinatario):
    mensaje = EmailMessage(
        subject=f"Resultados de la orden {orden.numero}",
        body=(
            "Adjuntamos el informe de resultados de la orden "
            f"{orden.numero}.\n\n"
            "Este mensaje fue generado por LabCore."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[destinatario],
    )
    with reporte.pdf.open("rb") as archivo:
        mensaje.attach(f"{reporte.numero}.pdf", archivo.read(), "application/pdf")
    if mensaje.send(fail_silently=False) != 1:
        raise OSError("Email backend did not accept the message")
    return mensaje
