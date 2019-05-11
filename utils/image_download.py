from PIL import Image
import requests
from io import BytesIO
import numpy as np
from utils.conf import *

def random_string():
    ans = ''
    for i in range(0, 20):
        ans += chr(ord('a') + np.random.randint(0, 25))
    return ans

def load_image(img_url):
    response = requests.get(img_url)
    img = Image.open(BytesIO(response.content))
    width = img.width
    height = img.height
    if width % 2 == 1:
        width -= 1
    if height % 2 == 1:
        height -= 1
    img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.ANTIALIAS)
    file_name = "downloaded/" + random_string() + '.jpg'
    img.save(file_name)
    print("Image size:", img.width, img.height)
    return file_name