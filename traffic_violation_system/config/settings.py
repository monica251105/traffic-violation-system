"""
config/settings.py
Konfigurasi global sistem deteksi pelanggaran lalu lintas.
"""


class Settings:
    # ── Model ────────────────────────────────────────────────
    DEFAULT_MODEL       = "yolov8n.pt"    # Nano (tercepat)
    # Pilihan model (semakin besar = lebih akurat, lebih lambat):
    # yolov8n.pt | yolov8s.pt | yolov8m.pt | yolov8l.pt | yolov8x.pt
    
    CONFIDENCE_THRESHOLD = 0.5
    IOU_THRESHOLD        = 0.45

    # ── Pilihan Lokasi Terdefinisi ────────────────────────────
    LOCATIONS = {
        "TRANSMART": {
            "name": "Perempatan Transmart Manado",
            "source": "rtsp://perempatan:12345678@10.96.98.226:554/stream2"
        },
        "PAAL_2": {
            "name": "Perempatan Paal 2 Manado",
            "source": "rtsp://perempatan:12345678@10.96.98.226:554/stream2"
        }
    }

    # ── Video ────────────────────────────────────────────────
    FRAME_WIDTH         = 1280
    FRAME_HEIGHT        = 720
    TARGET_FPS          = 30

    # ── Nama kelas heml ─────────────────────────────────────────
    HELMET_CLASSES = {"with helmet"}
    NO_HELMET_CLASSES = {"without helmet"}
    
    # ── Zona deteksi ─────────────────────────────────────────
    # Posisi horizontal garis stop (rasio dari lebar frame, 0.0 = kiri, 1.0 = kanan)
    STOP_LINE_X_RATIO   = 0.40  # Silakan ubah jika posisi garis kurang ke kiri/kanan
    # Batas vertikal garis stop (rasio dari tinggi frame, 1.0 = bawah, 0.0 = atas)
    STOP_LINE_START_Y   = 1.0  # Mulai dari paling bawah layar (100%)
    STOP_LINE_END_Y     = 0.5  # Membentang sampai ke tengah layar (50%)

    # ROI lampu lalu lintas untuk deteksi warna (x1%, y1%, x2%, y2%)
    # Sesuaikan dengan posisi lampu di kamera Anda
    TRAFFIC_LIGHT_ROI   = (0.45, 0.05, 0.55, 0.35)

    # ── Output ───────────────────────────────────────────────
    VIOLATIONS_DIR      = "violations"
    LOG_FILE            = "violations/violations_log.csv"
    SUMMARY_FILE        = "violations/summary.json"

    # ── Alert ────────────────────────────────────────────────
    ALERT_DURATION      = 3.0     # detik
    FLASH_INTERVAL      = 0.25    # detik
    VIOLATION_COOLDOWN  = 3.0     # jeda antar log untuk objek yang sama

    # ── Tampilan ─────────────────────────────────────────────
    SHOW_FPS            = True
    SHOW_BOUNDING_BOXES = True
    SHOW_CONFIDENCE     = True
    SIDE_PANEL_WIDTH    = 300
