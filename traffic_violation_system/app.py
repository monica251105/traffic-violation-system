from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import cv2
import json
import csv
import os
import threading
import time
from datetime import datetime
from pyngrok import ngrok

# Load environment variables from .env (if present)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed; user can install it for .env support
    pass

# Force OpenCV to use TCP for RTSP streams (more stable than UDP)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

# Internal modules from the existing project
from utils.detector import ViolationDetector
from utils.traffic_light import TrafficLightMonitor
from utils.logger import ViolationLogger
from config.settings import Settings
from main import _generate_demo_frame

app = Flask(__name__)
CORS(app, resources={r"/api/*": {
    "origins": "*",
    "allow_headers": ["Content-Type", "ngrok-skip-browser-warning", "Authorization"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
}})

VIOLATIONS_DIR = "violations"
IMAGES_DIR = os.path.join(VIOLATIONS_DIR, "images")
LOG_FILE = os.path.join(VIOLATIONS_DIR, "violations_log.csv")
SUMMARY_FILE = os.path.join(VIOLATIONS_DIR, "summary.json")

# Global variables for the video stream
current_frame = None
lock = threading.Lock()
camera_config = {
    "source": "demo", # can be 'demo', '0', '1', or 'rtsp://...'
    "location_name": "Mode Demo"
}
camera_config_changed = False

# Camera health tracking
camera_status = {
    "connected": False,
    "last_frame_time": 0,
    "frame_count": 0,
    "error": None,
    "source": "demo"
}
status_lock = threading.Lock()

def video_processing_thread():
    global current_frame
    settings = Settings()
    
    # Initialize components
    # Using the trained dataset model specified by the user
    detector = ViolationDetector(model_path=r"runs\detect\models\helmet_model3\weights\last.pt", conf_threshold=0.5)
    traffic_monitor = TrafficLightMonitor(simulate=True) # Set to True for demo/testing
    logger = ViolationLogger(output_dir=settings.VIOLATIONS_DIR)
    
    # Let's use demo mode for the dashboard by default, or 0 for webcam
    # We'll use demo mode so it works reliably without a webcam
    demo_mode = True
    cap = None
    
    if not demo_mode:
        cap = cv2.VideoCapture(0)
        
    frame_count = 0
    
    while True:
        # Check if we need to re-initialize the camera
        global camera_config_changed
        if camera_config_changed:
            if cap:
                cap.release()
            source = camera_config["source"]
            demo_mode = (source == "demo")
            if not demo_mode:
                # Try to parse as integer if it's a digit
                if source.isdigit():
                    cap = cv2.VideoCapture(int(source))
                else:
                    # Use CAP_FFMPEG backend explicitly for RTSP URLs
                    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
            camera_config_changed = False
            frame_count = 0 # Reset frame count on new source
            
            # Update camera status on source change
            with status_lock:
                camera_status["source"] = source
                camera_status["error"] = None
                camera_status["connected"] = demo_mode  # demo is always "connected"
                camera_status["frame_count"] = 0
            
        frame_count += 1
        
        if demo_mode:
            frame = _generate_demo_frame(frame_count, traffic_monitor.is_red())
            time.sleep(0.03) # Simulate roughly 30 FPS
            with status_lock:
                camera_status["connected"] = True
                camera_status["last_frame_time"] = time.time()
                camera_status["frame_count"] = frame_count
                camera_status["error"] = None
        else:
            if cap and cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame is None:
                    with status_lock:
                        camera_status["connected"] = False
                        camera_status["error"] = "No frame received from camera (stream may have dropped)"
                    time.sleep(1)
                    continue
                else:
                    with status_lock:
                        camera_status["connected"] = True
                        camera_status["last_frame_time"] = time.time()
                        camera_status["frame_count"] = frame_count
                        camera_status["error"] = None
            else:
                with status_lock:
                    camera_status["connected"] = False
                    camera_status["error"] = "Camera is not opened or unavailable"
                time.sleep(1)
                continue
                
        traffic_monitor.update()
        is_red_light = traffic_monitor.is_red()
        
        detections = detector.detect(frame)
        violations = detector.analyze_violations(frame, detections, is_red_light)
        
        for violation in violations:
            logger.log_violation(frame, violation)
            
        # Draw basic info for the stream
        display_frame = frame.copy()
        
        # --- Draw Location Name ---
        loc_name = camera_config.get("location_name", "Mode Demo")
        (tw, th), _ = cv2.getTextSize(loc_name, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        h, w = display_frame.shape[:2]
        
        # Pindahkan ke pojok kiri bawah agar tidak menimpa teks bawaan kamera
        pad_x, pad_y = 15, 20
        box_y1 = h - pad_y - th - 10
        box_y2 = h - pad_y + 10
        
        cv2.rectangle(display_frame, (pad_x, box_y1), (pad_x + tw + 20, box_y2), (0, 0, 0), -1)
        cv2.putText(display_frame, loc_name, (pad_x + 10, h - pad_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # We can draw the bounding boxes
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
            # Use 'class_name' key (matches what detector.py returns)
            cv2.putText(display_frame, f"{det['class_name']} {det['confidence']:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            
        if is_red_light:
            cv2.putText(display_frame, "RED LIGHT", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        else:
            cv2.putText(display_frame, "GREEN LIGHT", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
            
        with lock:
            current_frame = display_frame.copy()

# Start the background thread for video processing
thread = threading.Thread(target=video_processing_thread, daemon=True)
thread.start()

def generate_frames():
    global current_frame
    while True:
        with lock:
            if current_frame is None:
                continue
            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', current_frame)
            frame = buffer.tobytes()
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.05) # Yield roughly at 20 FPS

@app.route('/api/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/stats')
def get_stats():
    if os.path.exists(SUMMARY_FILE):
        with open(SUMMARY_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify({"total_violations": 0, "by_type": {"RED_LIGHT": 0, "NO_HELMET": 0}})

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    global camera_config_changed
    if request.method == 'POST':
        data = request.json
        if 'source' in data:
            camera_config["source"] = str(data['source'])
            if 'location_name' in data:
                camera_config["location_name"] = str(data['location_name'])
            camera_config_changed = True
            return jsonify({"status": "success", "message": f"Camera source updated to {camera_config['source']}"})
        return jsonify({"status": "error", "message": "Missing 'source' in request"}), 400
    
    # GET: Kembalikan config saat ini + daftar lokasi yang tersedia
    settings = Settings()
    response_data = dict(camera_config)
    response_data["available_locations"] = settings.LOCATIONS
    return jsonify(response_data)

@app.route('/api/camera_status')
def get_camera_status():
    """Return the current camera health/connection status."""
    with status_lock:
        status = dict(camera_status)
    # Calculate seconds since last frame
    if status["last_frame_time"] > 0:
        status["seconds_since_last_frame"] = round(time.time() - status["last_frame_time"], 1)
    else:
        status["seconds_since_last_frame"] = None
    return jsonify(status)

@app.route('/api/refresh_camera', methods=['POST'])
def refresh_camera():
    """Force the video thread to reconnect to the current camera source."""
    global camera_config_changed
    camera_config_changed = True
    return jsonify({"status": "success", "message": f"Refreshing camera source: {camera_config['source']}"})

@app.route('/api/violations')
def get_violations():
    violations = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                violations.append(row)
    
    # Return the latest violations first
    violations.reverse()
    
    # Optional pagination
    limit = request.args.get('limit', default=50, type=int)
    return jsonify(violations[:limit])

@app.route('/api/images/<filename>')
def get_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

if __name__ == '__main__':
    # Load Ngrok auth token (prefer .env)
    token = os.getenv('NGROK_AUTH_TOKEN')
    if token:
        ngrok.set_auth_token(token)
    else:
        ngrok.set_auth_token("3EdFU1bxz1rmiH67lBQu2eU4Sqw_5X8E2sjBBJcUAqbJMqg2n")
        print("[WARN] NGROK_AUTH_TOKEN tidak ditemukan, menggunakan token default.")

    import subprocess

    def _kill_ngrok_os():
        """Force kill any ngrok.exe processes using Windows taskkill."""
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "ngrok.exe"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

    # Ensure no leftover Ngrok process
    try:
        _kill_ngrok_os()
    except Exception:
        pass

    # Close any previous Ngrok client/tunnels
    try:
        ngrok.kill()
    except Exception:
        pass

    # Disconnect any tunnels still registered on the Ngrok service
    try:
        for t in ngrok.get_tunnels():
            ngrok.disconnect(t.public_url)
    except Exception:
        pass

    # Give Ngrok time to clean up remotely
    time.sleep(2)

    # Create a new tunnel (HTTPS) or reuse an existing one
    tunnels = ngrok.get_tunnels()
    if tunnels:
        public_url = tunnels[0].public_url
        print(f"[INFO] Menggunakan tunnel yang sudah ada: {public_url}")
    else:
        public_url = ngrok.connect(5000, bind_tls=True).public_url
        print(f"🌍 Tautan Publik Ngrok Anda (HTTPS): {public_url}")

    app.run(host='0.0.0.0', port=5000, debug=False)
