import cv2
import numpy as np
import os
from data.ImageInterval import ImageInterval
from data.VideoInterval import VideoInterval

from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageSequenceClip, ImageClip, CompositeAudioClip, AudioClip, AudioFileClip
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

    def __add_text_to_video__(self, file_name, intervals, duration, icon=None, overlay=None):
        icon_overlay = None
        icon_width = 0
        icon_height = 0
        if icon != None:
            icon_overlay = np.array(Image.open(icon).resize((ICON_SIZE, ICON_SIZE), Image.ANTIALIAS))
            icon_height, icon_width, _ = icon_overlay.shape

        overlay_img = None
        overlay_width = 0
        overlay_height = 0
        if OVERLAY_ENABLED and overlay != None:
            img = Image.open(overlay)
            pref_width = int(IMAGE_HEIGHT * img.width / img.height)
            overlay_img = np.array(img.resize((pref_width, IMAGE_HEIGHT), Image.ANTIALIAS))
            overlay_height, overlay_width, _ = overlay_img.shape

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

            if overlay != None and OVERLAY_ENABLED:
                for i in range(overlay_height):
                    for j in range(overlay_width):
                        if overlay_img[i][j][3] >= 200:
                            frame[i][j] = overlay_img[i][j][:3]
            
            if icon != None:
                for i in range(icon_height):
                    for j in range(icon_width):
                        if icon_overlay[i][j][3] != 0:
                            frame[ICON_MARGIN + i][ICON_MARGIN + j] = icon_overlay[i][j][:3]

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
                    
                    splited = interval.text.split(' ')
                    cur = ''
                    txts = []
                    for s in splited:
                        if (len(cur) + len(s) + 1) * LETTER_WIDTH <= (IMAGE_WIDTH - 500) * 2:
                            if len(cur) != 0:
                                cur += " "
                            cur += s
                        else:
                            txts.append(cur)
                            cur = s
                    if len(cur) != 0:
                        txts.append(cur)

                    text = ""
                    cur_shift = 0
                    diff = (interval.end - interval.begin) / len(interval.text)
                    for txt in txts:
                        from_time = interval.begin + cur_shift
                        to_time = interval.begin + cur_shift + diff * len(txt)
                        if from_time <= cur_time and cur_time <= to_time:
                            text = txt
                        cur_shift += diff * len(txt)

                    textWidth = len(text) * LETTER_WIDTH
                    if textWidth <= IMAGE_WIDTH - 200:
                        if TEXT_MODE == 'RIGHT':
                            draw.text((width - TEXT_RIGHT_PADDING - textWidth, height - TEXT_SIZE - TEXT_BOTTOM_PADDING), text, font = font)
                        elif TEXT_MODE == 'CENTER':
                            draw.text((width // 2 - textWidth // 2, height - TEXT_SIZE - TEXT_BOTTOM_PADDING), text, font = font)
                        elif TEXT_MODE == 'LEFT':
                            draw.text((TEXT_RIGHT_PADDING, height - TEXT_SIZE - TEXT_BOTTOM_PADDING), text, font = font)
                    else:
                        line1 = []
                        line2 = text.split(' ')
                        len1 = 0
                        len2 = 0
                        for elem in line2:
                            len2 += len(elem)
                        len2 += len(line2) - 1
                        while len1 < len2:
                            line1.append(line2[0])
                            line2 = line2[1:]
                            len1 = 0
                            len2 = 0
                            for elem in line1:
                                len1 += len(elem)
                            len1 += len(line1) - 1
                            for elem in line2:
                                len2 += len(elem)
                            len2 += len(line2) - 1

                        text1 = ''
                        text2 = ''
                        for elem in line1:
                            if len(text1) != 0:
                                text1 += " "
                            text1 += elem
                        for elem in line2:
                            if len(text2) != 0:
                                text2 += " "
                            text2 += elem
                        if TEXT_MODE == 'RIGHT':
                            draw.text((width - TEXT_RIGHT_PADDING - len(text1) * LETTER_WIDTH, height - int(TEXT_SIZE * 1.4) - TEXT_BOTTOM_PADDING), text1, font = font)
                            draw.text((width - TEXT_RIGHT_PADDING - (len(text2) + (len(text1) - len(text2)) // 2) * LETTER_WIDTH, height - TEXT_BOTTOM_PADDING), text2, font = font)
                        elif TEXT_MODE == 'CENTER':
                            draw.text((width // 2 - len(text1) * LETTER_WIDTH // 2, height - int(TEXT_SIZE * 1.4) - TEXT_BOTTOM_PADDING), text1, font = font)
                            draw.text((width // 2 - len(text2) * LETTER_WIDTH // 2, height - TEXT_BOTTOM_PADDING), text2, font = font)
                        elif TEXT_MODE == 'LEFT':
                            draw.text((TEXT_RIGHT_PADDING, height - int(TEXT_SIZE * 1.4) - TEXT_BOTTOM_PADDING), text1, font = font)
                            draw.text((TEXT_RIGHT_PADDING, height - TEXT_BOTTOM_PADDING), text2, font = font)
                    frame = np.array(image_pil)
            amount += 1
            if (amount + 1) % 10 == 0:
                print(amount + 1)

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
        print(from_file, to_file)
        my_clip = VideoFileClip(from_file)
        my_clip.write_videofile(to_file)

    def __add_audio_to_video__(self, file_path, duration):
        print(file_path)
        my_clip = VideoFileClip(file_path)
        audio_background = AudioFileClip('downloaded/audio.mp3').subclip(0, duration - 1)
        final_audio = CompositeAudioClip([audio_background])
        final_clip = my_clip.set_audio(final_audio)
        result_path = "tmp/" + self.__next_index__() + ".mp4"
        final_clip.write_videofile(result_path)
        return result_path

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
        full_with_text = self.__add_text_to_video__(full, intervals, duration, icon, overlay)
        full_with_text_audio = self.__add_audio_to_video__(full_with_text, duration)
        # self.__copy_to_file__(full_with_text_audio, "tmp/" + hsh + ".mp4")
        return full_with_text_audio