# 🚦 Sistem Deteksi Pelanggaran Lalu Lintas
**Traffic Violation Detection System berbasis Machine Learning**

---

## 📋 Daftar Isi
1. [Gambaran Sistem](#gambaran-sistem)
2. [Persyaratan Sistem](#persyaratan-sistem)
3. [Instalasi Lengkap](#instalasi-lengkap)
4. [Cara Menjalankan Program](#cara-menjalankan-program)
5. [Cara Kerja Sistem](#cara-kerja-sistem)
6. [Konfigurasi Lanjutan](#konfigurasi-lanjutan)
7. [Output & Log](#output--log)
8. [Troubleshooting](#troubleshooting)

---

## Gambaran Sistem

```
┌─────────────────────────────────────────────────────────┐
│           ARSITEKTUR SISTEM                             │
│                                                         │
│  [Kamera/CCTV/Video]                                    │
│         │                                               │
│         ▼                                               │
│  [OpenCV - Baca Frame]                                  │
│         │                                               │
│         ▼                                               │
│  [YOLOv8 - Deteksi Objek]                              │
│    ├── Kendaraan (motor, mobil, bus, truk)              │
│    ├── Orang (pengendara)                               │
│    └── Helm / No-Helmet                                 │
│         │                                               │
│         ▼                                               │
│  [Analisis Pelanggaran]                                 │
│    ├── Lampu Merah → Kendaraan melewati garis stop?    │
│    └── Motor → Pengendara pakai helm?                   │
│         │                                               │
│         ▼                                               │
│  [Logger] → Simpan foto bukti + CSV log                │
│         │                                               │
│         ▼                                               │
│  [Display HUD] → Tampilkan di layar secara real-time   │
└─────────────────────────────────────────────────────────┘
```

---

## Persyaratan Sistem

| Komponen | Minimum | Rekomendasi |
|----------|---------|-------------|
| OS | Windows 10 / Ubuntu 20.04 / macOS 11 | Windows 11 / Ubuntu 22.04 |
| Python | 3.8+ | 3.10+ |
| RAM | 4 GB | 8 GB+ |
| GPU | - (CPU saja) | NVIDIA GPU (CUDA 11.8+) |
| Storage | 2 GB | 5 GB+ |
| Kamera | Webcam USB | IP Camera / CCTV RTSP |

---

## Instalasi Lengkap

### LANGKAH 1 — Install Python

**Windows:**
1. Download Python dari https://python.org/downloads
2. Centang ✅ **"Add Python to PATH"** saat instalasi
3. Verifikasi: buka CMD, ketik `python --version`

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
python3 --version
```

**macOS:**
```bash
brew install python3
python3 --version
```

---

### LANGKAH 2 — Buat Virtual Environment

> ⚠️ Sangat disarankan menggunakan virtual environment agar tidak konflik dengan paket Python lain.

**Windows (CMD / PowerShell):**
```cmd
cd traffic_violation_system
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
cd traffic_violation_system
python3 -m venv venv
source venv/bin/activate
```

> Jika berhasil, terminal akan menampilkan prefix `(venv)` di depan prompt.

---

### LANGKAH 3 — Install Dependensi

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Proses ini akan mengunduh dan menginstal:
- **ultralytics** (YOLOv8 + PyTorch)
- **opencv-python** (OpenCV)
- **numpy**, **Pillow**, **pandas**

> ⏳ Proses instalasi bisa memakan waktu 5–15 menit tergantung koneksi internet.

---

### LANGKAH 4 — (Opsional) Install GPU Support

Jika Anda memiliki kartu grafis NVIDIA, install versi PyTorch dengan CUDA untuk performa lebih cepat:

```bash
# Cek versi CUDA yang terinstal
nvidia-smi

# Install PyTorch dengan CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install PyTorch dengan CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

---

### LANGKAH 5 — Download Model YOLO

Model akan diunduh otomatis saat pertama kali dijalankan. Namun, bisa juga diunduh manual:

```bash
# Dalam Python / terminal dengan venv aktif:
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

**Pilihan Model (trade-off kecepatan vs akurasi):**

| Model | Ukuran | Kecepatan | Akurasi | Cocok Untuk |
|-------|--------|-----------|---------|-------------|
| `yolov8n.pt` | 6 MB | ⚡⚡⚡ Tercepat | ⭐⭐ | CPU / Testing |
| `yolov8s.pt` | 22 MB | ⚡⚡ Cepat | ⭐⭐⭐ | CPU Kencang |
| `yolov8m.pt` | 52 MB | ⚡ Sedang | ⭐⭐⭐⭐ | GPU Entry |
| `yolov8l.pt` | 87 MB | 🐢 Lambat | ⭐⭐⭐⭐⭐ | GPU Mid-range |
| `yolov8x.pt` | 136 MB | 🐢🐢 | ⭐⭐⭐⭐⭐ | GPU High-end |

---

### LANGKAH 6 — (Opsional) Install Model Helm Khusus

Untuk deteksi helm yang lebih akurat, gunakan model YOLOv8 yang dilatih khusus:

```bash
# Download model helmet detection dari Roboflow (gratis):
# https://universe.roboflow.com/search?q=helmet+detection

# Atau gunakan model yang sudah ada:
# models/helmet_detector.pt  ← letakkan di folder models/
```

---

## Cara Menjalankan Program

### ▶ Mode 1: Demo (Tanpa Kamera)
Paling mudah untuk testing. Tidak membutuhkan webcam.
```bash
python main.py --source demo
```

### ▶ Mode 2: Webcam Langsung
```bash
# Kamera default (index 0)
python main.py --source 0

# Kamera kedua (index 1)
python main.py --source 1
```

### ▶ Mode 3: File Video
```bash
python main.py --source video_lalu_lintas.mp4

python main.py --source 0 --model "runs\detect\models\helmet_model3\weights\last.pt"
```


### ▶ Mode 4: CCTV via RTSP
```bash
# Format umum RTSP
python main.py --source "rtsp://username:password@192.168.1.100:554/stream"

# Contoh IP Camera Hikvision
python main.py --source "rtsp://admin:12345@192.168.1.64:554/Streaming/Channels/101"
```

### ▶ Mode 5: Simulasi Lampu Merah (untuk Testing)
```bash
python main.py --source demo --simulate-red
```

---

### 🎛 Opsi Lengkap Command Line

```
python main.py [OPTIONS]

Opsi:
  -s, --source TEXT     Sumber video (0=webcam, file.mp4, rtsp://..., demo)
  -m, --model TEXT      Model YOLO (default: yolov8n.pt)
  -c, --conf FLOAT      Confidence threshold 0.0-1.0 (default: 0.5)
  -o, --output TEXT     Simpan hasil ke file video
  --no-display          Mode headless (tanpa GUI, untuk server)
  --simulate-red        Mulai dengan simulasi lampu merah aktif
  -h, --help            Tampilkan bantuan
```

### Contoh Penggunaan Lengkap:
```bash
# Webcam dengan model lebih akurat, simpan output
python main.py --source 0 --model yolov8s.pt --conf 0.6 --output hasil.mp4

# File video tanpa GUI (server mode)
python main.py --source rekaman.mp4 --no-display

# CCTV dengan confidence lebih rendah
python main.py --source "rtsp://..." --conf 0.4
```

---

### ⌨️ Kontrol Keyboard (saat program berjalan)

| Tombol | Fungsi |
|--------|--------|
| `Q` | Keluar dari program |
| `S` | Simpan screenshot |
| `R` | Toggle simulasi lampu merah ON/OFF |

---

## Cara Kerja Sistem

### Deteksi Pelanggaran Lampu Merah
1. Sistem memantau status lampu lalu lintas (simulasi / deteksi warna)
2. Saat lampu **MERAH**, garis stop diaktifkan
3. Jika kendaraan terdeteksi melewati garis stop → **PELANGGARAN DICATAT**

### Deteksi Pengendara Tanpa Helm
1. YOLO mendeteksi **sepeda motor** dalam frame
2. Sistem mencari **orang** yang berada di atas motor tersebut
3. Mengecek apakah ada **helm** di area kepala pengendara
4. Jika tidak ada helm → **PELANGGARAN DICATAT**

---

## Konfigurasi Lanjutan

Edit file `config/settings.py` untuk menyesuaikan:

```python
# Posisi garis stop (0.0 = atas frame, 1.0 = bawah frame)
STOP_LINE_RATIO = 0.55

# Jeda antar pencatatan pelanggaran yang sama (detik)
VIOLATION_COOLDOWN = 3.0

# Area lampu lalu lintas di frame (x1%, y1%, x2%, y2%)
TRAFFIC_LIGHT_ROI = (0.45, 0.05, 0.55, 0.35)
```

---

## Output & Log

Semua pelanggaran disimpan di folder `violations/`:

```
violations/
├── images/
│   ├── RED_LIGHT_20240615_143022_123.jpg   ← Foto bukti
│   └── NO_HELMET_20240615_143045_456.jpg
├── violations_log.csv    ← Log lengkap (Excel-compatible)
└── summary.json          ← Statistik ringkasan
```

### Format CSV Log:
```
timestamp,type,vehicle,confidence,bbox_x1,bbox_y1,bbox_x2,bbox_y2,image_file,message
2024-06-15T14:30:22,RED_LIGHT,car,0.876,320,410,540,580,RED_LIGHT_...,Kendaraan melanggar lampu MERAH!
2024-06-15T14:30:45,NO_HELMET,motorcycle,0.741,200,300,350,480,NO_HELMET_...,Pengendara tidak memakai helm!
```

---

## Troubleshooting

### ❌ `ModuleNotFoundError: No module named 'ultralytics'`
```bash
pip install ultralytics
```

### ❌ `cv2.error: Can't open camera`
- Pastikan webcam terhubung
- Coba ganti index: `--source 1` atau `--source 2`
- Gunakan mode demo: `--source demo`

### ❌ Program berjalan sangat lambat (< 5 FPS)
```bash
# Gunakan model yang lebih kecil
python main.py --source 0 --model yolov8n.pt

# Kurangi resolusi kamera (edit di config/settings.py)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
```

### ❌ `CUDA out of memory`
```bash
# Paksa gunakan CPU
python main.py --source 0 --model yolov8n.pt
# Atau set environment variable:
# Windows: set CUDA_VISIBLE_DEVICES=-1
# Linux:   export CUDA_VISIBLE_DEVICES=-1
```

### ❌ Tidak ada deteksi objek
- Turunkan confidence threshold: `--conf 0.3`
- Pastikan pencahayaan cukup
- Coba model yang lebih besar: `--model yolov8s.pt`

---

## Struktur Proyek

```
traffic_violation_system/
├── main.py                 ← Entry point utama
├── requirements.txt        ← Daftar dependensi
├── README.md               ← Dokumentasi ini
├── config/
│   ├── __init__.py
│   └── settings.py         ← Konfigurasi global
├── utils/
│   ├── __init__.py
│   ├── detector.py         ← Deteksi objek (YOLO)
│   ├── traffic_light.py    ← Monitor lampu merah
│   ├── logger.py           ← Pencatatan pelanggaran
│   └── display.py          ← Rendering HUD
├── models/                 ← Folder model (auto-populated)
├── violations/             ← Output pelanggaran (auto-created)
└── logs/                   ← Log sistem
```

---

## Lisensi
Sistem ini dibuat untuk tujuan edukasi dan penelitian.
Gunakan secara bertanggung jawab sesuai regulasi privasi yang berlaku.
