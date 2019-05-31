from PIL import Image
import requests
from io import BytesIO
import numpy as np
from utils.conf import *
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from utils.logging.logger import logger
from config import DOWNLOAD_PATH
import os.path
from requests_html import HTMLSession


def random_string():
    ans = ''
    for i in range(0, 20):
        ans += chr(ord('a') + np.random.randint(0, 25))
    return ans


def hsh(s):
    return ''.join(filter(lambda char: char not in [',', '.', '\\', '/', ':', ';', '&', '='], s))


def load_image(img_url):
    file_name = os.path.join(DOWNLOAD_PATH, hsh(img_url) + '.jpg')
    logger.debug(f"file for image {file_name}")

    if os.path.exists(file_name):
        logger.debug("find image")
        return file_name

    response = requests.get(img_url)
    img = Image.open(BytesIO(response.content))
    width = img.width
    height = img.height
    if width % 2 == 1:
        width -= 1
    if height % 2 == 1:
        height -= 1
    img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.ANTIALIAS)
    img.save(file_name)
    logger.debug(f"Image with size: {img.width}  {img.height} save to {file_name}")
    return file_name


def find_images(text, limit=1):
    logger.debug(f"start find images for {text}")
    try:
        query = {
            "text": text
        }

        query = urllib.parse.urlencode(query)

        url = "https://yandex.ru/images/search?" + query
        logger.debug(f"get url {url}")

        response = urllib.request.urlopen(url)
        html = response.read()

        soup = BeautifulSoup(html, "html.parser")

        images = []
        for image in soup.find_all(attrs={"class": "serp-item__link"}):
            images.append(image["href"])

        logger.debug(f"get {len(images)} images before limiting")

        limit = min(limit, len(images))
        images = images[:limit]

        logger.info(f"get {len(images)} images")

        hrefs = []

        for href in images:
            url = "https://yandex.ru" + href

            logger.debug(f"get image from {url}")

            session = HTMLSession()

            response = session.get(url)
            response.html.render()

            logger.debug(response.html)

            images = response.html.find('.preview2__arrow-image')

            logger.debug(images)

            src = None
            for image in images:
                logger.debug(image.attrs)
                try:
                    test_src = image.attrs["src"]
                    logger.debug(f"find src {src}")
                    src = test_src
                    break
                except Exception as error:
                    logger.error(error)

            if src is not None:
                hrefs.append(src)

        return hrefs
    except Exception as error:
        logger.error(error)
        return []