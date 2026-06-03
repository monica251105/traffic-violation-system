"""
utils/traffic_light.py
Monitor status lampu lalu lintas.
Mendukung: deteksi via warna (OpenCV), simulasi, dan integrasi API eksternal.
"""

import cv2
import numpy as np
import time
from enum import Enum
from typing import Optional, Tuple


class LightState(Enum):
    RED    = "RED"
    YELLOW = "YELLOW"
    GREEN  = "GREEN"
    UNKNOWN= "UNKNOWN"


class TrafficLightMonitor:
    """
    Monitor dan analisis status lampu lalu lintas.
    
    Mode yang didukung:
    1. simulate=True  → siklus otomatis (RED/GREEN bergantian)
    2. simulate=False → deteksi warna dari ROI frame (butuh konfigurasi ROI)
    3. force_red      → paksa status MERAH (untuk testing)
    """

    # Durasi siklus simulasi (detik)
    RED_DURATION    = 57.0
    YELLOW_DURATION = 3.0
    GREEN_DURATION  = 57.0

    def __init__(
        self,
        simulate      : bool = True,
        roi           : Optional[Tuple[int,int,int,int]] = None,
    ):
        self.simulate       = simulate
        self.roi            = roi          # (x1, y1, x2, y2) area lampu di frame
        self._state         = LightState.RED
        self._phase_start   = time.time()
        self._force_red     = False
        self._sim_sequence  = [
            (LightState.RED,    self.RED_DURATION),
            (LightState.YELLOW, self.YELLOW_DURATION),
            (LightState.GREEN,  self.GREEN_DURATION),
            (LightState.YELLOW, self.YELLOW_DURATION),
        ]
        self._seq_index = 0

        # HSV bounds untuk deteksi warna
        self._red_lower1  = np.array([0,   120, 70])
        self._red_upper1  = np.array([10,  255, 255])
        self._red_lower2  = np.array([170, 120, 70])
        self._red_upper2  = np.array([180, 255, 255])
        self._green_lower = np.array([40,  50,  50])
        self._green_upper = np.array([90,  255, 255])

    # ──────────────────────────────────────────────────────────
    def update(self, frame: Optional[np.ndarray] = None):
        """
        Update status lampu. Panggil setiap frame.
        Jika frame diberikan dan ROI dikonfigurasi, gunakan deteksi warna.
        """
        if self._force_red:
            self._state = LightState.RED
            return

        if self.simulate:
            self._update_simulation()
        elif frame is not None and self.roi is not None:
            self._update_from_frame(frame)

    def _update_simulation(self):
        """Perbarui state berdasarkan siklus waktu."""
        elapsed = time.time() - self._phase_start
        _, duration = self._sim_sequence[self._seq_index]

        if elapsed >= duration:
            self._seq_index  = (self._seq_index + 1) % len(self._sim_sequence)
            self._state, _   = self._sim_sequence[self._seq_index]
            self._phase_start = time.time()

    def _update_from_frame(self, frame: np.ndarray):
        """Deteksi warna lampu dari ROI pada frame."""
        x1, y1, x2, y2 = self.roi
        roi_img = frame[y1:y2, x1:x2]
        if roi_img.size == 0:
            return

        hsv    = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
        
        red_mask1 = cv2.inRange(hsv, self._red_lower1, self._red_upper1)
        red_mask2 = cv2.inRange(hsv, self._red_lower2, self._red_upper2)
        red_mask  = cv2.bitwise_or(red_mask1, red_mask2)
        green_mask= cv2.inRange(hsv, self._green_lower, self._green_upper)

        red_pct   = cv2.countNonZero(red_mask)   / roi_img.size
        green_pct = cv2.countNonZero(green_mask) / roi_img.size

        THRESHOLD = 0.05
        if red_pct > THRESHOLD and red_pct > green_pct:
            self._state = LightState.RED
        elif green_pct > THRESHOLD:
            self._state = LightState.GREEN
        else:
            self._state = LightState.UNKNOWN

    # ──────────────────────────────────────────────────────────
    def is_red(self) -> bool:
        return self._state == LightState.RED

    def is_green(self) -> bool:
        return self._state == LightState.GREEN

    def get_state(self) -> LightState:
        return self._state

    def toggle_simulation(self):
        """Toggle paksa lampu MERAH (untuk debugging)."""
        self._force_red = not self._force_red
        if not self._force_red:
            self._state = LightState.GREEN

    def get_countdown(self) -> float:
        """Sisa waktu fase saat ini (hanya mode simulasi)."""
        if not self.simulate:
            return -1
        _, duration = self._sim_sequence[self._seq_index]
        elapsed = time.time() - self._phase_start
        return max(0.0, duration - elapsed)

    def get_state_label(self) -> str:
        labels = {
            LightState.RED    : "MERAH  🔴",
            LightState.YELLOW : "KUNING 🟡",
            LightState.GREEN  : "HIJAU  🟢",
            LightState.UNKNOWN: "?? ⚪",
        }
        return labels.get(self._state, "UNKNOWN")
