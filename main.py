import sys
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from engine import EngineManager
from vision import BoardVision
from overlay import BoardOverlay, CalibrationOverlay, ControlHUD

STOCKFISH_PATH = "stockfish.exe"


class ChessOverlayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.vision = BoardVision(template_dir="templates")
        self.engine = EngineManager(STOCKFISH_PATH, time_limit=0.25)

        self.overlay = BoardOverlay()
        self.calibrator = CalibrationOverlay()
        self.hud = ControlHUD()

        self.region = None
        self.last_frame = None
        self.last_fen = None
        self.stable_ticks = 0

        # Wire signals
        self.hud.calibrate_clicked.connect(self.calibrator.start)
        self.hud.capture_clicked.connect(self.capture_templates)
        self.hud.analyze_clicked.connect(self.analyze_once)
        self.hud.toggle_auto.connect(self.set_auto_scan)
        self.calibrator.region_selected.connect(self.on_calibrated)

        # Polling timer (every 200ms)
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_board)

        self.hud.show()

    def on_calibrated(self, region: dict):
        self.region = region
        self.last_frame = None
        self.last_fen = None
        self.stable_ticks = 0
        self.overlay.set_region(region)
        self.hud.status_label.setText("Status: Calibrated")

    def capture_templates(self):
        if not self.region:
            self.hud.status_label.setText("Status: Calibrate first!")
            return
        frame = self.vision.capture_board(self.region)
        count, side = self.vision.capture_starting_templates(
            frame, perspective=self.hud.perspective
        )
        self.last_fen = None
        side_name = "White" if side == "w" else "Black"
        self.hud.status_label.setText(f"Status: Saved {count} ({side_name})")

    def set_auto_scan(self, enabled: bool):
        if enabled and self.region:
            self.timer.start(200)
            self.hud.status_label.setText("Status: Scanning...")
        else:
            self.timer.stop()
            self.hud.status_label.setText("Status: Idle")

    def poll_board(self):
        if not self.region:
            return
        frame = self.vision.capture_board(self.region)

        # Debounce: wait for 2 consecutive identical frames (~400ms)
        if self.last_frame is not None and self.last_frame.shape == frame.shape:
            diff = np.mean(np.abs(frame.astype(float) - self.last_frame.astype(float)))
            if diff < 1.0:
                self.stable_ticks += 1
            else:
                self.stable_ticks = 0
        else:
            self.stable_ticks = 0

        self.last_frame = frame

        if self.stable_ticks == 2:
            self._run_analysis(frame)

    def analyze_once(self):
        if not self.region:
            self.hud.status_label.setText("Status: Calibrate first!")
            return
        frame = self.vision.capture_board(self.region)
        self._run_analysis(frame)

    def _run_analysis(self, frame: np.ndarray):
        fen, detected_side = self.vision.board_to_fen(
            frame, perspective=self.hud.perspective
        )
        side_name = "White" if detected_side == "w" else "Black"
        print(f"FEN ({side_name}):", fen)

        if fen == self.last_fen:
            return
        self.last_fen = fen

        move, eval_str = self.engine.analyze(fen)
        self.overlay.update_move(move, detected_side)
        self.hud.status_label.setText(f"Status: Playing {side_name}")
        self.hud.eval_label.setText(f"Eval: {eval_str} | Move: {move or '--'}")

    def run(self):
        exit_code = self.app.exec()
        self.engine.close()
        sys.exit(exit_code)


if __name__ == "__main__":
    ChessOverlayApp().run()