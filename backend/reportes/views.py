from django.core import signing
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from .models import Reporte
from .verification import SALT


@never_cache
@require_safe
def verify_report(request, token):
    report = None
    try:
        data = signing.Signer(salt=SALT).unsign_object(token)
        if isinstance(data, dict) and isinstance(data.get("number"), str):
            candidate = Reporte.objects.filter(numero=data["number"]).first()
            if (
                candidate
                and candidate.pdf
                and candidate.generado.isoformat() == data.get("issued")
            ):
                report = candidate
    except (signing.BadSignature, ValueError, TypeError):
        pass
    response = render(
        request,
        "reportes/verification.html",
        {"number": report.numero if report else None},
        status=200 if report else 404,
    )
    response["Referrer-Policy"] = "no-referrer"
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response
