from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from ultralytics import YOLO
from firebase_config import firebase_manager, save_detection, get_recent_detections, get_stats

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Load YOLO model
MODEL_PATH = 'best.pt'  # หรือ 'models/best.pt' ถ้าอยู่ในโฟลเดอร์ models
try:
    yolo_model = YOLO(MODEL_PATH)
    print(f"✅ YOLO model loaded: {MODEL_PATH}")
except Exception as e:
    print(f"❌ Failed to load YOLO model: {e}")
    yolo_model = None

# เพิ่ม CORS headers manually
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# สร้างโฟลเดอร์ uploads ถ้ายังไม่มี
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# ตั้งค่า API
API_URL = "https://api.aiforthai.in.th/lpr-iapp"
API_KEY = "GgY2UsQsZRrZxeWKSilQ8uKZGAFLiagW"

# Mock API สำหรับการทดสอบ (เปลี่ยนเป็น True เพื่อใช้ mock)
USE_MOCK_API = False  # เปลี่ยนเป็น False เพื่อใช้ API จริง
MOCK_API_URL = "http://127.0.0.1:5001/mock-lpr"

def allowed_file(filename):
    """ตรวจสอบไฟล์ที่อนุญาต"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def detect_license_plate_yolo(image_path, confidence_threshold=0.7):
    """ตรวจจับป้ายทะเบียนด้วย YOLO model"""
    if yolo_model is None:
        return None
    
    try:
        # อ่านภาพ
        image = cv2.imread(image_path)
        if image is None:
            return None
            
        # Run YOLO detection
        results = yolo_model(image)
        
        # Extract detections
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get confidence score
                    conf = float(box.conf[0])
                    
                    # Filter by confidence threshold
                    if conf >= confidence_threshold:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        detection = {
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'confidence': conf,
                            'class': int(box.cls[0]),
                            'width': int(x2 - x1),
                            'height': int(y2 - y1)
                        }
                        detections.append(detection)
        
        print(f"🎯 YOLO detected {len(detections)} license plates with conf > {confidence_threshold}")
        return detections
        
    except Exception as e:
        print(f"❌ YOLO detection error: {e}")
        return None

def crop_license_plate(image_path, bbox):
    """ครอบตัดภาพป้ายทะเบียนตาม bounding box"""
    try:
        image = cv2.imread(image_path)
        x1, y1, x2, y2 = bbox
        
        # Add padding
        padding = 10
        h, w = image.shape[:2]
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        # Crop image
        cropped = image[y1:y2, x1:x2]
        
        # Save cropped image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        cropped_filename = f"cropped_{timestamp}.jpg"
        cropped_path = os.path.join(app.config['UPLOAD_FOLDER'], cropped_filename)
        cv2.imwrite(cropped_path, cropped)
        
        return cropped_path
        
    except Exception as e:
        print(f"❌ Crop error: {e}")
        return None

def send_to_lpr_api(image_path):
    """ส่งภาพไปยัง API AIforThai LPR เพื่ออ่านป้ายทะเบียน"""
    
    # ใช้ Mock API สำหรับการทดสอบ
    if USE_MOCK_API:
        import random
        import time
        
        print(f"🎭 Using Mock API: {MOCK_API_URL}")
        
        # จำลองการประมวลผล
        time.sleep(random.uniform(0.2, 0.8))
        
        # 70% chance ตรวจพบป้าย
        if random.random() < 0.7:
            mock_plates = ["กข 1234", "1กก 2345", "ตณ 3754", "2กร 5678", "บจ 9876"]
            plate = random.choice(mock_plates)
            confidence = random.uniform(80, 95)
            
            return {
                'success': True,
                'license_plate': plate,
                'confidence': confidence / 100.0,
                'mock': True,
                'raw_response': {'lp_number': plate, 'conf': confidence}
            }
        else:
            return {
                'success': False,
                'license_plate': '',
                'confidence': 0,
                'error': 'ไม่พบป้ายทะเบียนในภาพ (Mock)',
                'mock': True
            }
    
    # ใช้ API จริง
    try:
        payload = {}
        
        with open(image_path, 'rb') as img_file:
            files = [('file', ('image.jpg', img_file, 'image/jpeg'))]
            headers = {'apikey': API_KEY}
            
            response = requests.post(API_URL, headers=headers, data=payload, files=files, timeout=20)
        
        print(f"API Response Status: {response.status_code}")
        print(f"API Response: {response.text}")
        
        if response.status_code == 200:
            api_result = response.json()
            
            # ตรวจสอบโครงสร้าง response ใหม่
            if api_result.get('status') == 200 and api_result.get('lp_number'):
                # API ใหม่ส่ง lp_number แทน LPR array
                return {
                    'success': True,
                    'license_plate': api_result.get('lp_number', ''),
                    'confidence': api_result.get('conf', 0) / 100.0,  # Convert percentage to decimal
                    'raw_response': api_result
                }
            elif 'LPR' in api_result and len(api_result['LPR']) > 0:
                # Old API format fallback
                lpr_data = api_result['LPR'][0]
                return {
                    'success': True,
                    'license_plate': lpr_data.get('plate', ''),
                    'confidence': lpr_data.get('confidence', 0),
                    'raw_response': api_result
                }
            else:
                return {
                    'success': False,
                    'license_plate': '',
                    'confidence': 0,
                    'error': 'ไม่พบป้ายทะเบียนในภาพ',
                    'raw_response': api_result
                }
        elif response.status_code == 401:
            return {
                'success': False,
                'error': 'API Key ไม่ถูกต้องหรือหมดอายุ - กรุณาติดต่อผู้ดูแลระบบ',
                'message': response.text
            }
        elif response.status_code == 429:
            return {
                'success': False,
                'error': 'API Rate Limit - เรียกใช้บ่อยเกินไป กรุณารอสักครู่',
                'message': response.text
            }
        else:
            return {
                'success': False,
                'error': f'API Error: {response.status_code}',
                'message': response.text
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'API Timeout - เชื่อมต่อเซิร์ฟเวอร์ช้าเกินไป'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Connection Error - ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error calling LPR API: {str(e)}'
        }

@app.route('/')
def index():
    """หน้าแรก"""
    return render_template('index.html')

@app.route('/webcam')
def webcam():
    """หน้า Webcam Detection"""
    return render_template('webcam.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """อัปโหลดและประมวลผลไฟล์"""
    if 'file' not in request.files:
        return jsonify({'error': 'ไม่มีไฟล์ถูกเลือก'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'ไม่มีไฟล์ถูกเลือก'})
    
    if file and allowed_file(file.filename):
        # บันทึกไฟล์
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # ส่งไปยัง API
        result = send_to_lpr_api(filepath)
        
        # เพิ่มข้อมูลไฟล์ลงใน result
        result['uploaded_file'] = filename
        result['upload_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify(result)
    else:
        return jsonify({'error': 'ไฟล์ไม่ถูกต้อง รองรับเฉพาะ PNG, JPG, JPEG, GIF, BMP'})

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """API สำหรับการตรวจจับจาก webcam"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'ไม่มีไฟล์ถูกส่งมา'})
    
    file = request.files['file']
    confidence = request.form.get('confidence', '0.25')
    source = request.form.get('source', 'unknown')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'ไม่มีไฟล์ถูกเลือก'})
    
    try:
        # สร้างชื่อไฟล์ชั่วคราว
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # รวม milliseconds
        temp_filename = f"webcam_{timestamp}.jpg"
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        
        # บันทึกไฟล์ชั่วคราว
        file.save(temp_filepath)
        
        print(f"📁 Saved temp file: {temp_filepath}")
        
        # ส่งไปยัง API
        result = send_to_lpr_api(temp_filepath)
        
        # เพิ่มข้อมูลเพิ่มเติม
        result['source'] = source
        result['confidence_threshold'] = float(confidence)
        result['capture_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result['temp_file'] = temp_filename
        
        # บันทึกลง Firebase (ถ้าตรวจพบป้ายทะเบียน)
        if result.get('success') and result.get('license_plate'):
            try:
                firebase_doc_id = firebase_manager.save_detection_result(
                    license_plate=result['license_plate'],
                    confidence_api=result.get('confidence', 0),
                    detection_mode="manual",
                    api_response=result  # ส่ง API response ทั้งหมดสำหรับการแยกจังหวัด
                )
                if firebase_doc_id:
                    result['firebase_doc_id'] = firebase_doc_id
                    print(f"✅ Saved to Firebase: {firebase_doc_id}")
            except Exception as firebase_error:
                print(f"⚠️ Firebase save failed: {firebase_error}")
                # ไม่ให้ Firebase error ทำให้ API fail
        
        print(f"📡 API Result: {result}")
        
        # ลบไฟล์ชั่วคราวหลังจากส่ง API (เก็บไว้ถ้า debug)
        # os.remove(temp_filepath)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in api_detect: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/detect-yolo', methods=['POST'])
def api_detect_yolo():
    """API สำหรับการตรวจจับด้วย YOLO + AIforThai API"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'ไม่มีไฟล์ถูกส่งมา'})
    
    file = request.files['file']
    confidence = float(request.form.get('confidence', '0.7'))
    source = request.form.get('source', 'unknown')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'ไม่มีไฟล์ถูกเลือก'})
    
    try:
        # สร้างชื่อไฟล์ชั่วคราว
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        temp_filename = f"webcam_yolo_{timestamp}.jpg"
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        
        # บันทึกไฟล์ชั่วคราว
        file.save(temp_filepath)
        print(f"📁 Saved temp file: {temp_filepath}")
        
        # Step 1: YOLO Detection
        detections = detect_license_plate_yolo(temp_filepath, confidence)
        
        if not detections:
            return jsonify({
                'success': False,
                'license_plate': '',
                'confidence': 0,
                'error': f'ไม่พบป้ายทะเบียนด้วย YOLO (confidence < {confidence})',
                'yolo_detections': [],
                'source': source,
                'confidence_threshold': confidence,
                'capture_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'temp_file': temp_filename
            })
        
        # Step 2: ใช้ detection ที่มี confidence สูงสุด
        best_detection = max(detections, key=lambda x: x['confidence'])
        print(f"🎯 Best YOLO detection: confidence={best_detection['confidence']:.3f}")
        
        # Step 3: Crop license plate
        cropped_path = crop_license_plate(temp_filepath, best_detection['bbox'])
        if not cropped_path:
            return jsonify({
                'success': False,
                'error': 'ไม่สามารถครอบตัดภาพป้ายทะเบียนได้',
                'yolo_detections': detections,
                'source': source,
                'confidence_threshold': confidence,
                'capture_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'temp_file': temp_filename
            })
        
        # Step 4: ส่งภาพที่ครอบตัดไปยัง AIforThai API
        api_result = send_to_lpr_api(cropped_path)
        
        # Step 5: รวมผลลัพธ์
        result = {
            'success': api_result.get('success', False),
            'license_plate': api_result.get('license_plate', ''),
            'confidence': api_result.get('confidence', 0),
            'yolo_detections': detections,
            'yolo_confidence': best_detection['confidence'],
            'bbox': best_detection['bbox'],
            'api_result': api_result,
            'source': source,
            'confidence_threshold': confidence,
            'capture_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'temp_file': temp_filename,
            'cropped_file': os.path.basename(cropped_path)
        }
        
        # บันทึกลง Firebase (ถ้าตรวจพบป้ายทะเบียน)
        if result.get('success') and result.get('license_plate'):
            try:
                firebase_doc_id = firebase_manager.save_detection_result(
                    license_plate=result['license_plate'],
                    confidence_api=result.get('confidence', 0),
                    confidence_yolo=result.get('yolo_confidence', 0),
                    detection_mode="auto",  # YOLO+API = Auto mode
                    api_response=api_result  # ส่ง API response สำหรับการแยกจังหวัด
                )
                if firebase_doc_id:
                    result['firebase_doc_id'] = firebase_doc_id
                    print(f"✅ Saved to Firebase: {firebase_doc_id}")
            except Exception as firebase_error:
                print(f"⚠️ Firebase save failed: {firebase_error}")
                # ไม่ให้ Firebase error ทำให้ API fail
        
        print(f"📡 YOLO+API Result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in api_detect_yolo: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/history')
def history():
    """หน้าประวัติการอัปโหลด"""
    # อ่านไฟล์ในโฟลเดอร์ uploads
    files = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_file(filename):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                stat = os.stat(filepath)
                files.append({
                    'filename': filename,
                    'size': f"{stat.st_size / 1024:.1f} KB",
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
    
    files.sort(key=lambda x: x['modified'], reverse=True)
    return render_template('history.html', files=files)

@app.route('/api/info')
def api_info():
    """ข้อมูล API"""
    return jsonify({
        'api_url': API_URL,
        'status': 'active',
        'supported_formats': ['PNG', 'JPG', 'JPEG', 'GIF', 'BMP'],
        'max_file_size': '16MB',
        'firebase_connected': firebase_manager.is_connected()
    })

@app.route('/api/firebase/stats')
def firebase_stats():
    """ข้อมูลสถิติจาก Firebase"""
    try:
        stats = get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/firebase/recent')
def firebase_recent():
    """ข้อมูลการตรวจจับล่าสุดจาก Firebase"""
    try:
        limit = int(request.args.get('limit', 20))
        recent = firebase_manager.get_recent_detections(limit)
        
        # แปลง timestamp เป็น string ถ้าจำเป็น
        for item in recent:
            if 'timestamp' in item and item['timestamp']:
                # ตรวจสอบว่า timestamp เป็น string หรือ datetime object
                if hasattr(item['timestamp'], 'strftime'):
                    item['timestamp'] = item['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                # ถ้าเป็น string แล้วก็ใช้ต่อไป
        
        return jsonify({
            'success': True,
            'detections': recent,
            'count': len(recent)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/firebase/search')
def firebase_search():
    """ค้นหาข้อมูลใน Firebase"""
    try:
        license_plate = request.args.get('license_plate')
        
        if not license_plate:
            return jsonify({
                'success': False,
                'error': 'กรุณาระบุหมายเลขป้ายทะเบียน'
            })
        
        results = firebase_manager.search_detections(license_plate=license_plate)
        
        # แปลง timestamp เป็น string
        for item in results:
            if 'timestamp' in item and item['timestamp']:
                item['timestamp'] = item['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'search_term': license_plate
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/province-stats', methods=['GET'])
def get_province_stats():
    """ดึงสถิติการตรวจจับตามจังหวัดและภาค"""
    try:
        stats = firebase_manager.get_province_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/dashboard')
def dashboard():
    """หน้า Dashboard สำหรับดูข้อมูล Firebase"""
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
