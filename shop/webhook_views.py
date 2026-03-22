import json
import asyncio

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Application
from django.conf import settings


@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            from shop.bot import create_application
            app = create_application()
            asyncio.run(app.process_update(Update.de_json(data, app.bot)))
        except Exception:
            pass
    return JsonResponse({'ok': True})
