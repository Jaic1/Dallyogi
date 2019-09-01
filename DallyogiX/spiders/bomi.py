# -*- coding: utf-8 -*-
import scrapy
import os
import requests
from urllib.parse import quote


class BomiSpider(scrapy.Spider):
    name = 'bomi'
    allowed_domains = ['twitter.com']
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) \
                            AppleWebKit/537.36 (KHTML, like Gecko) \
                            Chrome/76.0.3809.132 Safari/537.36"}

    # twitter config
    twitter_format = "https://twitter.com/search?f=tweets&q=from%3A{}"
    twitter_users = [
        '19910303net',
        'firstspring_313',
        'Apink_2011',
        'Asterisk813',
        '8h_13m',
        'Apinkbm',
    ]

    # serverChan config
    serverChan_SCKEY = 'SCU50038T918befe60eb8404f42ffa7b2c5c487955cc4724ac645a'

    def __init__(self):
        # init data directory
        if not os.path.exists('data'):
            os.mkdir('data')
        if not os.path.exists('data/twitter'):
            os.mkdir('data/twitter')

        # init twitter user record
        for twitter_user in self.twitter_users:
            if not os.path.exists("data/twitter/{}".format(twitter_user)):
                with open("data/twitter/{}".format(twitter_user), 'w', encoding='utf8') as f:
                    f.write('0')

    def start_requests(self):
        # start twitter requests
        while True:
            for twitter_user in self.twitter_users:
                yield scrapy.Request(self.twitter_format.format(twitter_user),
                                     self.parse_twitter, headers=self.headers)

    def parse_twitter(self, response):
        if response.status != 200:
            return

        # extract name, id and tweet from response html
        name = response.url.split('%3A')[-1]
        newId = response.css('div.stream ol.stream-items li.stream-item').xpath('@data-item-id').getall()[0]
        newId = str(newId)
        tweet = response.css('div.stream ol.stream-items li.stream-item p').getall()[0]

        # filter plain text from tweet
        i = j = 0
        while i < len(tweet):
            isTag = False
            for flag in ['p', 'a', 'img', 's', 'b']:
                if not tweet.startswith('<'+flag, i):
                    continue

                j = i
                while tweet[j] != '>':
                    j += 1
                tweet = tweet[:i] + tweet[j + 1:]
                j = tweet.find("</{}>".format(flag), i)
                if j >= i:
                    tweet = tweet[:j] + tweet[j + 3 + len(flag):]

                isTag = True
                break

            if not isTag:
                i += 1
        tweet.replace('\n', '')

        # check if this tweet is a new tweet
        with open("data/twitter/{}".format(name), 'r', encoding='utf8') as f:
            oldId = f.read()
        if newId == oldId:
            return None
        else:
            with open("data/twitter/{}".format(name), 'w', encoding='utf8') as f:
                f.write(newId)

        # inform ServerChan
        params = {
            'text': quote("{}有更新".format(name)),
            'desp': quote(tweet),
        }
        requests.get("https://sc.ftqq.com/{}.send?text={}&desp={}".format(
            self.serverChan_SCKEY, params['text'], params['desp']))
