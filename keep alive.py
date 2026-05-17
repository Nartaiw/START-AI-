import os
from aiohttp import web

async def handle(request):
    # Отвечаем Render и UptimeRobot
    return web.Response(text="Bot is alive and running!")

async def start_keep_alive_server():
    app = web.Application()
    app.router.add_get('/', handle)
    
    # Получаем порт от Render
    port = int(os.getenv("PORT", 8080))
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Запускаем веб-сервер на нужном порту
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Фоновый веб-сервер aiohttp запущен на порту {port}")
