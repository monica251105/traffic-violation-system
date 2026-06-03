"""
utils/detector.py
Modul utama deteksi objek menggunakan YOLOv8.
Mendeteksi: kendaraan, helm, pengendara motor, dan status pelanggaran.
"""

import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Label COCO yang relevan untuk sistem ini
VEHICLE_CLASSES    = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
PERSON_CLASS       = 0   # 'person' dalam COCO
HELMET_CLASS_NAMES = {"helmet", "hard hat"}   # jika model custom
NO_HELMET_NAMES    = {"no helmet", "no_helmet"}


class ViolationDetector:
    """
    Kelas utama untuk deteksi pelanggaran lalu lintas.
    Menggunakan YOLOv8 dari ultralytics.
    """

    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.5):
        self.conf_threshold = conf_threshold
        self.model = None
        self.use_yolo = False
        self._load_model(model_path)

        # Zona stop-line (koordinat relatif terhadap frame)
        # Format: (x1, y1, x2, y2) dalam persen ukuran frame
        self.stop_line_y_ratio = 0.55   # Garis stop di 55% tinggi frame

        # Tracking kendaraan yang sudah dicatat (hindari duplikat log)
        self._tracked_violations: Dict[int, float] = {}
        self._violation_cooldown = 3.0   # detik

    # ──────────────────────────────────────────────────────────
    def _load_model(self, model_path: str):
        """Muat model YOLO. Fallback ke OpenCV DNN jika gagal."""
        try:
            from ultralytics import YOLO
            print(f"[Detector] Memuat model: {model_path}")
            self.model = YOLO(model_path)
            self.use_yolo = True
            print("[Detector] ✓ Model YOLOv8 berhasil dimuat!")
        except ImportError:
            print("[Detector] ⚠ ultralytics tidak terinstal.")
            print("[Detector]   Menggunakan OpenCV DNN sebagai fallback...")
            self._init_opencv_dnn()
        except Exception as e:
            print(f"[Detector] ⚠ Gagal memuat YOLO: {e}")
            print("[Detector]   Menggunakan mode simulasi...")
            self.use_yolo = False

    def _init_opencv_dnn(self):
        """Inisialisasi OpenCV DNN sebagai fallback detector."""
        import os
        cfg_path    = "models/yolov3.cfg"
        weight_path = "models/yolov3.weights"
        names_path  = "models/coco.names"

        if os.path.exists(cfg_path) and os.path.exists(weight_path):
            self.dnn_net = cv2.dnn.readNetFromDarknet(cfg_path, weight_path)
            self.dnn_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.dnn_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            if os.path.exists(names_path):
                with open(names_path) as f:
                    self.dnn_classes = f.read().strip().split("\n")
            self.use_opencv_dnn = True
            print("[Detector] ✓ OpenCV DNN berhasil diinisialisasi!")
        else:
            print("[Detector] ⚠ File model OpenCV DNN tidak ditemukan.")
            print("[Detector]   Aktifkan mode simulasi untuk demo.")
            self.use_opencv_dnn = False

    # ──────────────────────────────────────────────────────────
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Jalankan deteksi objek pada frame.
        
        Returns:
            List of detections, masing-masing berisi:
            {class_id, class_name, confidence, bbox: (x1,y1,x2,y2)}
        """
        if self.use_yolo and self.model is not None:
            return self._detect_yolo(frame)
        elif hasattr(self, "use_opencv_dnn") and self.use_opencv_dnn:
            return self._detect_opencv_dnn(frame)
        else:
            return self._simulate_detections(frame)

    def _detect_yolo(self, frame: np.ndarray) -> List[Dict]:
        """Deteksi menggunakan YOLOv8."""
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        detections = []
        
        for r in results:
            for box in r.boxes:
                cls_id   = int(box.cls[0])
                cls_name = self.model.names[cls_id]
                conf     = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                detections.append({
                    "class_id"  : cls_id,
                    "class_name": cls_name,
                    "confidence": conf,
                    "bbox"      : (x1, y1, x2, y2),
                    "track_id"  : int(box.id[0]) if box.id is not None else -1
                })
        
        return detections

    def _detect_opencv_dnn(self, frame: np.ndarray) -> List[Dict]:
        """Deteksi menggunakan OpenCV DNN (YOLOv3)."""
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416),
                                     swapRB=True, crop=False)
        self.dnn_net.setInput(blob)
        
        layer_names  = self.dnn_net.getLayerNames()
        output_names = [layer_names[i - 1]
                        for i in self.dnn_net.getUnconnectedOutLayers()]
        outputs = self.dnn_net.forward(output_names)
        
        detections = []
        for output in outputs:
            for det in output:
                scores    = det[5:]
                cls_id    = int(np.argmax(scores))
                conf      = float(scores[cls_id])
                if conf < self.conf_threshold:
                    continue
                cx, cy, bw, bh = det[:4] * np.array([w, h, w, h])
                x1 = int(cx - bw / 2)
                y1 = int(cy - bh / 2)
                x2 = int(cx + bw / 2)
                y2 = int(cy + bh / 2)
                cls_name = (self.dnn_classes[cls_id]
                            if cls_id < len(self.dnn_classes) else str(cls_id))
                detections.append({
                    "class_id"  : cls_id,
                    "class_name": cls_name,
                    "confidence": conf,
                    "bbox"      : (x1, y1, x2, y2),
                    "track_id"  : -1
                })
        return detections

    def _simulate_detections(self, frame: np.ndarray) -> List[Dict]:
        """Simulasi deteksi untuk demo/testing tanpa model."""
        import math, time
        t     = time.time()
        h, w  = frame.shape[:2]
        dets  = []

        # Simulasi motor bergerak
        x = int((math.sin(t * 0.5) * 0.3 + 0.5) * (w - 200))
        y = int(h * 0.45)
        dets.append({
            "class_id"  : 3, "class_name": "motorcycle",
            "confidence": 0.85,
            "bbox"      : (x, y, x + 120, y + 80),
            "track_id"  : 1
        })
        # Simulasi pengendara
        dets.append({
            "class_id"  : 0, "class_name": "person",
            "confidence": 0.78,
            "bbox"      : (x + 20, y - 50, x + 100, y + 10),
            "track_id"  : 2
        })
        return dets

    # ──────────────────────────────────────────────────────────
    def analyze_violations(
        self,
        frame      : np.ndarray,
        detections : List[Dict],
        is_red     : bool
    ) -> List[Dict]:
        """
        Analisis deteksi untuk menemukan pelanggaran.
        
        Pelanggaran yang dicek:
        1. Kendaraan melewati garis stop saat lampu MERAH
        2. Pengendara motor tanpa helm
        """
        from config.settings import Settings
        
        h, w       = frame.shape[:2]
        stop_x = int(w * getattr(Settings, "STOP_LINE_X_RATIO", 0.5))
        start_y = int(h * getattr(Settings, "STOP_LINE_START_Y", 1.0))
        end_y = int(h * getattr(Settings, "STOP_LINE_END_Y", 0.5))
        
        # Pastikan start_y > end_y untuk logika rentang Y yang benar (karena 0 adalah atas frame)
        min_y = min(start_y, end_y)
        max_y = max(start_y, end_y)
        
        violations  = []
        now         = datetime.now()

        # Pisahkan deteksi berdasarkan nama kelas (menghindari bentrok ID dengan model custom)
        vehicles = []
        persons = []
        helmets = []
        no_helmets = []
        
        for d in detections:
            c_name = d["class_name"].lower()
            if c_name in {"car", "motorcycle", "bus", "truck", "bicycle"}:
                vehicles.append(d)
            elif c_name == "person":
                persons.append(d)
            elif any(h_name in c_name for h_name in HELMET_CLASS_NAMES):
                helmets.append(d)
            elif any(n in c_name for n in NO_HELMET_NAMES) or c_name == "without helmet":
                no_helmets.append(d)

        # ── 1. Cek pelanggaran lampu merah ──────────────────
        if is_red:
            for v in vehicles:
                x1, y1, x2, y2 = v["bbox"]
                vehicle_bottom  = y2
                
                # Kendaraan melewati garis stop vertikal (berada di kiri/kanan garis)
                # Syarat 1: X kendaraan melewati garis stop (x1 <= stop_x <= x2)
                # Syarat 2: Y kendaraan berada di rentang garis tersebut
                crosses_x = (x1 <= stop_x <= x2)
                in_y_range = (y2 > min_y) and (y1 < max_y)
                
                if crosses_x and in_y_range:
                    v_id = v.get("track_id", hash((x1, y1)))
                    if self._can_log_violation(v_id):
                        violations.append({
                            "type"      : "RED_LIGHT",
                            "confidence": v["confidence"],
                            "bbox"      : v["bbox"],
                            "vehicle"   : v["class_name"],
                            "timestamp" : now,
                            "message"   : f"Kendaraan ({v['class_name']}) melanggar lampu MERAH!",
                            "color"     : (0, 0, 255)
                        })
                        self._track_violation(v_id)

        # ── 2. Cek pelanggaran helm ──────────────────────────
        motorcycles = [v for v in vehicles
                       if "motorcycle" in v["class_name"].lower() or
                          "bike" in v["class_name"].lower()]
        
        for moto in motorcycles:
            mx1, my1, mx2, my2 = moto["bbox"]
            
            # Cari pengendara yang berada di atas motor
            rider = self._find_rider(persons, mx1, my1, mx2, my2)
            
            if rider:
                # Cek apakah ada helm di area kepala pengendara
                has_helmet = self._check_helmet(
                    rider, helmets, [], frame.shape
                )
                
                if not has_helmet:
                    r_id = rider.get("track_id", hash(rider["bbox"]))
                    if self._can_log_violation(r_id + 1000):
                        violations.append({
                            "type"      : "NO_HELMET",
                            "confidence": rider["confidence"],
                            "bbox"      : rider["bbox"],
                            "vehicle"   : "motorcycle",
                            "timestamp" : now,
                            "message"   : "Pengendara motor TIDAK memakai helm!",
                            "color"     : (0, 165, 255)
                        })
                        self._track_violation(r_id + 1000)

        return violations

    def _find_rider(self, persons, mx1, my1, mx2, my2) -> Optional[Dict]:
        """Cari orang yang berada di atas/dalam area motor."""
        for person in persons:
            px1, py1, px2, py2 = person["bbox"]
            # Pengendara biasanya overlap dengan motor dan berada di atasnya
            overlap_x = max(0, min(px2, mx2) - max(px1, mx1))
            person_w  = px2 - px1
            if overlap_x > person_w * 0.3 and py2 > my1 and py1 < my2:
                return person
        return None

    def _check_helmet(self, rider, helmets, no_helmets, shape) -> bool:
        """
        Periksa apakah pengendara memakai helm.
        Strategi: cek area kepala (1/4 atas bounding box pengendara).
        """
        # Jika model punya kelas 'no_helmet' eksplisit
        if no_helmets:
            rx1, ry1, rx2, ry2 = rider["bbox"]
            head_y2 = ry1 + (ry2 - ry1) // 3
            for nh in no_helmets:
                nx1, ny1, nx2, ny2 = nh["bbox"]
                # Overlap dengan area kepala
                if ny1 < head_y2 and nx1 < rx2 and nx2 > rx1:
                    return False
            return True
        
        if helmets:
            rx1, ry1, rx2, ry2 = rider["bbox"]
            head_y2 = ry1 + (ry2 - ry1) // 3
            for h in helmets:
                hx1, hy1, hx2, hy2 = h["bbox"]
                if hy1 < head_y2 and hx1 < rx2 and hx2 > rx1:
                    return True
            # Ada model helm tapi tidak ada di kepala pengendara
            return False
        
        # Fallback: estimasi berdasarkan warna/bentuk kepala (heuristik sederhana)
        return self._heuristic_helmet_check(rider, shape)

    def _heuristic_helmet_check(self, rider: Dict, shape: tuple) -> bool:
        """
        Heuristik sederhana jika tidak ada kelas helm.
        Menganggap tidak ada helm untuk demo (lebih konservatif).
        Implementasikan logika custom di sini.
        """
        # Dalam sistem produksi: gunakan model helm khusus
        # Untuk demo: asumsikan tidak ada helm (trigger alert)
        return False

    def _can_log_violation(self, track_id: int) -> bool:
        import time
        last = self._tracked_violations.get(track_id, 0)
        return (time.time() - last) > self._violation_cooldown

    def _track_violation(self, track_id: int):
        import time
        self._tracked_violations[track_id] = time.time()
