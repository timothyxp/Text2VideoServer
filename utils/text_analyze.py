from abc import abstractmethod, ABC
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

from config import DEFAULT_EMOTION, YOUTUBE_FILTER
import bs4 as bs
import urllib.request
import re
import nltk
from nltk.corpus import stopwords
import heapq

from summa import summarizer

import json

import os

class TextAnalyzeBase(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def analyze(self, text):
       pass

class TextAnalyze(TextAnalyzeBase):
    def __init__(self):
        self.search_cache = {}
        if os.path.exists("search_cache.json"):
            with open("search_cache.json", "r") as inp:
                data = str(inp.read())
                self.search_cache = json.loads(data)

    def __summarize__(self, article_text):
        print(len(article_text))
        if len(article_text) <= 500:
            new_article_text = summarizer.summarize(article_text)
            if new_article_text != None and len(new_article_text) >= 20:
                return new_article_text, None
            return article_text, None
        article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
        article_text = re.sub(r'\s+', ' ', article_text)
        formatted_article_text = re.sub('[^А-Яа-я]',' ', article_text)
        formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)
        sentence_list = nltk.sent_tokenize(article_text)
        mystopwords = stopwords.words('russian') + ['это', 'наш' , 'тыс', 'млн', 'млрд', u'также',  'т', 'д', '-', '-']
        word_frequencies = {}
        for word in nltk.word_tokenize(formatted_article_text):
            if word not in mystopwords:
                if word not in word_frequencies.keys():
                    word_frequencies[word] = 1
                else:
                    word_frequencies[word] += 1
        if len(word_frequencies.values()) == 0:
            return None, "К сожалению мы не можем обработать данный текст. Если Вы считаете, что это произошло по ошибке, сообщите нам."
        maximum_frequncy = max(word_frequencies.values())

        for word in word_frequencies.keys():
            word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)
        sentence_scores = {}
        for sent in sentence_list:
            for word in nltk.word_tokenize(sent.lower()):
                if word in word_frequencies.keys():
                    if len(sent.split(' ')) < 30:
                        if sent not in sentence_scores.keys():
                            sentence_scores[sent] = word_frequencies[word]
                        else:
                            sentence_scores[sent] += word_frequencies[word]
        summary_sentences = heapq.nlargest(7, sentence_scores, key=sentence_scores.get)

        summary = ' '.join(summary_sentences)
        return summary, None

    def __make_content_video__(self, href):
        return {
            'type': 'video',
            'href': href,
        }

    def __make_content_image__(self, src):
        return {
            'type': 'image',
            'src': src,
        }

    def __in_apostrofs__(self, text):
        res = []
        while text.find('\"') != -1:
            first_index = text.find('\"')
            text = text[first_index + 1:]
            second_index = text.find('\"')
            if second_index == -1:
                break
            res.append(text[:second_index])
            text = text[second_index + 1:]
        return res

    def __save_search_cache__(self):
        with open('search_cache.json', 'w') as out:
            out.write(json.dumps(self.search_cache))

    def __make_search__(self, text):
        print("Searching for", text)
        if text in self.search_cache:
            return self.search_cache[text]
        try:
            query = {
                'search_query': text,
                'sp':YOUTUBE_FILTER
            }
            query = urllib.parse.urlencode(query)

            url = "https://www.youtube.com/results?" + query

            response = urllib.request.urlopen(url)
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')
            ans = []
            for video in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
                ans.append(video['href'])
            self.search_cache[text] = ans
            self.__save_search_cache__()
            return self.search_cache[text]
        except Exception as error:
            print(error)
            return []

    def __search__(self, text):
        words = text.split(' ')
        index = 0
        ans = []
        now = ''
        used = {}
        while index < len(words):
            if len(now) != 0:
                now += ' '
            now += words[index]
            if len(now) >= 30:
                buffer = self.__make_search__(now)
                for elem in buffer:
                    if not elem in used:
                        used[elem] = True
                        ans.append(elem)
                        if len(ans) > 6:
                            break
                now = ''
            index += 1
        if len(now) != 0:
            buffer = self.__make_search__(now)
            for elem in buffer:
                if not elem in used:
                    used[elem] = True
                    ans.append(elem)
                    if len(ans) > 6:
                        break
        return ans

    def analyze(self, text):
        text, error = self.__summarize__(text)
        if error != None:
            return None, error
        videos_href = {}
        videos = []
        for statement in text.split('.'):
            statement = statement.strip()
            if len(statement) == 0:
                continue
            videos_href[statement] = []
            in_apostrofs = self.__in_apostrofs__(statement)

            for video in self.__search__(statement):
                href = 'https://www.youtube.com' + video
                videos_href[statement].append(self.__make_content_video__(href))
                videos.append(href)
                print("Link:", href)

        print('Text length:', len(text))

        return {
            'emotion': DEFAULT_EMOTION,
            'videos': videos,
            'data': videos_href,
            'length': len(text) * .2
        }, None
