import json
import asyncio
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            from shop.bot import create_application
            app = create_application()
            asyncio.run(app.initialize())
            from telegram import Update
            update = Update.de_json(data, app.bot)
            asyncio.run(app.process_update(update))
            asyncio.run(app.shutdown())
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
    return JsonResponse({'ok': True})
