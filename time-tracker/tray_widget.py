import math
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QColor, QPainter, QPixmap


def create_tray_icon(recording: bool) -> QIcon:
    """Erstellt ein einfaches farbiges Tray-Icon."""
    pixmap = QPixmap(22, 22)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    color = QColor("#e74c3c") if recording else QColor("#27ae60")
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 18, 18)
    painter.end()
    return QIcon(pixmap)


class FloatingTimer(QWidget):
    """Kleines schwebendes Timer-Widget."""

    stopped = pyqtSignal(datetime, datetime, int)  # start, end, duration_minutes

    def __init__(self, parent=None):
        super().__init__(parent)
        self._start_time: datetime | None = None
        self._running = False
        self._elapsed_seconds = 0

        self.setWindowTitle("Zeiterfassung")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(210, 100)
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(1000)

        self._drag_pos = None

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget#container {
                background-color: #2c3e50;
                border-radius: 10px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#start_btn {
                background-color: #27ae60;
                color: white;
                border: none;
            }
            QPushButton#start_btn:hover { background-color: #2ecc71; }
            QPushButton#stop_btn {
                background-color: #e74c3c;
                color: white;
                border: none;
            }
            QPushButton#stop_btn:hover { background-color: #c0392b; }
            QPushButton#open_btn {
                background-color: #3498db;
                color: white;
                border: none;
            }
            QPushButton#open_btn:hover { background-color: #2980b9; }
        """)

        container = QWidget(self)
        container.setObjectName("container")
        container.setGeometry(0, 0, 210, 100)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(4)

        # Titelzeile mit Schließen-Button
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_label = QLabel("Zeiterfassung")
        title_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #7f8c8d; border: none; font-size: 11px; padding: 0; }"
            "QPushButton:hover { color: #e74c3c; }"
        )
        close_btn.clicked.connect(self.hide)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)

        self.time_label = QLabel("00:00:00")
        font = QFont("Consolas", 22, QFont.Weight.Bold)
        self.time_label.setFont(font)
        self.time_label.setStyleSheet("color: #ecf0f1;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.toggle_btn = QPushButton("Start")
        self.toggle_btn.setObjectName("start_btn")
        self.toggle_btn.clicked.connect(self._toggle)

        self.open_btn = QPushButton("Backend")
        self.open_btn.setObjectName("open_btn")

        btn_layout.addWidget(self.toggle_btn)
        btn_layout.addWidget(self.open_btn)

        layout.addLayout(title_layout)
        layout.addWidget(self.time_label)
        layout.addLayout(btn_layout)

    def _toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        self._start_time = datetime.now()
        self._elapsed_seconds = 0
        self._running = True
        self._timer.start()
        self.toggle_btn.setText("Stopp")
        self.toggle_btn.setObjectName("stop_btn")
        self.toggle_btn.setStyleSheet(
            "background-color: #e74c3c; color: white; border: none; border-radius: 6px; padding: 4px 12px; font-weight: bold; font-size: 12px;"
        )

    def _stop(self):
        self._timer.stop()
        self._running = False
        end_time = datetime.now()
        raw_minutes = self._elapsed_seconds / 60
        duration = math.ceil(raw_minutes / 15) * 15
        if duration == 0:
            duration = 15

        self.toggle_btn.setText("Start")
        self.toggle_btn.setObjectName("start_btn")
        self.toggle_btn.setStyleSheet(
            "background-color: #27ae60; color: white; border: none; border-radius: 6px; padding: 4px 12px; font-weight: bold; font-size: 12px;"
        )
        self.time_label.setText("00:00:00")

        self.stopped.emit(self._start_time, end_time, duration)
        self._start_time = None
        self._elapsed_seconds = 0

    def _tick(self):
        self._elapsed_seconds += 1
        h = self._elapsed_seconds // 3600
        m = (self._elapsed_seconds % 3600) // 60
        s = self._elapsed_seconds % 60
        self.time_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    # ── Drag to move ──────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class TrayManager:
    """Verwaltet das System-Tray-Icon."""

    def __init__(self, app: QApplication, timer_widget: FloatingTimer):
        self.app = app
        self.widget = timer_widget
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(create_tray_icon(False))
        self.tray.setToolTip("Zeiterfassung")
        self._build_menu()
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        # Update icon when recording state changes
        timer_widget.stopped.connect(lambda *_: self.tray.setIcon(create_tray_icon(False)))

    def _build_menu(self):
        menu = QMenu()
        action_show = menu.addAction("Widget anzeigen")
        action_show.triggered.connect(self.widget.show)
        action_backend = menu.addAction("Backend öffnen")
        action_backend.triggered.connect(self.widget.open_btn.clicked)
        menu.addSeparator()
        action_quit = menu.addAction("Beenden")
        action_quit.triggered.connect(self.app.quit)
        self.tray.setContextMenu(menu)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.widget.isVisible():
                self.widget.hide()
            else:
                self.widget.show()
