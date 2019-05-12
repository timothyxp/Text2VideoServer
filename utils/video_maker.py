import cv2
import numpy as np
import os
from data.ImageInterval import ImageInterval
from data.VideoInterval import VideoInterval

from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageSequenceClip, ImageClip
from utils.image_download import load_image

from utils.conf import *

from PIL import ImageFont, ImageDraw, Image

class VideoMakerBase:
    def make(self, intervals, emotions, icon=None, overlay=None):
        pass

class VideoMaker(VideoMakerBase):
    def __init__(self):
        self.index = 0

    def __next_index__(self):
        self.index = self.index + 1
        return str(self.index)

    def __apply_transformation__(self, file_path, duration):
        output_file_path = "tmp/" + self.__next_index__() + ".mp4"
        cap = cv2.VideoCapture(file_path)
        res_writer = cv2.VideoWriter(output_file_path, cv2.VideoWriter_fourcc(*'XVID'), VIDEO_FPS, (IMAGE_WIDTH, IMAGE_HEIGHT))

        scale = IMAGE_SCALING
        cur_time = 0.0

        while cap.isOpened():
            ret, frame = cap.read()
            if ret == False:
                break

            height, width, colors = frame.shape

            cur_time += 1.0 / VIDEO_FPS

            to_x = width / 2 * scale * cur_time / duration
            to_y = height / 2 * scale * cur_time / duration

            img = Image.fromarray(frame)
            img = img.crop((to_x, to_y, width - to_x, height - to_y))
            img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.ANTIALIAS)
            frame = np.array(img)
            res_writer.write(frame)

        cap.release()
        res_writer.release()
        return output_file_path

    def __make_image_video__(self, image_src, duration):
        file_path = "./tmp/{:s}.mp4".format(str(self.__next_index__()))
        clip = ImageClip(image_src, duration=duration)
        clip.write_videofile(file_path, fps=VIDEO_FPS)
        clip.close()

        file_path = self.__apply_transformation__(file_path, duration)

        return file_path

    def __make_video_video__(self, video_src, begin, end):
        file_path = "./tmp/{:s}.mp4".format(str(self.__next_index__()))
        clip = VideoFileClip(video_src).subclip(begin, end)
        clip.write_videofile(file_path, fps=VIDEO_FPS)
        clip.close()    
        return file_path

    def __merge_videos__(self, files):
        clips = []
        for file in files:
            clips.append(VideoFileClip(file))
        for clip in clips:
            print(clip.duration, clip.size, clip.fps)
        file_name = "./tmp/{:s}.mp4".format(self.__next_index__())
        merged_clip = concatenate_videoclips(clips)
        merged_clip.write_videofile(file_name, fps=VIDEO_FPS)
        merged_clip.close()
        for clip in clips:
            clip.close()
        return file_name

    def __make_drop_shadow__(self, frame):
        height, width, layers = frame.shape
        shadow = int(height * SHADOW_SIZE)
        for i in range(shadow):
            delta = i / shadow
            frame[height - 1 - i] *= delta * delta * delta
        return frame

    def __add_text_to_video__(self, file_name, intervals, duration, icon=None):
        icon_overlay = None
        icon_width = 0
        icon_height = 0
        if icon != None:
            icon_overlay = np.array(Image.open(icon).resize((ICON_SIZE, ICON_SIZE), Image.ANTIALIAS))
            icon_height, icon_width, _ = icon_overlay.shape
        output_file_name = "tmp/" + self.__next_index__() + ".mp4"
        cap = cv2.VideoCapture(file_name)
        amount = 0
        events_index = 0
        res_writer = cv2.VideoWriter(output_file_name, cv2.VideoWriter_fourcc(*'XVID'), VIDEO_FPS, (IMAGE_WIDTH, IMAGE_HEIGHT))
        fps = VIDEO_FPS
        cur_time = 0.0

        while cap.isOpened():
            ret, frame = cap.read()
            if ret == False:
                break
            frame = np.array(frame, dtype='float32') / 255
            
            cur_time += 1.0 / fps

            frame = self.__make_drop_shadow__(frame)
            frame *= 255
            frame = np.array(frame, dtype='uint8')

            height, width, colors = frame.shape

            while events_index < len(intervals) and cur_time >= intervals[events_index].end:
                events_index += 1

            if events_index >= 0 and events_index < len(intervals):
                interval = intervals[events_index]
                if interval.begin <= cur_time and cur_time < interval.end:
                    image_pil = Image.fromarray(frame)
                    draw = ImageDraw.Draw(image_pil)
                    font = ImageFont.truetype('fonts/Roboto-Regular.ttf', TEXT_SIZE)
                    text = interval.text
                    
                    textWidth = len(text) * 30

                    draw.text((width - TEXT_RIGHT_PADDING - textWidth, height - TEXT_SIZE - TEXT_BOTTOM_PADDING), text, font = font)
                    frame = np.array(image_pil)
            amount += 1
            if (amount + 1) % 10 == 0:
                print(amount + 1)

            if icon != None:
                for i in range(icon_height):
                    for j in range(icon_width):
                        if icon_overlay[i][j][3] != 0:
                            frame[ICON_MARGIN + i][ICON_MARGIN + j] = icon_overlay[i][j][:3]

            res_writer.write(frame)

        cap.release()
        res_writer.release()

        return output_file_name

    def __make_str_hash__(self, s):
        ans = 0
        for c in s:
            ans += ord(c)
        return ans

    def __make_hash__(self, intervals):
        mod = 100000000
        prime = 37
        cur = 0
        for interval in intervals:
            if type(interval) == ImageInterval:
                cur += interval.begin
                cur *= prime
                cur %= mod
                cur += interval.end
                cur *= prime
                cur %= mod
                cur += self.__make_str_hash__(interval.src)
                cur *= prime
                cur %= mod
            elif type(interval) == VideoInterval:
                cur += interval.begin
                cur *= prime
                cur %= mod
                cur += interval.end
                cur *= prime
                cur %= mod
                cur += self.__make_str_hash__(interval.src)
                cur *= prime
                cur %= mod
        cur += int(VIDEO_FPS)
        return str(cur)

    def __copy_to_file__(self, from_file, to_file):
        cap = cv2.VideoCapture(from_file)
        res_writer = cv2.VideoWriter(to_file, cv2.VideoWriter_fourcc(*'XVID'), VIDEO_FPS, (IMAGE_WIDTH, IMAGE_HEIGHT))

        while cap.isOpened():
            ret, frame = cap.read()
            if ret == False:
                break
            res_writer.write(frame)

        cap.release()
        res_writer.release()

    def make(self, intervals, emotions, icon=None, overlay=None):
        hsh = self.__make_hash__(intervals)
        if os.path.exists("tmp/" + hsh + ".mp4"):
            return "tmp/" + hsh + ".mp4"

        files = []
        duration = 0
        for i in range(len(intervals)):
            if type(intervals[i]) == ImageInterval:
                print("Working on making image video")
                img = load_image(intervals[i].src)
                file_name = self.__make_image_video__(img, intervals[i].end - intervals[i].begin)
                duration += intervals[i].end - intervals[i].begin
                files.append(file_name)
                print(file_name)
            elif type(intervals[i]) == VideoInterval:
                file_name = self.__make_video_video__(intervals[i].src, intervals[i].video_begin, intervals[i].video_end)
                duration += intervals[i].end - intervals[i].begin
                files.append(file_name)
            else:
                print("Unknown object")

        print()
        print(files)

        full = self.__merge_videos__(files)
        full_with_text = self.__add_text_to_video__(full, intervals, duration, icon)
        self.__copy_to_file__(full_with_text, "tmp/" + hsh + ".mp4")
        self.__copy_to_file__(full_with_text, "tmp/" + hsh + ".avi")
        return full_with_text