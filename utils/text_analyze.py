from abc import abstractmethod, ABC


class TextAnalyzeBase(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def analyze(self, text):
        return {
            'emotion': 'angry',
            'videos': [
                'https://www.youtube.com/watch?v=nDSe9kRWQXA',
                'https://www.youtube.com/watch?v=nDSe9kRWQXA',
                'https://www.youtube.com/watch?v=cKkGhZGA3ac',
                'https://www.youtube.com/watch?v=KpRkek6glbA'
            ],
            'images':[
                'https://avatars.mds.yandex.net/get-marketpic/1594519/market_CbgUEV3RDAUW1iIYtYTxAg/orig',
                'https://wallbox.ru/wallpapers/main/201239/eda-a3605149a117.jpg',
                'https://im0-tub-ru.yandex.net/i?id=77bb6764fc6a184f1517caf6567bce4f&n=13'
            ],
            'length': 54
        }
