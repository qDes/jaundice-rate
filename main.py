import aiohttp
import asyncio

from adapters.inosmi_ru import sanitize


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def main():
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, "https://inosmi.ru/economic/20190629/245384784.html")
        sanitized_html = sanitize(html, plaintext=True)
        print(sanitized_html)


asyncio.run(main())
