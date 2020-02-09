import json

from aiohttp import http_exceptions, web
from main import fetch_articles_scores


async def handle(request):
    try:
        urls = request.query.get('urls').split(',')
        print(urls)
        scores = await fetch_articles_scores(urls)
        return web.json_response(scores)
    except AttributeError:
        return web.Response(text='sasi')


app = web.Application()
app.add_routes([web.get('/', handle),
                ])


if __name__ == '__main__':
    web.run_app(app)
