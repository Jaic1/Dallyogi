import scrapy
from Dallyogi.items import TweetItem
import re


class BomiSpider(scrapy.spiders.CrawlSpider):
    # remember to config: username, ins config

    name = 'bomi'

    # twitter config
    username = ''
    tweet_text_len = 20
    url_head = 'https://mobile.twitter.com'
    url_head_desktop = 'https://twitter.com/'
    following_list = list()

    # ins config
    ins_url_head = 'https://www.instagram.com/'
    ins_users = [
        'official.apink2011/',
        '__yoonbomi__/',
        'haru_x_bomi/'
    ]

    def __init__(self):
        self.url_following = f"{self.url_head}/{self.username}/following"

    def start_requests(self):
        # start twitter requests
        yield scrapy.Request(url=self.url_following, callback=self.parse)

        # start ins requests
        for ins_user in self.ins_users:
            yield scrapy.Request(url=self.ins_url_head+ins_user, callback=self.parse_ins)

    def parse(self, response):
        self.following_list.extend(response.css('table.user-item span.username::text').getall())
        cursor = response.css('div.w-button-more a::attr(href)').get()
        if cursor is not None:
            yield scrapy.Request(url=self.url_head+cursor, callback=self.parse)
        else:
            if len(self.following_list) == 0:
                self.logger.error(f"User {self.username} doesn't have any followings!")
            else:
                for following_name in self.following_list:
                    yield scrapy.Request(url=self.url_head_desktop + following_name, callback=self.parse_following)

    def parse_following(self, response):
        following_name = response.url.split('/')[-1]
        top_tweet_texts = response.css('div.stream ol.stream-items li.stream-item:not(.js-pinned) \
                        p.tweet-text *::text').getall()[0:self.tweet_text_len]
        top_tweet = str()
        for text in top_tweet_texts:
            top_tweet += text
        yield TweetItem(username='twitter-'+following_name, top_tweet=top_tweet)

    def parse_ins(self, response):
        ins_username = response.url.split('/')[-2]
        if response.status != 200:
            self.logger.error(f"ins {ins_username} can't response.")
            yield TweetItem(username='ins-' + ins_username, top_tweet='无法获取response')
            return

        pattern_edge = re.compile(r"edge_owner_to_timeline_media.*?node.*?edges.*?\[(.*?)\]", re.DOTALL)
        match_edge = pattern_edge.search(response.text)
        # input_text is the literal string of its UTF-16 meaning, e.g r"\uc5d0"
        input_text = str()
        try:
            input_text = match_edge.group(1)
        except IndexError:
            self.logger.error(f"ins user {ins_username} can't match")
            yield TweetItem(username='ins-' + ins_username, top_tweet="re can't match.")
            return
        if input_text != '':
            match_text = re.search(r"text\":\"(.*?)\"", input_text, re.DOTALL)
            input_text = match_text.group(1)
        else:
            match_code = re.search(r"edge_owner_to_timeline_media.*?shortcode\":\"(.*?)\"",
                                   response.text, re.DOTALL)
            code = match_code.group(1)
            yield TweetItem(username='ins-' + ins_username, top_tweet=code)
            return

        # convert to UTF-16 string
        output_text = str()
        i = 0
        while True:
            if input_text[i] == '\\':
                if input_text[i + 1] == 'n':
                    output_text += '\n'
                    i += 2
                elif input_text[i + 1] == 'u':
                    c = chr(int(input_text[i + 2:i + 6], 16))
                    # problem about conversion between utf-8 and utf-16 unresolved
                    try:
                        c.encode('utf-8')
                        output_text += c
                    except UnicodeEncodeError:
                        pass
                    i += 6
                else:
                    self.logger.error(f"{ins_username}'s' corner case when dealing utf-16 converting\n{input_text}")
                    output_text += '\\'
                    i += 1
            else:
                output_text += input_text[i]
                i += 1
            if i >= len(input_text):
                break
        yield TweetItem(username='ins-' + ins_username, top_tweet=output_text)