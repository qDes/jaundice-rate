import aiohttp
import asyncio
import logging
import pymorphy2
import time

from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound
from aionursery import Nursery
from aiohttp.client_exceptions import ClientConnectionError
from async_timeout import timeout
from contextlib import contextmanager
from enum import Enum
from text_tools import calculate_jaundice_rate, split_by_words
from text_tools import load_charged_words


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'

    def __str__(self):
        return str(self.value)


async def analyzator(morph, html):
    words = await split_by_words(morph, html)
    analyze_time = time.monotonic()
    return words, analyze_time


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


async def process_article(session, morph, charged_words, url):
    score = None
    words_count = None
    time_analyze = None
    try:
        async with timeout(1.5) as tm:
            html = await fetch(session, url)
        sanitized_html = sanitize(html, plaintext=True)
        async with timeout(3) as tm:
            article_words, time_analyze = await analyzator(morph, sanitized_html)
        score = calculate_jaundice_rate(article_words, charged_words)
        words_count = len(article_words)
        status = ProcessingStatus.OK
    except ClientConnectionError:
        status = ProcessingStatus.FETCH_ERROR
    except ArticleNotFound:
        status = ProcessingStatus.PARSING_ERROR
    except asyncio.TimeoutError:
        status = ProcessingStatus.TIMEOUT
    return (status, url, score, words_count, time_analyze)


def process_results(results):
    for result in results:
        outcome = result.result()
        print("Article name", outcome[0])
        print("Processing status", outcome[1])
        print("Article score", outcome[2])
        print("Words count", outcome[3])
        logging.debug(f"Analyze time {str(outcome[4])}")
        print()


async def fetch_articles_scores(urls):
    FORMAT = "%(levelname)s:root: %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    morph = pymorphy2.MorphAnalyzer()
    charged_words = load_charged_words('charged_dict/negative_words.txt')
    async with aiohttp.ClientSession() as session:
        async with Nursery() as nursery:
            tasks = []
            for num, url in enumerate(urls):
                task = nursery.start_soon(process_article(session, morph, 
                    charged_words, url))
                tasks.append(task)
            results = await asyncio.wait(tasks)
    scores = []    
    for result in results[0]:
        scores.append({"status": str(result.result()[0]),
            "url": result.result()[1],
            "score": result.result()[2],
            "words_count": result.result()[3]})
        logging.debug(f"Analyze time {str(result.result()[4])}")
    return scores


async def main():
    TEST_ARTICLES = ['https://inosmi.ru/politic/20200119/246646205.html',
            'https://inosmi.ru/social/20200119/246596410.html',
            'https://inosmi.ru/social/20200119/246642707.html',
            'https://inosmi.ru/social/20200119/246644975.html',
            'http://sasifsd45eegdfi.com',
            'https://lenta.ru/news/2020/01/24/voting/'
            ]
    results = await fetch_articles_scores(TEST_ARTICLES)
    print(results)
    '''
    FORMAT = "%(levelname)s:root: %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
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
    '''

if __name__ == "__main__":
    asyncio.run(main())
