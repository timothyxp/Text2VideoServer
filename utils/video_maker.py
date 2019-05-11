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

    def __make_image_video__(self, image_src, duration):
        file_path = "./tmp/{:s}.mp4".format(str(self.__next_index__()))
        clip = ImageClip(image_src, duration=duration)
        clip.write_videofile(file_path, fps=VIDEO_FPS)
        clip.close()
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
            frame[height - 1 - i] *= delta * delta * delta * delta
        return frame

    def __add_text_to_video__(self, file_name, intervals, duration, icon=None):
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
                    
                    textWidth = len(text) * 15

                    draw.text((width - TEXT_RIGHT_PADDING - textWidth, height - TEXT_BOTTOM_PADDING), text, font = font)
                    frame = np.array(image_pil)
            amount += 1
            if (amount + 1) % 10 == 0:
                print(amount + 1)

            if icon != None:
                pass

            res_writer.write(frame)

        cap.release()
        res_writer.release()

        return output_file_name

    def make(self, intervals, emotions, icon=None, overlay=None):
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
        return full_with_text