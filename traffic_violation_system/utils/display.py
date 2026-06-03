"""
utils/display.py
Rendering tampilan HUD (Heads-Up Display) pada frame video.
Menampilkan: status lampu, statistik, bounding box, panel info.
"""

import cv2
import numpy as np
import time
from typing import List, Dict, Any, Optional
from datetime import datetime


# Palet warna sistem (BGR)
C_RED     = (0,   0,   255)
C_GREEN   = (0,   220, 0  )
C_YELLOW  = (0,   210, 255)
C_ORANGE  = (0,   165, 255)
C_BLUE    = (255, 100, 0  )
C_CYAN    = (255, 220, 0  )
C_WHITE   = (255, 255, 255)
C_BLACK   = (0,   0,   0  )
C_DARK    = (20,  20,  25 )
C_PANEL   = (30,  30,  35 )


class DisplayManager:
    """
    Mengelola semua elemen visual pada output video.
    """

    def __init__(self, settings):
        self.settings      = settings
        self._alert_start  : Optional[float] = None
        self._alert_msg    : str = ""
        self._alert_color  = C_RED
        self._flash_state  = True
        self._last_flash   = time.time()

    # ──────────────────────────────────────────────────────────
    def render(
        self,
        frame          : np.ndarray,
        detections     : List[Dict],
        violations     : List[Dict],
        is_red         : bool,
        stats          : Dict,
        fps            : float,
        traffic_monitor
    ) -> np.ndarray:
        """
        Render semua elemen HUD pada frame.
        Returns frame yang sudah dianotasi + panel samping.
        """
        h, w = frame.shape[:2]

        # 1. Gambar garis stop
        self._draw_stop_line(frame, w, h, is_red)

        # 2. Gambar bounding box deteksi
        self._draw_detections(frame, detections, violations)

        # 3. Overlay pelanggaran aktif
        if violations:
            self._trigger_alert(violations[0])
        self._draw_alert_overlay(frame, w, h)

        # 4. Tambah panel samping (info dashboard)
        panel = self._create_side_panel(
            h, is_red, stats, fps, traffic_monitor, violations
        )
        combined = np.hstack([frame, panel])

        # 5. Header bar
        self._draw_header(combined, combined.shape[1], is_red)

        return combined

    # ──────────────────────────────────────────────────────────
    def _draw_stop_line(self, frame, w, h, is_red):
        """Gambar garis stop pada posisi yang dikonfigurasi."""
        from config.settings import Settings
        stop_x   = int(w * getattr(Settings, "STOP_LINE_X_RATIO", 0.5))
        start_y  = int(h * getattr(Settings, "STOP_LINE_START_Y", 1.0))
        end_y    = int(h * getattr(Settings, "STOP_LINE_END_Y", 0.5))
        color    = C_RED if is_red else C_GREEN
        thickness = 3 if is_red else 2

        cv2.line(frame, (stop_x, start_y), (stop_x, end_y), color, thickness)

        label = "GARIS STOP"
        text_y = end_y + ((start_y - end_y) // 2)
        # Put text vertically or just horizontally next to the line
        cv2.putText(frame, label,
                    (stop_x + 10, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

    def _draw_detections(self, frame, detections, violations):
        """Gambar bounding box untuk semua deteksi."""
        violation_bboxes = {v["bbox"] for v in violations}

        for det in detections:
            bbox    = det["bbox"]
            x1,y1,x2,y2 = bbox
            cls_name = det["class_name"]
            conf     = det["confidence"]

            # Warna berbeda jika ini objek yang melanggar
            if bbox in violation_bboxes:
                color = C_RED
                thick = 3
            elif cls_name in {"motorcycle","car","bus","truck"}:
                color = C_CYAN
                thick = 2
            elif cls_name == "person":
                color = C_ORANGE
                thick = 2
            else:
                color = C_WHITE
                thick = 1

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thick)

            # Label kecil
            label = f"{cls_name} {conf:.0%}"
            cv2.putText(frame, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    def _trigger_alert(self, violation: Dict):
        self._alert_start = time.time()
        self._alert_msg   = violation.get("message", "PELANGGARAN TERDETEKSI!")
        self._alert_color = violation.get("color", C_RED)

    def _draw_alert_overlay(self, frame, w, h):
        """Flash merah saat pelanggaran terjadi."""
        if self._alert_start is None:
            return

        elapsed = time.time() - self._alert_start
        if elapsed > 3.0:
            self._alert_start = None
            return

        # Flash interval
        if time.time() - self._last_flash > 0.25:
            self._flash_state  = not self._flash_state
            self._last_flash   = time.time()

        if self._flash_state:
            # Border merah berkedip
            border = 6
            cv2.rectangle(frame, (0, 0), (w, h),
                          self._alert_color, border)

            # Teks peringatan
            msg  = "⚠ " + self._alert_msg
            (tw, th), _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_DUPLEX, 0.85, 2)
            tx = (w - tw) // 2
            ty = 60

            # Background teks
            cv2.rectangle(frame, (tx - 10, ty - th - 8),
                          (tx + tw + 10, ty + 8),
                          self._alert_color, -1)
            cv2.putText(frame, msg, (tx, ty),
                        cv2.FONT_HERSHEY_DUPLEX, 0.85, C_WHITE, 2)

    def _create_side_panel(
        self, h, is_red, stats, fps, traffic_monitor, violations
    ) -> np.ndarray:
        """Buat panel samping dashboard 300px."""
        panel_w = 300
        panel   = np.full((h, panel_w, 3), C_PANEL, dtype=np.uint8)

        y = 20

        # ── Judul ────────────────────────────────────────────
        cv2.putText(panel, "DASHBOARD", (10, y),
                    cv2.FONT_HERSHEY_DUPLEX, 0.75, C_CYAN, 1)
        y += 5
        cv2.line(panel, (10, y), (panel_w - 10, y), C_CYAN, 1)
        y += 20

        # ── Status Lampu ─────────────────────────────────────
        light_color = C_RED if is_red else C_GREEN
        light_label = "MERAH" if is_red else "HIJAU"
        cv2.circle(panel, (25, y + 5), 12, light_color, -1)
        cv2.putText(panel, f"LAMPU: {light_label}", (45, y + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, light_color, 2)
        y += 35

        # Countdown
        countdown = traffic_monitor.get_countdown()
        if countdown >= 0:
            cv2.putText(panel, f"  Ganti dalam: {countdown:.1f}s", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_WHITE, 1)
            y += 25
        
        cv2.line(panel, (10, y), (panel_w - 10, y), (60, 60, 65), 1)
        y += 15

        # ── Statistik ────────────────────────────────────────
        cv2.putText(panel, "STATISTIK SESI", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, C_YELLOW, 1)
        y += 20

        elapsed = time.time() - stats["start_time"]
        items = [
            (f"FPS          : {fps:.1f}",  C_WHITE),
            (f"Frame        : {stats['frames']}",  C_WHITE),
            (f"Durasi       : {int(elapsed)}s",  C_WHITE),
        ]
        for text, color in items:
            cv2.putText(panel, text, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 1)
            y += 18
        y += 5

        cv2.line(panel, (10, y), (panel_w - 10, y), (60, 60, 65), 1)
        y += 15

        # ── Pelanggaran ──────────────────────────────────────
        cv2.putText(panel, "PELANGGARAN", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, C_RED, 1)
        y += 22

        rl = stats.get("red_violations", 0)
        nh = stats.get("helmet_violations", 0)

        cv2.putText(panel, f"Lampu Merah  : {rl}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, C_RED, 1)
        y += 20
        cv2.putText(panel, f"Tanpa Helm   : {nh}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, C_ORANGE, 1)
        y += 20
        total = rl + nh
        cv2.putText(panel, f"Total        : {total}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, C_WHITE, 2)
        y += 30

        cv2.line(panel, (10, y), (panel_w - 10, y), (60, 60, 65), 1)
        y += 15

        # ── Pelanggaran terbaru ──────────────────────────────
        if violations:
            cv2.putText(panel, "DETEKSI TERBARU:", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_YELLOW, 1)
            y += 18
            for v in violations[:3]:
                vt  = v["type"].replace("_", " ")
                clr = v.get("color", C_RED)
                cv2.putText(panel, f"  • {vt}", (10, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, clr, 1)
                y += 18
            y += 5

        cv2.line(panel, (10, y), (panel_w - 10, y), (60, 60, 65), 1)
        y += 15

        # ── Kontrol keyboard ─────────────────────────────────
        cv2.putText(panel, "KONTROL:", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, C_CYAN, 1)
        y += 18
        controls = [
            "Q  = Keluar",
            "S  = Screenshot",
            "R  = Toggle Lampu",
        ]
        for ctrl in controls:
            cv2.putText(panel, f"  {ctrl}", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.43, (160, 160, 170), 1)
            y += 16

        # ── Timestamp ────────────────────────────────────────
        now_str = datetime.now().strftime("%H:%M:%S")
        cv2.putText(panel, now_str, (panel_w // 2 - 30, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, C_WHITE, 1)

        return panel

    def _draw_header(self, frame, w, is_red):
        """Header bar tipis di atas frame."""
        bar_h = 28
        color = (20, 15, 40)
        cv2.rectangle(frame, (0, 0), (w, bar_h), color, -1)
        title = "SISTEM DETEKSI PELANGGARAN LALU LINTAS  |  v1.0"
        cv2.putText(frame, title, (10, 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, C_CYAN, 1)
        # Status dot
        dot_color = C_RED if is_red else C_GREEN
        cv2.circle(frame, (w - 20, 14), 6, dot_color, -1)
