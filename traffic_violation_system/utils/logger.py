"""
utils/logger.py
Pencatatan dan penyimpanan bukti pelanggaran lalu lintas.
Output: gambar (JPG), CSV log, dan JSON ringkasan.
"""

import cv2
import csv
import json
import os
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class ViolationLogger:
    """
    Catat dan simpan setiap pelanggaran yang terdeteksi.
    
    Struktur output:
    violations/
    ├── images/           ← Foto bukti pelanggaran
    │   ├── RED_LIGHT_20240101_120000.jpg
    │   └── NO_HELMET_20240101_120005.jpg
    ├── violations_log.csv ← Log lengkap dalam format CSV
    └── summary.json       ← Ringkasan statistik
    """

    def __init__(self, output_dir: str = "violations"):
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.log_path   = self.output_dir / "violations_log.csv"
        self.summary_path = self.output_dir / "summary.json"

        # Buat direktori
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Inisialisasi CSV
        self._init_csv()

        # Counter
        self.counts = {"RED_LIGHT": 0, "NO_HELMET": 0}

    def _init_csv(self):
        """Buat CSV dengan header jika belum ada."""
        if not self.log_path.exists():
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "timestamp", "type", "vehicle", "confidence",
                    "bbox_x1", "bbox_y1", "bbox_x2", "bbox_y2",
                    "image_file", "message"
                ])
                writer.writeheader()

    def log_violation(self, frame: np.ndarray, violation: Dict[str, Any]):
        """
        Simpan bukti pelanggaran (gambar + log CSV).
        
        Args:
            frame     : Frame video saat pelanggaran terjadi
            violation : Dict berisi detail pelanggaran
        """
        ts        = violation["timestamp"]
        v_type    = violation["type"]
        ts_str    = ts.strftime("%Y%m%d_%H%M%S_%f")[:-3]
        img_name  = f"{v_type}_{ts_str}.jpg"
        img_path  = self.images_dir / img_name

        # Gambar anotasi pada salinan frame
        annotated = self._annotate_frame(frame.copy(), violation)
        cv2.imwrite(str(img_path), annotated)

        # Tulis ke CSV
        x1, y1, x2, y2 = violation["bbox"]
        row = {
            "timestamp"  : ts.isoformat(),
            "type"       : v_type,
            "vehicle"    : violation.get("vehicle", "unknown"),
            "confidence" : f"{violation['confidence']:.3f}",
            "bbox_x1"    : x1,
            "bbox_y1"    : y1,
            "bbox_x2"    : x2,
            "bbox_y2"    : y2,
            "image_file" : img_name,
            "message"    : violation.get("message", "")
        }
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            writer.writerow(row)

        # Update counter
        self.counts[v_type] = self.counts.get(v_type, 0) + 1
        self._save_summary()

    def _annotate_frame(self, frame: np.ndarray, violation: Dict) -> np.ndarray:
        """Tambahkan anotasi pelanggaran pada frame."""
        x1, y1, x2, y2 = violation["bbox"]
        color   = violation.get("color", (0, 0, 255))
        v_type  = violation["type"]

        # Kotak merah tebal di sekitar objek
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

        # Label pelanggaran
        label = f"PELANGGARAN: {v_type}"
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(frame, (x1, y1 - lh - 10), (x1 + lw + 10, y1), color, -1)
        cv2.putText(frame, label, (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Timestamp
        ts_text = violation["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, ts_text, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)

        # Watermark
        cv2.putText(frame, "SISTEM DETEKSI PELANGGARAN", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        return frame

    def _save_summary(self):
        """Simpan ringkasan statistik ke JSON."""
        summary = {
            "last_updated": datetime.now().isoformat(),
            "total_violations": sum(self.counts.values()),
            "by_type": self.counts,
            "log_file": str(self.log_path),
            "images_dir": str(self.images_dir)
        }
        with open(self.summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def get_counts(self) -> Dict[str, int]:
        return self.counts.copy()
