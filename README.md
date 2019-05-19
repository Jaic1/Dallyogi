# Dallyogi
Scrapy &amp; Scrapy Cloud to crawl Twitter's and Instagram's data and Alertover to send notification
## Architecture
### Twitter
specify our own username and then the spider(bomi.py) will parse ours' following.
### Instagram
specify the users we want to follow and then the spider(bomi.py) will parse each user. *(not supported to specify username yet)*
### Scrapy Cloud
* use Scrapy Cloud to run our project and record old items
* specify the api key and project id of our Scrapy Cloud account
* use shub to deploy our project
### Alertover
specify the source id and receiver id
## About
* prepare to try scrapyd to host the project
* add more functions about instagram
