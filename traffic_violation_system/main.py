"""
=============================================================
  SISTEM DETEKSI PELANGGARAN LALU LINTAS BERBASIS ML
  Traffic Violation Detection System
  
  Fitur:
  - Deteksi pelanggaran lampu merah (Red Light Violation)
  - Deteksi pengendara tanpa helm (No Helmet Detection)
  - Logging & penyimpanan bukti pelanggaran
  - Dashboard real-time
=============================================================
"""

import cv2
import numpy as np
import argparse
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# Internal modules
from utils.detector import ViolationDetector
from utils.traffic_light import TrafficLightMonitor
from utils.logger import ViolationLogger
from utils.display import DisplayManager
from config.settings import Settings


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Sistem Deteksi Pelanggaran Lalu Lintas",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--source", "-s",
        type=str,
        default="0",
        help=(
            "Sumber video:\n"
            "  0, 1, 2   = Webcam/CCTV (index kamera)\n"
            "  video.mp4 = File video\n"
            "  rtsp://... = Stream RTSP CCTV\n"
            "  demo       = Mode demo (tanpa kamera)"
        )
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="yolov8n.pt",
        help="Model YOLO yang digunakan (default: yolov8n.pt)"
    )
    parser.add_argument(
        "--conf", "-c",
        type=float,
        default=0.5,
        help="Confidence threshold (0.0 - 1.0, default: 0.5)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Simpan output ke file video (opsional)"
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Jalankan tanpa tampilan GUI (headless mode)"
    )
    parser.add_argument(
        "--simulate-red",
        action="store_true",
        help="Simulasikan lampu merah untuk testing"
    )
    return parser.parse_args()


def main():
    print("=" * 60)
    print("  SISTEM DETEKSI PELANGGARAN LALU LINTAS")
    print("  Traffic Violation Detection System v1.0")
    print("=" * 60)
    
    args = parse_arguments()
    settings = Settings()
    
    # ── Inisialisasi komponen utama ──────────────────────────
    print("\n[INFO] Memuat model YOLO...")
    detector = ViolationDetector(
        model_path=args.model,
        conf_threshold=args.conf
    )
    
    print("[INFO] Menginisialisasi monitor lampu lalu lintas...")
    traffic_monitor = TrafficLightMonitor(simulate=args.simulate_red)
    
    print("[INFO] Menginisialisasi logger pelanggaran...")
    logger = ViolationLogger(output_dir=settings.VIOLATIONS_DIR)
    
    display_mgr = DisplayManager(settings)
    
    # ── Buka sumber video ────────────────────────────────────
    if args.source == "demo":
        print("[INFO] Mode DEMO aktif - membuat video sintetik...")
        cap = None
        demo_mode = True
    else:
        source = int(args.source) if args.source.isdigit() else args.source
        print(f"[INFO] Membuka sumber video: {source}")
        cap = cv2.VideoCapture(source)
        demo_mode = False
        
        if not cap.isOpened():
            print(f"[ERROR] Tidak dapat membuka sumber video: {source}")
            print("[HINT] Coba gunakan --source demo untuk mode demo")
            sys.exit(1)
    
    # ── Setup output video (opsional) ───────────────────────
    out_writer = None
    if args.output:
        fps = cap.get(cv2.CAP_PROP_FPS) if cap else 30
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if cap else 1280
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if cap else 720
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_writer = cv2.VideoWriter(args.output, fourcc, fps, (w + 300, h))
        print(f"[INFO] Output akan disimpan ke: {args.output}")
    
    print("\n[INFO] ✓ Semua komponen berhasil diinisialisasi!")
    print("[INFO] Tekan 'Q' untuk keluar, 'S' untuk screenshot")
    print("[INFO] Tekan 'R' untuk toggle simulasi lampu merah\n")
    print("-" * 60)
    
    # ── Statistik sesi ───────────────────────────────────────
    stats = {
        "frames": 0,
        "red_violations": 0,
        "helmet_violations": 0,
        "start_time": time.time()
    }
    
    frame_count = 0
    
    # ══════════════════════════════════════════════════════════
    #  MAIN LOOP
    # ══════════════════════════════════════════════════════════
    try:
        while True:
            frame_count += 1
            
            # Ambil frame
            if demo_mode:
                frame = _generate_demo_frame(frame_count, traffic_monitor.is_red())
                ret = True
            else:
                ret, frame = cap.read()
            
            if not ret or frame is None:
                print("[INFO] Video selesai atau frame tidak tersedia.")
                break
            
            # ── Update status lampu lalu lintas ─────────────
            traffic_monitor.update()
            # Pelanggaran dihitung jika lampu Merah ATAU Kuning
            is_violation_phase = traffic_monitor.is_red() or traffic_monitor.get_state().name == "YELLOW"
            
            # ── Deteksi objek dengan YOLO ────────────────────
            detections = detector.detect(frame)
            
            # ── Analisis pelanggaran ─────────────────────────
            violations = detector.analyze_violations(
                frame, detections, is_violation_phase
            )
            
            # ── Catat & simpan pelanggaran ───────────────────
            for violation in violations:
                logger.log_violation(frame, violation)
                if violation["type"] == "RED_LIGHT":
                    stats["red_violations"] += 1
                elif violation["type"] == "NO_HELMET":
                    stats["helmet_violations"] += 1
                    
                print(f"[PELANGGARAN] {violation['type']} terdeteksi! "
                      f"Confidence: {violation['confidence']:.2f}")
            
            stats["frames"] += 1
            elapsed = time.time() - stats["start_time"]
            fps_actual = frame_count / elapsed if elapsed > 0 else 0
            
            # ── Render tampilan ──────────────────────────────
            if not args.no_display:
                output_frame = display_mgr.render(
                    frame=frame,
                    detections=detections,
                    violations=violations,
                    is_red=is_violation_phase,
                    stats=stats,
                    fps=fps_actual,
                    traffic_monitor=traffic_monitor
                )
                
                cv2.imshow("Sistem Deteksi Pelanggaran Lalu Lintas", output_frame)
                
                if out_writer:
                    out_writer.write(output_frame)
                
                # Handle keyboard
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == ord("Q"):
                    print("\n[INFO] Keluar dari program...")
                    break
                elif key == ord("s") or key == ord("S"):
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    sc_path = f"violations/screenshot_{ts}.jpg"
                    cv2.imwrite(sc_path, output_frame)
                    print(f"[INFO] Screenshot disimpan: {sc_path}")
                elif key == ord("r") or key == ord("R"):
                    traffic_monitor.toggle_simulation()
                    state = "MERAH" if traffic_monitor.is_red() else "HIJAU"
                    print(f"[INFO] Lampu disimulasikan: {state}")
    
    except KeyboardInterrupt:
        print("\n[INFO] Dihentikan oleh pengguna (Ctrl+C)")
    
    finally:
        # ── Cleanup ──────────────────────────────────────────
        if cap:
            cap.release()
        if out_writer:
            out_writer.release()
        cv2.destroyAllWindows()
        
        # ── Laporan akhir sesi ───────────────────────────────
        elapsed = time.time() - stats["start_time"]
        print("\n" + "=" * 60)
        print("  LAPORAN SESI DETEKSI")
        print("=" * 60)
        print(f"  Durasi          : {elapsed:.1f} detik")
        print(f"  Frame diproses  : {stats['frames']}")
        print(f"  Pelanggaran Lampu Merah : {stats['red_violations']}")
        print(f"  Pelanggaran Helm        : {stats['helmet_violations']}")
        print(f"  Total pelanggaran       : {stats['red_violations'] + stats['helmet_violations']}")
        print(f"  Log disimpan di : violations/")
        print("=" * 60)


