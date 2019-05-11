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

class TextAnalyzeBase(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def analyze(self, text):
       pass

class TextAnalyze(TextAnalyzeBase):
    def __summarize__(self, article_text):
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
        import heapq  
        summary_sentences = heapq.nlargest(7, sentence_scores, key=sentence_scores.get)

        summary = ' '.join(summary_sentences)
        return summary

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

    def analyze(self, text):
        text = self.__summarize__(text)
        videos_href = {}
        videos = []
        for statement in text.split('.'):
            if len(statement) == 0:
                continue
            print("Searching for:", statement)
            query = {
                'search_query': statement,
                'sp':YOUTUBE_FILTER
            }
            videos_href[statement] = []
            query = urllib.parse.urlencode(query)

            url = f"https://www.youtube.com/results?" + query

            response = urllib.request.urlopen(url)
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')

            for video in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
                href = 'https://www.youtube.com' + video['href']
                videos_href[statement].append(self.__make_content_video__(href))
                videos.append(href)
                print("Link:", href)

        return {
            'emotion': DEFAULT_EMOTION,
            'videos': videos,
            # 'images': [
            #     'https://avatars.mds.yandex.net/get-marketpic/1594519/market_CbgUEV3RDAUW1iIYtYTxAg/orig',
            #     'https://wallbox.ru/wallpapers/main/201239/eda-a3605149a117.jpg',
            #     'https://im0-tub-ru.yandex.net/i?id=77bb6764fc6a184f1517caf6567bce4f&n=13'
            # ],
            'data': videos_href,
            'length': len(text) * 1.3
        }
