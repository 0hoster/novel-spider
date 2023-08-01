#  Copyright (c) 2023. hoster, Inc. All Rights Reserved
#  @作者    : hoster
#  @邮件    : zh721548595@outlook.com
#  @文件    : 项目 [novel] - main.py
#  @描述    : 异步爬取 www.xbiquge.la 的小说

import aiohttp
import asyncio
from re import sub
from lxml import etree
from anyio import Path
from os.path import exists
from os import makedirs, listdir

CONCURRENCY = 64  # 多线程数
headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/73.0.3683.103 Safari/537.36"
}

semaphore = asyncio.Semaphore(CONCURRENCY)
session = None
book_title = None
book_url = None
chapter_title = None
w = 0


async def download(idx):
    async with semaphore:
        try:
            async with session.get("https://www.xbiquge.la" + book_url[idx]) as response:
                _html = await response.text()
                html = etree.HTML(_html)
                # print(html.xpath('//div[@class="box_con"]/div[@id="content"]/text()'))
                texts = [i.replace("\xa0\xa0\xa0\xa0", "").replace("\r", "\n") for i in
                         html.xpath('//div[@class="box_con"]/div[@id="content"]/text()')]
                # print(texts)
                text = ""
                for i in range(len(texts)):
                    text += texts[i]
                # print(text)
                text = text.replace("\ufeff", "").replace("\n\n", "\n")
                title = to_num(idx + 1)
                _t = sub("第[零一二两三四五六七八九十百千万0-9]+章?\s?", "-", chapter_title[idx])
                if _t != "-":
                    title += _t
                print("Done %s" % title)
                await Path('./novel/%s/%s.txt' % (book_title[0], title)).write_text(text)
        except Exception as e:
            print("Download Error:    %s" % chapter_title[idx])
            print("#" * 128)
            pass


async def main():
    global session
    global book_title
    global book_url
    global chapter_title
    global w
    session = aiohttp.ClientSession()
    book_url = input("Type the book's URL: ")
    async with session.get(book_url) as response:
        html = await response.text()
    book_html = etree.HTML(html)
    book_title = book_html.xpath('//div[@id="info"]/h1/text()')
    book_url = book_html.xpath('//div[@id="list"]/dl/dd/a/@href')
    chapter_title = book_html.xpath('//div[@id="list"]/dl/dd/a/text()')
    tmp = len(chapter_title)
    w = 0
    while tmp:
        tmp //= 10
        w += 1
    if not exists("./novel/%s" % book_title[0]):
        makedirs('./novel/%s' % book_title[0])
    try:
        start = int(input("Name:%s\tTotal:%d\tProgress:%d\nStart at:" % (
            book_title[0], len(chapter_title), len(listdir('./novel/%s' % book_title[0])))))
        end = int(input("End at  :"))
    except ValueError:
        ls = len(listdir('./novel/%s' % book_title[0]))
        start = ls
        if ls == 0: start = 1
        end = len(chapter_title)
    scrape_index_tasks = [asyncio.ensure_future(download(i)) for i in range(start - 1, end)]
    await asyncio.gather(*scrape_index_tasks)
    await session.close()


def to_num(x):
    x = str(x)
    while len(x) < w:
        x = '0' + x
    return x


if __name__ == '__main__':
    asyncio.run(main())
