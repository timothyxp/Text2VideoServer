from server.app import app

from flask import request, abort

from config.configuration import Config

from config import *
from utils.conf import *

from utils.load_json import load_json

from os import path

import bs4 as bs  
import urllib.request  

import json

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
            print("paragraph")
            article_text += p.text
        # divs = parsed_article.find_all('div')
        # for div in divs:  
        #     print("div")
        #     article_text += div.text
        print(article_text)
        return article_text, None
    except Exception as error:
        print(error)
        return None, "We cannot download article for your link"

@app.route('/search', methods=["POST"])
def search():
    if not request.json:
        return abort(400)

    if DEMO:
        return load_json("beta/search_top.json")

    req = request.get_json()

    config = Config()

    error = None
    if not 'type' in req:
        error = "Type field cannot be empty"
    reqType = None
    if error != None:
        reqType = str(req['type'])
        if not reqType in ['link', 'text']:
            error = "Unknown request type: " + reqType

    if error != None:
        return make_error(error)

    if reqType == 'text' and not 'text' in req:
        error = "Text field is empty"
    if reqType == 'link' and not 'link' in req:
        error = "Link field is empty"

    if error != None:
        return make_error(error)

    data = ''
    if reqType == 'text':
        data = req["text"]
    else:
        data, error = load_from_link(req['link'])
        if error != None:
            return make_error(error)

    data = config.analyzer.analyze(data)
    videos = []

    bad_videos = {}

    print(data)
    for sentence in data['data']:
        print(sentence)
        buffer = []
        for elem in data['data'][sentence]:
            print(elem, end = ' ')
            if elem['type'] == 'video':
                if not elem['href'] in bad_videos:
                    buffer.append(elem)
                else:
                    print("Found bad video:", elem)
            else:
                buffer.append(elem)
        print()
        data['data'][sentence] = buffer

    return json.dumps(data)

