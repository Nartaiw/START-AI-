import os
import asyncio
from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is alive and running!")

def keep_alive():
    """Эта функция больше не нужна, сервер запускается напрямую в bot.py"""
    pass

async def start_keep_alive_server():
    app = web.Application()
    app.router.add_get('/', handle)
    
    port = int(os.getenv("PORT", 8080))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Фоновый веб-сервер успешно запущен на порту {port}")
