from urllib.parse import urlsplit

from django.conf import settings
from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse


SALT = "labcore.report-verification.v1"


def verification_url(report):
    base = settings.REPORT_VERIFICATION_BASE_URL.rstrip("/")
    parsed = urlsplit(base)
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ImproperlyConfigured("Invalid REPORT_VERIFICATION_BASE_URL")
    token = signing.Signer(salt=SALT).sign_object(
        {"number": report.numero, "issued": report.generado.isoformat()}
    )
    return base + reverse("verify-report", kwargs={"token": token})
