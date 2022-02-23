import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, flash, jsonify
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import json
import requests
import tempfile, shutil, os
from PIL import Image
from io import BytesIO

from linebot.models import (
    TemplateSendMessage, AudioSendMessage,
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, PostbackEvent, StickerMessage, StickerSendMessage, 
    LocationMessage, LocationSendMessage, ImageMessage, ImageSendMessage
)
from linebot.models.template import *
from linebot import (
    LineBotApi, WebhookHandler
)

app = Flask(__name__, static_url_path="/static")

UPLOAD_FOLDER ='static/uploads/'
DOWNLOAD_FOLDER = 'static/downloads/'
ALLOWED_EXTENSIONS = {'jpg', 'png','.jpeg'}

lineaccesstoken = 'ulJgFHtnnrJza3wgi37wN7/LjSC1rB8ExvliVO+up7isUuSOfZLsH7P87+PNaPXT1coYmcUIz9zbUCTfwJ6vglMejyyiyR+YLnEXETwhX+MyJ8teZFzr7O20XrFKoGyXHbs2lZFwtBNCaJEgjoExXQdB04t89/1O/w1cDnyilFU='

line_bot_api = LineBotApi(lineaccesstoken)

# APP CONFIGURATIONS
app.config['SECRET_KEY'] = 'opencv'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
# limit upload size upto 6mb
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file attached in request')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            process_file(os.path.join(UPLOAD_FOLDER, filename), filename)
            data={
                "processed_img":'static/downloads/'+filename,
                "uploaded_img":'static/uploads/'+filename
            }
            return render_template("index.html",data=data)  
    return render_template('index.html')


def process_file(path, filename):
    detect_object(path, filename)
    
def detect_object(path, filename):    
    CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
        "sofa", "train", "tvmonitor"]
    COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))
    prototxt="ssd/MobileNetSSD_deploy.prototxt.txt"
    model ="ssd/MobileNetSSD_deploy.caffemodel"
    net = cv2.dnn.readNetFromCaffe(prototxt, model)
    image = cv2.imread(path)
    image = cv2.resize(image,(480,360))
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()
    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.60:
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # display the prediction
            label = "{}: {:.2f}%".format(CLASSES[idx], confidence * 100)
            # print("[INFO] {}".format(label))
            cv2.rectangle(image, (startX, startY), (endX, endY),
                COLORS[idx], 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            cv2.putText(image, label, (startX, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)

    cv2.imwrite(f"{DOWNLOAD_FOLDER}{filename}",image)

@app.route('/callback', methods=['POST'])
def callback():
    json_line = request.get_json(force=False,cache=False)
    json_line = json.dumps(json_line)
    decoded = json.loads(json_line)
    
    # เชื่อมต่อกับ line 
    no_event = len(decoded['events'])
    for i in range(no_event):
            event = decoded['events'][i]
            event_handle(event,json_line)

    # เชื่อมต่อกับ dialogflow
    #intent = decoded["queryResult"]["intent"]["displayName"] 
    #text = decoded['originalDetectIntentRequest']['payload']['data']['message']['text'] 
    #reply_token = decoded['originalDetectIntentRequest']['payload']['data']['replyToken']
    #id = decoded['originalDetectIntentRequest']['payload']['data']['source']['userId']
    #disname = line_bot_api.get_profile(id).display_name
    #reply(intent,text,reply_token,id,disname)

    return '',200

def reply(intent,text,reply_token,id,disname):
    text_message = TextSendMessage(text="ทดสอบ")
    line_bot_api.reply_message(reply_token,text_message)

def event_handle(event,json_line):
    print(event)
    try:
        userId = event['source']['userId']
    except:
        print('error cannot get userId')
        return ''

    try:
        rtoken = event['replyToken']
    except:
        print('error cannot get rtoken')
        return ''
    try:
        msgId = event["message"]["id"]
        msgType = event["message"]["type"]
    except:
        print('error cannot get msgID, and msgType')
        sk_id = np.random.randint(1,17)
        replyObj = StickerSendMessage(package_id=str(1),sticker_id=str(sk_id))
        line_bot_api.reply_message(rtoken, replyObj)
        return ''

    if msgType == "text":
        msg = str(event["message"]["text"])
        if msg == "น้ำลำไย":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "น้ำใบเตย":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "น้ำเก๊กฮวย":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "น้ำอัญชัน":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "น้ำอัดลม":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)    
        elif msg == "น้ำเปล่า":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)            
        elif msg == "ชากุหลาบ":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)     
        elif msg == "ชามะนาว":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)     
        elif msg == "ชามะนาว":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj) 
        elif msg == "ชาไทย":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "ชาเขียว":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj) 
        elif msg == "ส้มตำปูปลาร้า":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)    
         elif msg == "หมูฮ้อง":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)    
        elif msg == "คอหมูย่าง":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)            
        elif msg == "แกงปู":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)     
        elif msg == "แกงคั่วหอยขม":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)     
        elif msg == "พะโล้โบราณ":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj) 
        elif msg == "หมูผัดพริกแกง":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "ปลาทอดเครื่อง":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj) 
        elif msg == "แกงเขียวหวานไก่":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "ผัดไทยกุ้งสด":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "ข้าวมันไก่ต้ม":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "ข้าวมันไก่ทอด":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "ข้าวขาหมู":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)    
        elif msg == "ข้าวหมูกรอบ":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)            
        elif msg == "ข้าวผัด":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)     
        elif msg == "ข้าวไข่เจียว":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)     
        elif msg == "กะเพรา":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj) 
        elif msg == "ผัดซีอิ๊ว":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)
        elif msg == "ต้มจืด":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj) 
        elif msg == "ไก่ทอดกระเทียม":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)    
         elif msg == "หมูทอดกระเทียม":
            replyObj = TextSendMessage(text="ข้าวหอมรับออเดอร์ค่ะ")
            line_bot_api.reply_message(rtoken, replyObj)    
        elif msg == "covid" :
            url = "https://covid19.ddc.moph.go.th/api/Cases/today-cases-all"
            response = requests.get(url)
            response = response.json()
            replyObj = TextSendMessage(text=str(response))
            line_bot_api.reply_message(rtoken, replyObj)
        else :
            headers = request.headers
            json_headers = ({k:v for k, v in headers.items()})
            json_headers.update({'Host':'bots.dialogflow.com'})
            url = "https://bots.dialogflow.com/line/5a8df0d9-f1fb-4bd6-a501-41540bcb9f4d/webhook"
            requests.post(url,data=json_line, headers=json_headers)
    elif msgType == "image":
        try:
            message_content = line_bot_api.get_message_content(event['message']['id'])
            i = Image.open(BytesIO(message_content.content))
            filename = event['message']['id'] + '.jpg'
            i.save(UPLOAD_FOLDER + filename)
            process_file(os.path.join(UPLOAD_FOLDER, filename), filename)

            url = request.url_root + DOWNLOAD_FOLDER + filename
            
            line_bot_api.reply_message(
                rtoken, [
                    TextSendMessage(text='Object detection result:'),
                    ImageSendMessage(url,url)
                ])    
    
        except:
            message = TextSendMessage(text="เกิดข้อผิดพลาด กรุณาส่งใหม่อีกครั้ง")
            line_bot_api.reply_message(event.reply_token, message)

            return 0

    else:
        sk_id = np.random.randint(1,17)
        replyObj = StickerSendMessage(package_id=str(1),sticker_id=str(sk_id))
        line_bot_api.reply_message(rtoken, replyObj)
    return ''

if __name__ == '__main__':
    app.run()
