# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import requests
# import urllib.parse
# from scrapy.mail import MailSender


class TweetPipeline(object):
    def __init__(self):
        # remember to config: project_id, api_key, source_id, receiver_id

        self.project_id = '388177'
        self.api_key = ''
        self.spider_name = 'bomi'

        self.isUpdated = False
        self.old_tweets = dict()
        self.updated_tweets = dict()

        # alertover solution
        self.source_id = ''
        self.receiver_id = ''
        self.alertover_url = 'https://api.alertover.com/v1/alert'

        # email solution
        # self.user_email = ''
        # self.smtphost = ''
        # self.mailfrom = ''
        # self.smtpuser = ''
        # self.smtppass = ''
        # self.smtpport = 465
        # self.smtpssl = True

        # server chan
        # self.serverChan_SCKEY = ''
        # self.serverChan_URL = ''

        # get old items using scrapinghub's api
        try:
            old_items = requests.get(f"https://app.scrapinghub.com/api/items.json?project={self.project_id}\
            &spider={self.spider_name}&apikey={self.api_key}").json()
            for old_item in old_items:
                self.old_tweets[old_item['username']] = old_item['top_tweet']
        except ConnectionError:
            pass

    def process_item(self, item, spider):
        username = item['username']
        top_tweet = item['top_tweet']

        if username in self.old_tweets.keys():
            if top_tweet != self.old_tweets[username]:
                self.isUpdated = True
                self.updated_tweets[username] = top_tweet
        else:
            self.isUpdated = True
            self.updated_tweets[username] = top_tweet
        return item

    def close_spider(self, spider):
        if not self.isUpdated:
            return

        # use alertvoer to inform user
        for user, top_tweet in self.updated_tweets.items():
            if user.startswith('twitter'):
                platform = 'twitter'
                username = user[8:]
            elif user.startswith('ins'):
                platform = 'ins'
                username = user[4:]
            try:
                requests.post(
                    url=self.alertover_url,
                    data={
                        "source": self.source_id,
                        "receiver": self.receiver_id,
                        "content": top_tweet,
                        "title": f"{username}的{platform}有更新"
                    }
                )
            except ConnectionError:
                spider.logger.error(f"Connection Error occurs when sending {user}'s "
                                    f"message to alertover")

        # use email to inform user
        # mailer = MailSender(smtphost=self.smtphost, mailfrom=self.mailfrom, smtpuser=self.smtpuser,
        #                     smtppass=self.smtppass, smtpport=self.smtpport, smtpssl=self.smtpssl)
        # subject = 'Twitter有更新'
        # body = '<h3>更新列表如下：</h3>'
        # for username in self.updated_tweets.keys():
        #     body += f"<p>{username}: {self.updated_tweets[username]}</p>"
        # body += '<h3>以上</h3>'
        #
        # mailer.send(to=self.user_email, subject=subject, body=body.encode('utf8'),
        #             mimetype='text/html', charset='utf8')

        # use serverChan to inform user
        # updated_users = list(self.updated_tweets.keys())
        # group_num = 25
        # updated_len = (len(updated_users)-1)//group_num +1
        # for group_i in range(updated_len):
        #     params = {
        #         'text': 'Twitter有更新',
        #         'desp': '',
        #     }
        #     if updated_len > 1:
        #         params['text'] += f"{group_i+1}{updated_len}"
        #     for user in updated_users[group_i*group_num:(group_i+1)*group_num]:
        #         params['desp'] += f"{user},"
        #     log = requests.get(url=self.serverChan_URL.format(self.serverChan_SCKEY,
        #                                                       urllib.parse.quote(params['text']),
        #                                                       urllib.parse.quote(params['desp'])))
        #     if log.status_code != 200:
        #         spider.logger.error(f"ServerChan出问题了{group_i+1}/{updated_len}: {log.status_code}")
