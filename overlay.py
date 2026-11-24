from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
)


def uci_to_grid(square: str, perspective: str):
    """Maps 'e2' -> (col, row) in 0..7 screen coordinates."""
    file_idx = ord(square[0]) - ord("a")
    rank_idx = int(square[1]) - 1
    if perspective == "w":
        return file_idx, 7 - rank_idx
    return 7 - file_idx, rank_idx


class BoardOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.best_move = None
        self.perspective = "w"

    def set_region(self, region: dict):
        self.setGeometry(
            region["left"], region["top"], region["width"], region["height"]
        )
        self.show()

    def update_move(self, uci_move: str | None, perspective: str):
        self.best_move = uci_move
        self.perspective = perspective
        self.update()

    def paintEvent(self, event):
        if not self.best_move or len(self.best_move) < 4:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        sq_w = self.width() / 8.0
        sq_h = self.height() / 8.0

        src_col, src_row = uci_to_grid(self.best_move[:2], self.perspective)
        dst_col, dst_row = uci_to_grid(self.best_move[2:4], self.perspective)

        src_rect = QRect(int(src_col * sq_w), int(src_row * sq_h), int(sq_w), int(sq_h))
        dst_rect = QRect(int(dst_col * sq_w), int(dst_row * sq_h), int(sq_w), int(sq_h))

        # Source square highlight (amber)
        painter.setPen(QPen(QColor(255, 193, 7, 230), 4))
        painter.setBrush(QBrush(QColor(255, 193, 7, 45)))
        painter.drawRect(src_rect.adjusted(2, 2, -2, -2))

        # Destination square highlight (emerald)
        painter.setPen(QPen(QColor(46, 204, 113, 230), 4))
        painter.setBrush(QBrush(QColor(46, 204, 113, 55)))
        painter.drawRect(dst_rect.adjusted(2, 2, -2, -2))

        # Connecting line
        painter.setPen(QPen(QColor(46, 204, 113, 180), 5))
        painter.drawLine(src_rect.center(), dst_rect.center())


class CalibrationOverlay(QWidget):
    region_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowOpacity(0.25)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.origin = QPoint()
        self.current = QPoint()
        self.dragging = False

    def start(self):
        # Span across all connected monitors
        virtual_geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(virtual_geo)
        self.show()

    def mousePressEvent(self, event):
        self.origin = event.pos()
        self.current = event.pos()
        self.dragging = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        rect = QRect(self.origin, self.current).normalized()
        # Convert to global desktop coordinates so mss captures the right monitor
        global_top_left = self.mapToGlobal(rect.topLeft())
        self.hide()
        if rect.width() > 80 and rect.height() > 80:
            self.region_selected.emit({
                "left": global_top_left.x(),
                "top": global_top_left.y(),
                "width": rect.width(),
                "height": rect.height(),
            })

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
        if self.dragging:
            rect = QRect(self.origin, self.current).normalized()
            painter.setPen(QPen(QColor(0, 255, 128), 3))
            painter.setBrush(QBrush(QColor(0, 255, 128, 40)))
            painter.drawRect(rect)


class ControlHUD(QWidget):
    calibrate_clicked = pyqtSignal()
    capture_clicked = pyqtSignal()
    analyze_clicked = pyqtSignal()
    toggle_auto = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BoardLens HUD")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)

        self.status_label = QLabel("Status: Not calibrated")
        self.eval_label = QLabel("Eval: -- | Move: --")
        layout.addWidget(self.status_label)
        layout.addWidget(self.eval_label)

        row = QHBoxLayout()
        self.side_combo = QComboBox()
        self.side_combo.addItems(["Auto", "White", "Black"])
        row.addWidget(QLabel("Side:"))
        row.addWidget(self.side_combo)
        layout.addLayout(row)

        self.btn_calibrate = QPushButton("Calibrate Board")
        self.btn_calibrate.clicked.connect(self.calibrate_clicked.emit)
        layout.addWidget(self.btn_calibrate)

        self.btn_capture = QPushButton("Capture Templates")
        self.btn_capture.clicked.connect(self.capture_clicked.emit)
        layout.addWidget(self.btn_capture)

        self.btn_analyze = QPushButton("Analyze Now")
        self.btn_analyze.clicked.connect(self.analyze_clicked.emit)
        layout.addWidget(self.btn_analyze)

        self.btn_auto = QPushButton("Auto-Scan: OFF")
        self.btn_auto.setCheckable(True)
        self.btn_auto.toggled.connect(self._on_auto_toggled)
        layout.addWidget(self.btn_auto)

    def _on_auto_toggled(self, checked: bool):
        self.btn_auto.setText(f"Auto-Scan: {'ON' if checked else 'OFF'}")
        self.toggle_auto.emit(checked)

    @property
    def perspective(self) -> str:
        text = self.side_combo.currentText()
        if text == "White":
            return "w"
        if text == "Black":
            return "b"
        return "auto"