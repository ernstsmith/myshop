from .models import TelegramUser


def telegram_user(request):
    user_pk = request.session.get("telegram_user_pk")
    if not user_pk:
        return {"telegram_user": None}
    try:
        user = TelegramUser.objects.get(pk=user_pk)
    except TelegramUser.DoesNotExist:
        request.session.pop("telegram_user_pk", None)
        return {"telegram_user": None}
    return {"telegram_user": user}
