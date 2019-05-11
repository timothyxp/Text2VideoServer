from abc import abstractmethod, ABC
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

from config import DEFAULT_EMOTION, YOUTUBE_FILTER


class TextAnalyzeBase(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def analyze(self, text):
       pass


class TextAnalyze(TextAnalyzeBase):
    def analyze(self, text):
        videos_href = []

        for statement in text.split('.'):
            query = f"{statement}&sp={YOUTUBE_FILTER}"

            url = f"https://www.youtube.com/results?search_query=" + query
            response = urllib.request.urlopen(url)
            html = response.read()
            soup = BeautifulSoup(html, 'html.parser')

            for video in soup.findAll(attrs={'class': 'yt-uix-tile-link'}):
                href = 'https://www.youtube.com' + video['href']
                videos_href.append(href)
                break

        count_words = len(list(filter(lambda x: x != '', text.replace('/n', ' ').replace(',', ' ').split(' '))))

        return {
            'emotion': DEFAULT_EMOTION,
            'videos': videos_href,
            'images': [
                'https://avatars.mds.yandex.net/get-marketpic/1594519/market_CbgUEV3RDAUW1iIYtYTxAg/orig',
                'https://wallbox.ru/wallpapers/main/201239/eda-a3605149a117.jpg',
                'https://im0-tub-ru.yandex.net/i?id=77bb6764fc6a184f1517caf6567bce4f&n=13'
            ],
            'length': count_words * 2
        }


if __name__ == "__main__":
    an=TextAnalyze()

    print(an.analyze('rkek'))
