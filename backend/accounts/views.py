import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST


def session_response(request):
    user = request.user
    return JsonResponse({
        "user": {
            "id": user.pk,
            "username": user.username,
            "name": user.get_full_name() or user.username,
            "role": user.rol,
        } if user.is_authenticated else None,
        "csrf_token": get_token(request),
    })


@never_cache
@require_GET
def session_view(request):
    return session_response(request)


@never_cache
@require_POST
@csrf_protect
def login_view(request):
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "Expected a JSON object."}, status=400)
    if not isinstance(data, dict) or not all(
        isinstance(data.get(field), str) and data[field]
        for field in ("username", "password")
    ):
        return JsonResponse({"detail": "Username and password are required."}, status=400)
    user = authenticate(request, username=data["username"], password=data["password"])
    if user is None:
        return JsonResponse({"detail": "Invalid username or password."}, status=401)
    login(request, user)
    return session_response(request)


@never_cache
@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return session_response(request)
