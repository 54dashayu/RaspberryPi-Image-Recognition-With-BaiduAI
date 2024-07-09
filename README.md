我不会编程，是一个新手，大部分代码是由ChatGPT帮我完成。这是我的第一个GitHub项目，感谢大家！

我使用树莓派3B+和树莓派摄像头制作了一个项目，在你的帮助下完程的，可以实现拍照后调用百度大模型识别镜头前的物体，并使用百度语音TTS功能在树莓派3.5mm音频接口播放语音。

![image](https://github.com/54dashayu/RaspberryPi-Image-Recognition-With-BaiduAI/assets/7693331/5f0ffa2d-5c49-48c6-b826-4aaa8dd845c7)

本项目图像识别使用了百度千帆大模型公有云通用物体识别API（免费体验），TTS语音生成使用百度在线语音合成API（按Token后付费），请自行申请：https://cloud.baidu.com/?from=console。  

![image](https://github.com/54dashayu/RaspberryPi-Image-Recognition-With-BaiduAI/assets/7693331/1025a0d3-4f0e-40bb-9558-0d638e25817c)


建立测试应用后调用API，将图像服务的APIKey和SecretKey替换app.py中的XXXXXXX部分，语音服务APIKey和SecretKey替换app.py中的YYYYYYY部分。


以下是项目的基本情况：
1. 硬件
树莓派 3B+
树莓派摄像头
OLED 屏幕 (SSD1306)
按钮
3.5mm耳机或扬声器

2. 树莓派系统中需要支持的环境、库、程序
树莓派操作系统（建议使用最新的Raspberry Pi OS）
安装必要的软件和库
更新和升级系统软件包：
sudo apt update

sudo apt upgrade -y

安装 Git：

sudo apt install git -y

安装 Python 3 和 pip：

sudo apt install python3 python3-pip -y

安装必要的 Python 库：

pip3 install flask requests Pillow luma.oled gpiozero pydub simplejson

安装 mpg321 音频播放器：

sudo apt install mpg321 -y

安装 pydub 依赖库：

sudo apt install ffmpeg -y


3. 项目代码、配置文件、文件目录结构
目录结构：

![image](https://github.com/54dashayu/RaspberryPi-Image-Recognition-With-BaiduAI/assets/7693331/9477eeec-863a-4d0b-883c-cf388022f45c)

5. 其他注意事项
a.确保树莓派连接互联网，以便访问百度AI的API服务，本地网页端地址：http://Raspberrypi_IP:5000。
b.确保所有依赖库正确安装并配置。
c.注意设置文件和目录的权限，确保程序可以读写所需文件。
 d.调整 GPU 内存，确保在 /boot/config.txt 文件中分配足够的 GPU 内存。编辑文件：
sudo nano /boot/config.txt
添加或修改以下行：
gpu_mem=256
e.配置音频输出，确保树莓派的音频设置正确，可以通过alsamixer进行调整。

如果遇到问题，查看日志文件/home/用户/app.log获取详细信息。
