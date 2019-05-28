import cv2
import numpy as np
import os
from data.ImageInterval import ImageInterval
from data.VideoInterval import VideoInterval

from server.app import working_status, saveWorkingStatus, saveTimings, setRenderTime, setRenderTimestamp, setProcessStatus
from utils.Timer import Timer

from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageSequenceClip, ImageClip, CompositeAudioClip, AudioClip, AudioFileClip
from utils.image_download import load_image

from utils.conf import *

from PIL import ImageFont, ImageDraw, Image

from flask_socketio import emit

import time

class VideoMakerBase:
    def make(self, intervals, emotions, config, icon=None, overlay=None):
        pass

class VideoMaker(VideoMakerBase):
    def __init__(self):
        self.index = working_status['max_video_index']

    def __next_index__(self):
        self.index = self.index + 1
        working_status['max_video_index'] = self.index
        saveWorkingStatus()
        return str(self.index)

    def __apply_transformation__(self, file_path, duration, config):
        output_file_path = "tmp/" + self.__next_index__() + ".mp4"
        cap = cv2.VideoCapture(file_path)
        res_writer = cv2.VideoWriter(output_file_path, cv2.VideoWriter_fourcc(*'XVID'), config['fps'], (config['width'], config['height']))

        scale = IMAGE_SCALING
        cur_time = 0.0

        while cap.isOpened():
            ret, frame = cap.read()
            if ret == False:
                break

            height, width, colors = frame.shape

            cur_time += 1.0 / config['fps']

            to_x = width / 2 * scale * cur_time / duration
            to_y = height / 2 * scale * cur_time / duration

            img = Image.fromarray(frame)
            img = img.crop((to_x, to_y, width - to_x, height - to_y))
            img = img.resize((config['width'], config['height']), Image.ANTIALIAS)
            frame = np.array(img)
            res_writer.write(frame)

        cap.release()
        res_writer.release()
        return output_file_path

    def __make_image_video__(self, image_src, duration, config):
        file_path = "./tmp/{:s}.mp4".format(str(self.__next_index__()))
        clip = ImageClip(image_src, duration=duration)
        clip.write_videofile(file_path, fps=config['fps'])
        clip.close()

        file_path = self.__apply_transformation__(file_path, duration, config)

        return file_path

    def __make_video_video__(self, video_src, begin, end, config):
        file_path = "./tmp/{:s}.mp4".format(str(self.__next_index__()))
        print("Making video from video", video_src, begin, end, file_path)
        clip = VideoFileClip(video_src).subclip(begin, end).resize((config['width'], config['height']))
        clip.write_videofile(file_path, fps=config['fps'])
        clip.close()    
        return file_path

    def __merge_videos__(self, files, config):
        clips = []
        for file in files:
            clips.append(VideoFileClip(file))
        for clip in clips:
            print(clip.duration, clip.size, clip.fps)
        file_name = "./tmp/{:s}.mp4".format(self.__next_index__())
        merged_clip = concatenate_videoclips(clips)
        merged_clip.write_videofile(file_name, fps=config['fps'])
        merged_clip.close()
        for clip in clips:
            clip.close()
        return file_name

    def __make_drop_shadow__(self, frame, config):
        height, width, layers = frame.shape
        if config['shadowEnabled']:
            shadow = int(height * config['shadowSize'])
            for i in range(shadow):
                delta = i / shadow
                frame[height - 1 - i] *= delta * delta * delta
        return frame

    def __add_text_to_video__(self, file_name, intervals, duration, config, icon=None, overlay=None):
        font = ImageFont.truetype('fonts/Roboto-Regular.ttf', config['textSize'])

        icon_overlay = None
        icon_width = 0
        icon_height = 0
        if icon != None:
            icon_overlay = np.array(Image.open(icon).resize((config['iconSize'], config['iconSize']), Image.ANTIALIAS))
            icon_height, icon_width, _ = icon_overlay.shape

        overlay_img = None
        overlay_width = 0
        overlay_height = 0
        if OVERLAY_ENABLED and overlay != None:
            img = Image.open(overlay)
            pref_width = int(config['height'] * img.width / img.height)
            overlay_img = np.array(img.resize((pref_width, IMAGE_HEIGHT), Image.ANTIALIAS))
            overlay_height, overlay_width, _ = overlay_img.shape

        output_file_name = "tmp/" + self.__next_index__() + ".mp4"
        cap = cv2.VideoCapture(file_name)
        amount = 0
        events_index = 0
        res_writer = cv2.VideoWriter(output_file_name, cv2.VideoWriter_fourcc(*'XVID'), config['fps'], (config['width'], config['height']))
        fps = config['fps']
        cur_time = 0.0

        while cap.isOpened():
            ret, frame = cap.read()
            if ret == False:
                break
                
            if icon != None:
                for i in range(icon_height):
                    for j in range(icon_width):
                        if icon_overlay[i][j][3] != 0:
                            r = icon_overlay[i][j][2]
                            g = icon_overlay[i][j][1]
                            b = icon_overlay[i][j][0]
                            a = icon_overlay[i][j][3]
                            frame[config['iconMargin'] + i][config['iconMargin'] + j] = [r, g, b]
            
            if overlay != None and OVERLAY_ENABLED:
                for i in range(overlay_height):
                    for j in range(overlay_width):
                        if overlay_img[i][j][3] >= 200:
                            frame[i][j] = overlay_img[i][j][:3]

            frame = np.array(frame, dtype='float32') / 255
            
            cur_time += 1.0 / fps

            frame = self.__make_drop_shadow__(frame, config)
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
                    
                    splited = interval.text.split(' ')
                    cur = ''
                    txts = []
                    for s in splited:
                        if (len(cur) + len(s) + 1) * config['letterWidth'] <= (config['width'] - 500) * 2:
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

                    textWidth = len(text) * config['letterWidth']
                    if textWidth <= config['width'] - 200:
                        if config['textMode'] == 'RIGHT':
                            draw.text((width - TEXT_RIGHT_PADDING - textWidth, height - config['textSize'] - TEXT_BOTTOM_PADDING), text, font = font)
                        elif config['textMode'] == 'CENTER':
                            draw.text((width // 2 - textWidth // 2, height - config['textSize'] - TEXT_BOTTOM_PADDING), text, font = font)
                        elif config['textMode'] == 'LEFT':
                            draw.text((TEXT_RIGHT_PADDING, height - config['textSize'] - TEXT_BOTTOM_PADDING), text, font = font)
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
                        if config['textMode'] == 'RIGHT':
                            draw.text((width - TEXT_RIGHT_PADDING - len(text1) * LETTER_WIDTH, height - int(config['textSize'] * 1.4) - TEXT_BOTTOM_PADDING), text1, font = font)
                            draw.text((width - TEXT_RIGHT_PADDING - (len(text2) + (len(text1) - len(text2)) // 2) * config['letterWidth'], height - TEXT_BOTTOM_PADDING), text2, font = font)
                        elif config['textMode'] == 'CENTER':
                            draw.text((width // 2 - len(text1) * config['letterWidth'] // 2, height - int(config['textSize'] * 1.4) - TEXT_BOTTOM_PADDING), text1, font = font)
                            draw.text((width // 2 - len(text2) * config['letterWidth'] // 2, height - TEXT_BOTTOM_PADDING), text2, font = font)
                        elif config['textMode'] == 'LEFT':
                            draw.text((TEXT_RIGHT_PADDING, height - int(config['textSize'] * 1.4) - TEXT_BOTTOM_PADDING), text1, font = font)
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

    def __make_hash__(self, intervals, config):
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
        cur += int(config['fps'])
        return str(cur)

    def __copy_to_file__(self, from_file, to_file):
        print(from_file, to_file)
        my_clip = VideoFileClip(from_file)
        my_clip.write_videofile(to_file)

    def __add_audio_to_video__(self, file_path, duration, config):
        print(file_path)
        my_clip = VideoFileClip(file_path)
        audio_background = AudioFileClip('downloaded/audio.mp3').subclip(0, duration - 1)
        final_audio = CompositeAudioClip([audio_background])
        final_clip = my_clip.set_audio(final_audio)
        result_path = "tmp/" + self.__next_index__() + ".mp4"
        final_clip.write_videofile(result_path)
        return result_path

    def make(self, intervals, emotions, config, current_id=None, icon=None, overlay=None):
        setRenderTimestamp(current_id, time.time())
        makeTimer = Timer()
        timer = Timer()
        timings = {
            'intervals': []
        }
        makeTimer.start()
        hsh = self.__make_hash__(intervals, config)
        if os.path.exists("tmp/" + hsh + ".mp4"):
            return "tmp/" + hsh + ".mp4"
        files = []
        duration = 0
        setProcessStatus(current_id, "Создаем структуру")
        saveWorkingStatus()
        index = 0
        for i in range(len(intervals)):
            timings['intervals'].append({})
            if type(intervals[i]) == ImageInterval:
                print("Working on making image video")
                timer.start()
                img = load_image(intervals[i].src)
                timings['intervals'][-1]['load_image'] = timer.end()
                timer.start()
                file_name = self.__make_image_video__(img, intervals[i].end - intervals[i].begin, config)
                timings['intervals'][-1]['__make_image_video__'] = timer.end()
                duration += intervals[i].end - intervals[i].begin
                files.append(file_name)
                print(file_name)
            elif type(intervals[i]) == VideoInterval:
                timer.start()
                file_name = self.__make_video_video__(intervals[i].src, intervals[i].video_begin, intervals[i].video_end, config)
                timings['intervals'][-1]['__make_video_video__'] = timer.end()
                duration += intervals[i].end - intervals[i].begin
                files.append(file_name)
            else:
                print("Unknown object")
            index += 1
            setProcessStatus(current_id, "Готово фрагментов: {:d}/{:d}".format(index, len(intervals)))
            saveTimings(current_id, timings)
        print(files)
        setProcessStatus(current_id, "Сливаем видео")
        timer.start()
        full = self.__merge_videos__(files, config)
        timings['__merge_videos__'] = timer.end()
        saveTimings(current_id, timings)
        setProcessStatus(current_id, "Добавляем текст")
        timer.start()
        full_with_text = self.__add_text_to_video__(full, intervals, duration, config, icon=icon, overlay=overlay)
        timings['__add_text_to_video__'] = timer.end()
        saveTimings(current_id, timings)
        setProcessStatus(current_id, "Добавляем аудио")
        timer.start()
        full_with_text_audio = self.__add_audio_to_video__(full_with_text, duration, config)
        timings['__add_audio_to_video__'] = timer.end()
        saveTimings(current_id, timings)
        # self.__copy_to_file__(full_with_text_audio, "tmp/" + hsh + ".mp4")
        setRenderTime(current_id, makeTimer.end())
        return full_with_text_audio