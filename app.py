# -*- coding: utf-8 -*-
import time
import base64
import requests
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
from picamera import PiCamera
from gpiozero import Button
import threading
import logging
from collections import defaultdict
from pydub import AudioSegment
from pydub.playback import play

# 设置日志记录
logging.basicConfig(filename='/home/用户/app.log', level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s:%(message)s')

app = Flask(__name__)

# 百度API信息
image_api_key = 'XXXXXXXXXXXXXXX'
image_secret_key = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
tts_api_key = 'YYYYYYYYYYYYYYYYYYYY'
tts_secret_key = 'YYYYYYYYYYYYYYYYYYYYYYYYYYYYYY'

# 初始化摄像头
camera = PiCamera()

# 初始化I2C接口和OLED显示
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

# 加载中文字体
font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 14)

# 初始化按钮
button = Button(17)

# 全局变量保存状态
status = {
    "image_path": "static/zhanwei.png",
    "result": None,
    "status_message": "请按按钮拍照识别物体",
    "timestamp": 0
}

def capture_image():
    timestamp = int(time.time() * 1000)
    image_path = f'/home/用户/static/image_{timestamp}.jpg'  # 使用带时间戳的路径
    camera.capture(image_path)
    status["image_path"] = f"static/image_{timestamp}.jpg"
    status["timestamp"] = timestamp
    logging.debug(f"Image captured: {status['image_path']}")
    return image_path

def get_access_token(api_key, secret_key):
    url = 'https://aip.baidubce.com/oauth/2.0/token'
    params = {
        'grant_type': 'client_credentials',
        'client_id': api_key,
        'client_secret': secret_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        result = response.json()
        logging.debug("Access token obtained")
        return result['access_token']
    else:
        logging.error(f"Failed to get access token: {response.json()}")
    return None

def recognize_image(image_path):
    with open(image_path, 'rb') as f:
        image_data = f.read()
    base64_image = base64.b64encode(image_data).decode('utf-8')

    access_token = get_access_token(image_api_key, image_secret_key)
    if not access_token:
        logging.error("No access token available")
        return None

    url = f'https://aip.baidubce.com/rest/2.0/image-classify/v2/advanced_general?access_token={access_token}'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'image': base64_image}

    response = requests.post(url, headers=headers, data=data)
    logging.debug(f"API Response: {response.json()}")
    if response.status_code == 200:
        result = response.json()
        status["result"] = aggregate_results(result["result"])
        return result
    else:
        logging.error(f"Error in API response: {response.json()}")
    return None

def aggregate_results(results):
    aggregated = defaultdict(float)
    for item in results:
        aggregated[item['keyword']] += item['score']
    return [{'keyword': k, 'score': v} for k, v in aggregated.items() if v >= 0.3]

def display_on_oled(message):
    device.clear()
    with canvas(device) as draw:
        draw.text((0, 0), message, font=font, fill="white")
    logging.debug(f"Displayed on OLED: {message}")

def speak(text):
    access_token = get_access_token(tts_api_key, tts_secret_key)
    if not access_token:
        logging.error("No access token available for TTS")
        return
    
    url = 'https://tsn.baidu.com/text2audio'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'tex': text,
        'tok': access_token,
        'cuid': 'raspberrypi',
        'ctp': 1,
        'lan': 'zh',
        'aue': 6,  # wav
        'spd': 5,  # 语速，取值0-15，默认为5中语速
        'pit': 5,  # 音调，取值0-15，默认为5中语调
        'vol': 5,  # 音量，取值0-15，默认为5中音量
        'per': 0   # 发音人，取值0为女声，1为男声，3为度逍遥，4为度丫丫
    }
    response = requests.post(url, headers=headers, data=data)
    logging.debug(f"TTS Response Headers: {response.headers}")
    logging.debug(f"TTS Response Content: {response.content[:100]}...")  # 只显示前100个字节
    if response.headers['Content-Type'] == 'audio/wav':
        with open('/home/用户/speech.wav', 'wb') as f:
            f.write(response.content)
        logging.debug("Speech WAV saved.")
        sound = AudioSegment.from_wav('/home/用户/speech.wav')
        play(sound)
    else:
        logging.error("Error in TTS response: Response is not audio")

def capture_and_recognize():
    status["status_message"] = "拍照中..."
    logging.debug("Button pressed, capturing image")
    image_path = capture_image()
    result = recognize_image(image_path)
    if result and 'result' in result:
        display_result_on_oled(result['result'])
        create_tts_message(result['result'])
    else:
        display_on_oled("未检测到符合条件的物体")
        speak("图片中没有我能判断出来的物品")
    status["status_message"] = "请按按钮拍照识别物体"

def display_result_on_oled(result):
    device.clear()
    combined_text = ""
    with canvas(device) as draw:
        y = 0
        for item in result:
            text = f"{item['keyword']} {item['score']:.2f}"
            draw.text((0, y), text, font=font, fill="white")
            combined_text += f"{item['keyword']}，置信度 {item['score']:.2f}. "
            y += 14
            if y > 64:  # 防止超出屏幕
                break
    logging.debug("Result displayed on OLED")
    threading.Timer(30, reset_display).start()  # 启动30秒计时器

def create_tts_message(result):
    if not result:
        speak("镜头中没有我能判断出来的物体")
        return
    
    items = [item['keyword'] for item in result]
    if len(items) > 1:
        message = "镜头中的物品可能有" + "、".join(items[:-1]) + "和" + items[-1]
    else:
        message = "镜头中的物品可能有" + items[0]
    speak(message)

def reset_display():
    # 清空结果并重置图片路径
    status["image_path"] = "static/zhanwei.png"
    status["result"] = None
    display_on_oled("请按按钮拍照识别物体")
    logging.debug("OLED display reset")

@app.route('/')
def index():
    return render_template('index.html', status=status)

@app.route('/capture')
def capture():
    capture_and_recognize()
    return jsonify(status)

@app.route('/status')
def get_status():
    return jsonify(status)

if __name__ == '__main__':
    display_on_oled("请按按钮拍照识别物体")
    button.when_pressed = capture_and_recognize
    app.run(host='0.0.0.0', port=5000)

