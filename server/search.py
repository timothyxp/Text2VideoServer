import json
import urllib.request

import bs4 as bs
from flask import request, abort

from config.configuration import Config
from server.app import app
from utils.conf import *
from utils.load_json import load_json
from utils.logging.logger import logger


def make_error(error):
    return json.dumps({
        'type': 'error',
        'error': str(error)
    })


def load_from_link(link):
    try:
        scraped_data = urllib.request.urlopen(link)  
        article = scraped_data.read()
        parsed_article = bs.BeautifulSoup(article, 'lxml')
        paragraphs = parsed_article.find_all('p')
        article_text = ""
        for p in paragraphs:
            article_text += p.text
        # divs = parsed_article.find_all('div')
        # for div in divs:  
        #     print("div")
        #     article_text += div.text
        logger.debug(article_text)
        return article_text, None
    except Exception as error:
        logger.error(error)
        return None, "We cannot download article for your link"


@app.route('/search', methods=["POST"])
def search():
    if not request.json:
        return abort(400)

    if DEMO:
        return load_json("beta/search_top.json")

    req = request.get_json()
    logger.debug(req)

    config = Config()

    error = None
    if not 'type' in req:
        error = "Type field cannot be empty"
    reqType = None
    if error == None:
        reqType = str(req['type'])
        if not reqType in ['link', 'text']:
            error = "Unknown request type: " + reqType

    if error != None:
        return make_error(error)

    if reqType == 'text' and not 'text' in req:
        error = "Text field is empty"
    if reqType == 'link' and not 'link' in req:
        error = "Link field is empty"

    logger.info("Request type " + reqType)

    if error != None:
        return make_error(error)

    data = ''
    if reqType == 'text':
        data = req["text"]
    else:
        data, error = load_from_link(req['link'])
        if error != None:
            return make_error(error)

    data, error = config.analyzer.analyze(data)
    if error != None:
        return make_error(error)
    videos = []

    bad_videos = {}

    logger.debug(data)
    for sentence in data['data']:
        logger.debug(sentence)
        buffer = []
        for elem in data['data'][sentence]:
            logger.debug(elem)
            if elem['type'] == 'video':
                if not elem['href'] in bad_videos:
                    buffer.append(elem)
                else:
                    logger.warning("Found bad video: " + elem)
            else:
                buffer.append(elem)
        print()
        data['data'][sentence] = buffer

    return json.dumps(data)

