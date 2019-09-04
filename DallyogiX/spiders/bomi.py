# -*- coding: utf-8 -*-
import scrapy
import os
import requests
from urllib.parse import quote
import random
import time
from bs4 import BeautifulSoup
import json


class BomiSpider(scrapy.Spider):
    # remember to config: ins_cookies, serverChan_SCKEY

    name = 'bomi'
    allowed_domains = ['twitter.com', 'instagram.com']
    headers = [
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/76.0.3809.132 "
                       "Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/57.0.2987.110 "
                       "Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/61.0.3163.79 "
                       "Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/62.0.3202.89 "
                       "Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/61.0.3163.91 "
                       "Safari/537.36"},
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/63.0.3239.108 "
                       "Safari/537.36"},
    ]

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

    # ins config
    ins_host = 'https://www.instagram.com'
    ins_cookies = ''
    ins_users = [
        'mulgokizary',
        '__yoonbomi__',
        'haru_x_bomi',
    ]

    # serverChan config
    serverChan_SCKEY = ''

    def __init__(self):
        # init data directory
        if not os.path.exists('data'):
            os.mkdir('data')
        if not os.path.exists('data/twitter'):
            os.mkdir('data/twitter')
        if not os.path.exists('data/ins'):
            os.mkdir('data/ins')
        if not os.path.exists('data/story'):
            os.mkdir('data/story')

        # init twitter user record
        for twitter_user in self.twitter_users:
            if not os.path.exists("data/twitter/{}".format(twitter_user)):
                with open("data/twitter/{}".format(twitter_user), 'w', encoding='utf8') as f:
                    f.write('0')

        # init ins user record
        for ins_user in self.ins_users:
            if not os.path.exists("data/ins/{}".format(ins_user)):
                with open("data/ins/{}".format(ins_user), 'w', encoding='utf8') as f:
                    f.write('0')

    def start_requests(self):
        while True:
            # start twitter requests
            for twitter_user in self.twitter_users:
                yield scrapy.Request(self.twitter_format.format(twitter_user),
                                     self.parse_twitter, headers=random.choice(self.headers))
            time.sleep(60)

            # start ins requests
            for ins_user in self.ins_users:
                yield scrapy.Request(self.ins_host + '/' + ins_user + '/',
                                     self.parse_ins_posts, headers=random.choice(self.headers))
            time.sleep(60)
            yield scrapy.Request(self.ins_host, self.parse_ins_stories,
                                 headers={'User-Agent': random.choice(self.headers)['User-Agent'],
                                          'cookie': self.ins_cookies})
            time.sleep(30)

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
                if not tweet.startswith('<' + flag, i):
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
        self.inform_serverChan("{}有更新".format(name), tweet)

    def parse_ins_posts(self, response):
        if response.status != 200:
            return

        # get latest shortcode
        html = BeautifulSoup(response.text)
        js = html.body.find_all('script', type='text/javascript')[0]
        json_data = json.loads(js.text[len('window._sharedData = '):-1])
        user = json_data['entry_data']['ProfilePage'][0]['graphql']['user']
        shortcode = user['edge_owner_to_timeline_media']['edges'][0]['node']['shortcode']

        # compare shortcode
        username = response.url.split('/')[-2]
        with open('data/ins/' + username, 'r', encoding='utf8') as f:
            prev_shortcode = f.read()
        if shortcode != prev_shortcode:
            with open('data/ins/' + username, 'w', encoding='utf8') as f:
                f.write(shortcode)
            self.inform_serverChan(username + '更新了', 'shortcode: ' + shortcode)

    def parse_ins_stories(self, response):
        if response.status != 200:
            return

        time.sleep(30)

        html = BeautifulSoup(response.text)
        stories_links = html.head.find_all('link', attrs={
            'rel': 'preload', 'as': 'fetch', 'type': 'application/json'})
        for link in stories_links:
            if 'stories' in link['href']:
                yield scrapy.Request(self.ins_host + link['href'], self.parse_ins_stories_json,
                                     headers={'User-Agent': random.choice(self.headers)['User-Agent'],
                                              'cookie': self.ins_cookies})

    def parse_ins_stories_json(self, response):
        if response.status != 200:
            self.logger.error('Cannot get ins stories json.')
            return

        json_data = json.loads(response.text)
        nodes = json_data['data']['user']['feed_reels_tray']['edge_reels_tray_to_reel']['edges']
        for i in range(len(nodes)):
            is_updated = False
            username = nodes[i]['node']['owner']['username']
            expiring = str(nodes[i]['node']['expiring_at'])
            if os.path.exists('data/story/' + username):
                with open('data/story/' + username, 'r', encoding='utf8') as f:
                    prev_expiring = f.read()
                if expiring != prev_expiring:
                    is_updated = True
            else:
                is_updated = True
                with open('data/story/' + username, 'w', encoding='utf8') as f:
                    f.write(expiring)
            if is_updated:
                self.inform_serverChan(username + '的story更新了', 'expiring_at: ' + expiring)
                time.sleep(5)

    def inform_serverChan(self, text, desp):
        params = {
            'text': quote(text),
            'desp': quote(desp),
        }
        requests.get("https://sc.ftqq.com/{}.send?text={}&desp={}".format(
            self.serverChan_SCKEY, params['text'], params['desp']))
