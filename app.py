import os
from datetime import datetime
import re
from predict import Predictor

from flask import Flask, request
from subsai import SubsAI
from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips, CompositeVideoClip
from moviepy.editor import VideoFileClip, TextClip, ImageClip, vfx
import moviepy.editor as mp
import fnmatch
from rembg import remove
import cv2
from PIL import Image
import io
import numpy as np

app = Flask(__name__)

@app.post('/rmbackground')
def rmbackground():
  json = request.get_json()
  input_path = json['image_path']
  output_path = json['output_path']

  with open(input_path, 'rb') as i:
    input = i.read()
    output = remove(input)
    output_image = Image.open(io.BytesIO(output))
    green_bg = Image.new("RGBA", output_image.size, (0, 255, 0, 255))
    green_bg.paste(output_image, (0, 0), output_image)
    with open(output_path, 'wb') as o:
      green_bg.save(o, "PNG")
  return 'ok', 200
        
@app.post('/gen')
def gen():
  json = request.get_json()
  audio_path = json['audio_path']
  image_path = json['image_path']
  result_dir = json['result_dir']

  sad_talker = Predictor()
  sad_talker.predict(
    image_path, 
    audio_path, 
    result_dir=result_dir, 
    preprocess='crop',
    enhancer=None,
    ref_eyeblink=None,
    ref_pose=None,
    still=False,
  )
  return 'ok', 200

@app.post('/convert_mp4_to_wav')
def convert_mp4_to_wav():
  json = request.get_json()
  mp4_path = json['mp4_path']
  wav_path = json['wav_path']

  AudioFileClip(mp4_path).write_audiofile(wav_path)
  return 'ok', 200
        
@app.post('/gen_subtitle')
def gen_subtitle():
  json = request.get_json()
  file_path = json['file_path']
  output_path = json['output_path']

  model = 'openai/whisper' # 'linto-ai/whisper-timestamped'

  subs_ai = SubsAI()
  model = subs_ai.create_model(model, {'model_type': 'large'})
  subs = subs_ai.transcribe(file_path, model)
  subs.save(output_path)
  return 'ok', 200


# 从 SRT 格式的时间字符串中提取时间（以秒为单位）
def extract_time(time_str):
  time_format = "%H:%M:%S,%f"
  datetime_obj = datetime.strptime(time_str, time_format)
  return datetime_obj.hour * 3600 + datetime_obj.minute * 60 + datetime_obj.second + datetime_obj.microsecond / 1000000

# 从 SRT 格式的字幕文件中解析字幕
def parse_subtitles(subtitle_path):
  with open(subtitle_path, 'r') as f:
    content = f.read()
  blocks = re.split(r'\n\n', content)
  subtitles = []
  for block in blocks:
    lines = block.split('\n')
    if len(lines) >= 3:
      time_range = lines[1]
      text = ' '.join(lines[2:])
      start_time_str, end_time_str = time_range.split(' --> ')
      start_time = extract_time(start_time_str)
      end_time = extract_time(end_time_str)
      duration = end_time - start_time
      subtitles.append((start_time, duration, text))
  return subtitles

@app.post('/merge_video_and_subtitle')
def merge_video_and_subtitle():
  json = request.get_json()
  video_path = json['video_path']
  subtitle_path = json['subtitle_path']
  output_path = json['output_path']

  print(video_path, subtitle_path, output_path)
  video = VideoFileClip(video_path)
  subtitles = parse_subtitles(subtitle_path)
    
  subtitle_clips = [
    TextClip(txt, fontsize=36, color='black', font='./NotoSansCJK-Regular.ttc')
    .set_start(start)
    .set_duration(duration)
    .set_position(('center', 'bottom'))
  for start, duration, txt in subtitles]
  video = CompositeVideoClip([video] + subtitle_clips)
  video.write_videofile(output_path)
  return 'ok', 200

# @app.post('/merge_video_and_subtitle')
# def set_subtitle():
#   json = request.get_json()
  
#   video_path = json['video_path']
#   subtitles = json['subtitles']
#   output_path = json['output_path']
#   # print(video_path, output_path)
#   video = VideoFileClip(video_path)
  
#   subtitle_setting = []
#   for sub in subtitles:
#     text = sub['text']
#     fontsize = sub['fontsize']
#     color = sub['color']
#     font = sub['font']
#     start_time = sub['start_time']
#     end_time = sub['end_time']
#     start = extract_time(start_time)
#     end = extract_time(end_time)
#     duration = end - start
#     subtitle_setting.append((text, start, duration, fontsize, color, font))
      
#   subtitle_clips = [
#     TextClip(text, fontsize=fontsize, color=color, font=font)
#     .set_start(start)
#     .set_duration(duration)
#     .set_position(('center', 'bottom'))
#   for text, start, duration, fontsize, color, font in subtitles]
#   video = CompositeVideoClip([video] + subtitle_clips)
#   video.write_videofile(output_path)

#   return 'ok', 200

@app.post('/merge_avatar_video_chunks')
def merge_avatar_video_chunks():
  json = request.get_json()
  chunks_dir = json['chunks_dir']
  output_path = json['output_path']

  chunk_files = sorted(os.listdir(chunks_dir))
  chunks = []
  chunks_times = 0
  for chunk_file in chunk_files:
    if fnmatch.fnmatch(chunk_file, f'*chunk_{chunks_times}.mp4'):
      chunks_times += 1
      print(chunk_file)
      chunk = VideoFileClip(os.path.join(chunks_dir, chunk_file))
      chunks.append(chunk)
  if len(chunks) == 0:
    return 'no chunks', 400
  final_clip = concatenate_videoclips(chunks)
  final_clip.write_videofile(output_path)
  return 'ok', 200

def remove_green_background(image):
  # 34, 177, 76
  image = image.copy()
  lower_green = np.array([25, 160, 60], dtype=np.uint8)
  upper_green = np.array([45, 185, 85], dtype=np.uint8)

  mask = cv2.inRange(image, lower_green, upper_green)

  image[mask, :, :] = [0, 0, 0] * 255
  return image

@app.post('/merge_video_and_avatar_video')
def merge_video_and_avatar_video():
  json = request.get_json()
  main_video_path = json['main_video_path']
  avatar_video_path = json['avatar_video_path']
  output_path = json['output_path']
  avatar_shape = json['avatar_shape'] # square, circle, rembg
  position = json['position']

  position = tuple(map(float, position[1:-1].split(',')))
  main_video = VideoFileClip(main_video_path)
  avatar_video = VideoFileClip(avatar_video_path)

  green_screen = np.array([0, 255, 0])
  #avatar_video = vfx.mask_color(avatar_video, green_screen, thr=1, s=0)
  
  avatar_video = avatar_video.fx(vfx.mask_color, green_screen, thr=200, s=20)
  
  position = (main_video.size[0] * position[0], main_video.size[1] * position[1])

  if avatar_shape == 'circle':
    mask = ImageClip('./circle.png', ismask=True, fromalpha=True).to_mask()
    mask = mask.resize(avatar_video.size)
    avatar_video = avatar_video.set_mask(mask)

  final_video = CompositeVideoClip([main_video, avatar_video.set_position(position)])
  final_video.write_videofile(output_path)
  return 'ok', 200

@app.get('/health/<string:test>/<string:output_path>')
def health(test, output_path):
  return f'{test} {output_path}', 200
