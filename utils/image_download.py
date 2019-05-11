from PIL import Image
import requests
from io import BytesIO
import numpy as np
from utils.conf import *

import os

def random_string():
    ans = ''
    for i in range(0, 20):
        ans += chr(ord('a') + np.random.randint(0, 25))
    return ans

def hsh(s):
    ans = ''
    for c in s:
        if not c in [',', '.', '\\', '/', ':', ';']:
            ans += c    
    return ans

def load_image(img_url):
    if img_url.find("downloaded") != -1:
        return img_url
    file_name = "downloaded/" + hsh(img_url) + '.jpg'
    print(file_name)

    if os.path.exists(file_name):
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
    print("Image size:", img.width, img.height)
    return file_name