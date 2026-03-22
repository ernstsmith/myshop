import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            import asyncio
            from telegram import Update
            from shop.bot import create_application

            data = json.loads(request.body)
            app = create_application()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(app.initialize())
                update = Update.de_json(data, app.bot)
                loop.run_until_complete(app.process_update(update))
            finally:
                loop.run_until_complete(app.shutdown())
                loop.close()
        except Exception as e:
            logger.error(f"Webhook error: {e}", exc_info=True)
    return JsonResponse({'ok': True})
