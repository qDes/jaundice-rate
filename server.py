from aiohttp import web


async def handle(request):
    urls = request.query.get('urls').split(',')
    #print((data.keys()))
    #print(urls.split(','))
    resp = {'urls': urls}
    return web.json_response(resp)


app = web.Application()
app.add_routes([web.get('/', handle),
                #web.get('/{name}', handle)
                ])


if __name__ == '__main__':
    web.run_app(app)
