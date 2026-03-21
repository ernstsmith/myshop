from django.conf import settings

from .models import TelegramUser


def telegram_user(request):
    user_pk = request.session.get("telegram_user_pk")
    if not user_pk:
        return {
            "telegram_user": None,
            "CLOUDINARY_CLOUD_NAME": settings.CLOUDINARY_CLOUD_NAME,
        }
    try:
        user = TelegramUser.objects.get(pk=user_pk)
    except TelegramUser.DoesNotExist:
        request.session.pop("telegram_user_pk", None)
        return {
            "telegram_user": None,
            "CLOUDINARY_CLOUD_NAME": settings.CLOUDINARY_CLOUD_NAME,
        }
    return {
        "telegram_user": user,
        "CLOUDINARY_CLOUD_NAME": settings.CLOUDINARY_CLOUD_NAME,
    }
