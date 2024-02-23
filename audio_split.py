from pydub import AudioSegment
from pydub.silence import split_on_silence
import os

def split_audio(filepath: str, min_per_slice=60, silence_thresh=-40, silence_len=500):
  # 將檔案轉為 AudioSegment 物件
  sound = AudioSegment.from_file(filepath, format='wav')

  # 使用 split_on_silence 切割音訊
  audio_chunks = split_on_silence(
    sound,
    min_silence_len=silence_len,
    silence_thresh=silence_thresh,
    keep_silence=True,
  )

  # 確保每個切割的音訊長度都至少有 min_per_slice 秒
  target_length = min_per_slice * 1000
  output_chunks = [audio_chunks[0]]
  for chunk in audio_chunks[1:]:
    if len(output_chunks[-1]) < target_length:
      output_chunks[-1] += chunk
    else:
      output_chunks.append(chunk)

  # 確認目標目錄存在，如果不存在則建立該目錄
  filepaths = filepath.split('/')
  dest = '/'.join(filepaths[:-1]) + '/dest/'
  if not os.path.isdir(dest):
    os.makedirs(dest)

  datas = []
  end_time = 0
  for i, chunk in enumerate(output_chunks):
    start_time = end_time
    end_time = start_time + chunk.duration_seconds
    datas.append({'start_time': start_time, 'end_time': end_time, 'path': f'{dest}chunk_{i}.wav'})
    
    chunk.export(f'{dest}chunk_{i}.wav', format='wav')

  return datas

if __name__ == '__main__':
  datas = split_audio('./data/audio.wav', min_per_slice=10, silence_len=500)

  # Print the timestamps
  for i, time_range in enumerate(datas):
    s = time_range['start_time']
    e = time_range['end_time']
    print(f'Chunk {i+1} starts at {s}s and ends at {e}s')
