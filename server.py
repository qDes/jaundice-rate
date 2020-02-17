from aiohttp import web
from main import fetch_articles_scores


async def handle(request):
    try:
        urls = request.query.get('urls').split(',')
        if len(urls) > 10:
            response = {"error":
                        "too many urls in request, should be 10 or less"}
            return web.json_response(response, status=400)
        scores = await fetch_articles_scores(urls)
        return web.json_response(scores)
    except AttributeError:
        response = {"error": "no urls in request"}
        return web.json_response(response)


app = web.Application()
app.add_routes([web.get('/', handle),
                ])


if __name__ == '__main__':
    web.run_app(app)
