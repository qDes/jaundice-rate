import aiohttp
import asyncio
import pymorphy2

from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound
from aionursery import Nursery
from aiohttp.client_exceptions import ClientConnectionError
from enum import Enum
from text_tools import calculate_jaundice_rate, split_by_words
from text_tools import load_charged_words


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'

    def __str__(self):
        return str(self.value)


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session, morph, charged_words, url, title):
    try:
        html = await fetch(session, url)
        sanitized_html = sanitize(html, plaintext=True)
        article_words = split_by_words(morph, sanitized_html)
        score = calculate_jaundice_rate(article_words, charged_words)
        words_count = len(article_words)
        status = ProcessingStatus.OK
    except ClientConnectionError:
        return (title, ProcessingStatus.FETCH_ERROR, None, None)
    except ArticleNotFound:
        return (title, ProcessingStatus.PARSING_ERROR, None, None)
    return (title,status, score, words_count)


def process_results(results):
    for result in results:
        outcome = result.result()
        print("Article name", outcome[0])
        print("Processing status", outcome[1])
        print("Article score", outcome[2])
        print("Words count", outcome[3])



async def main():
    TEST_ARTICLES = ['https://inosmi.ru/politic/20200119/246646205.html',
            'https://inosmi.ru/social/20200119/246596410.html',
            'https://inosmi.ru/social/20200119/246642707.html',
            'https://inosmi.ru/social/20200119/246644975.html',
            'http://sasifsd45eegdfi.com',
            'https://lenta.ru/news/2020/01/24/voting/'
            ]
    morph = pymorphy2.MorphAnalyzer()
    charged_words = load_charged_words('charged_dict/negative_words.txt')
    async with aiohttp.ClientSession() as session:
        async with Nursery() as nursery:
            tasks = []
            for num, url in enumerate(TEST_ARTICLES):
                task = nursery.start_soon(process_article(session, morph, 
                    charged_words, url, f'{num}'))
                tasks.append(task)
            results = await asyncio.wait(tasks)
        for result in results[0]:
            print(result.result())

        process_results(results[0])


if __name__ == "__main__":
    asyncio.run(main())