def _generate_demo_frame(frame_count: int, is_red: bool) -> np.ndarray:
    """Generate synthetic demo frame untuk testing tanpa kamera."""
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Background gradien
    for y in range(720):
        val = int(20 + (y / 720) * 30)
        frame[y, :] = [val, val + 5, val + 2]
    
    # Gambar jalan
    cv2.rectangle(frame, (200, 300), (1080, 720), (60, 60, 65), -1)
    cv2.rectangle(frame, (300, 300), (980, 720), (50, 50, 55), -1)
    
    # Marka jalan
    for x in range(400, 900, 100):
        cv2.rectangle(frame, (x, 500), (x + 60, 520), (200, 200, 200), -1)
    
    # Kendaraan animasi (bergerak)
    car_x = int(400 + (frame_count * 3) % 600)
    _draw_vehicle(frame, car_x, 400)
    
    # Lampu lalu lintas
    tl_color = (0, 0, 255) if is_red else (0, 255, 0)
    cv2.rectangle(frame, (580, 150), (620, 290), (30, 30, 30), -1)
    cv2.circle(frame, (600, 200), 20, tl_color, -1)
    
    # Label demo
    cv2.putText(frame, "MODE DEMO - Tidak ada kamera nyata",
                (10, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 255), 1)
    
    return frame


def _draw_vehicle(frame: np.ndarray, x: int, y: int):
    """Gambar kendaraan sederhana pada frame."""
    cv2.rectangle(frame, (x, y), (x + 120, y + 60), (150, 100, 50), -1)
    cv2.rectangle(frame, (x + 15, y - 25), (x + 105, y + 5), (130, 90, 45), -1)
    cv2.circle(frame, (x + 20, y + 62), 15, (40, 40, 40), -1)
    cv2.circle(frame, (x + 100, y + 62), 15, (40, 40, 40), -1)


if __name__ == "__main__":
    main()
