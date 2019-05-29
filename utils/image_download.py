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
import os

import os


def random_string():
    ans = ''
    for i in range(0, 20):
        ans += chr(ord('a') + np.random.randint(0, 25))
    return ans


def hsh(s):
    return ''.join(filter(lambda char: char not in [',', '.', '\\', '/', ':', ';', '&', '='], s))


def load_image(img_url):
    #if img_url.find("downloaded") != -1:
    #    return img_url
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


def find_images(text):
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
        for image in soup.find_all(attrs={"class": "serp-item__thumb justifier__thumb"}):
            images.append(image["src"])

        logger.info(f"get {len(images)} images")

        return images
    except Exception as error:
        logger.error(error)
        return []
