from subsai import SubsAI
from argparse import ArgumentParser
import os

def main(args):
  file = args.file
  output_crt = os.path.join(args.save_dir, 'output_crt.srt')
  model = 'openai/whisper' # 'linto-ai/whisper-timestamped'

  subs_ai = SubsAI()
  model = subs_ai.create_model(model, {'model_type': 'large'})
  subs = subs_ai.transcribe(file, model)
  subs.save(output_crt)
  output_srt = os.path.join(args.save_dir, 'styled_output_crt.srt')
  style_srt_subtitle(output_crt, output_srt)

if __name__ == '__main__':
    
  parser = ArgumentParser()
  parser.add_argument("--file", default='./data/sheng-cheng-shi-ai-yong-chatgpt-he-midjourney-lai-wan-wen-zi-mou-xian-you-xi.mp4', help="path to source video")
  parser.add_argument("--save_dir", default='./results', help="path to output")

  args = parser.parse_args()
  main(args)

def style_srt_subtitle(input_srt, output_srt):
    with open(input_srt, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    # 在每個字幕文本前後添加HTML標籤以設定顏色和字體樣式
    styled_srt_content = ""
    for line in srt_content.split('\n\n'):
        lines = line.split('\n')
        if len(lines) >= 3:
            subtitle_time = lines[1]
            subtitle_text = "\n".join(lines[2:])
            styled_subtitle_text = f'<font color="blue"><b>{subtitle_text}</b></font>'
            styled_srt_content += f"{lines[0]}\n{subtitle_time}\n{styled_subtitle_text}\n\n"

    with open(output_srt, 'w', encoding='utf-8') as f:
        f.write(styled_srt_content)