"""
Zeiterfassung – Lokale Desktop-Anwendung
=========================================
Starten: python main.py

Abhängigkeiten installieren:
    pip install -r requirements.txt
"""
import sys
import os

# Sicherstellen, dass Importe aus dem eigenen Verzeichnis funktionieren
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

import database as db
from tray_widget import FloatingTimer, TrayManager
from backend_window import BackendWindow


def main():
    # HiDPI-Skalierung für Windows
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("Zeiterfassung")
    app.setQuitOnLastWindowClosed(False)  # App läuft auch ohne Fenster weiter

    # Datenbank initialisieren
    db.init_db()

    # Backend-Fenster (lazy, wird auf Knopfdruck geöffnet)
    backend = BackendWindow()

    # Timer-Widget
    timer = FloatingTimer()
    timer.show()

    # Backend-Button im Widget verbinden
    timer.open_btn.clicked.connect(lambda: (backend.show(), backend.raise_(), backend.activateWindow()))

    # Nach Stopp: Dialog zum Zuweisen öffnen
    def on_timer_stopped(start_time, end_time, duration_minutes):
        from dialogs import StopTimerDialog
        dlg = StopTimerDialog(None, start_time, end_time, duration_minutes)
        if dlg.exec():
            # Backend aktualisieren, falls geöffnet
            if backend.isVisible():
                backend.findChild(type(backend.centralWidget()).__mro__[0])
            backend.load_entries() if hasattr(backend, "load_entries") else None
            # Tab 0 hat load_entries via Attribut
            try:
                backend.load_entries()
            except Exception:
                pass

    timer.stopped.connect(on_timer_stopped)

    # System Tray
    tray = TrayManager(app, timer)

    # Startposition: unten rechts
    from PyQt6.QtWidgets import QApplication as _QApp
    screen = _QApp.primaryScreen().availableGeometry()
    timer.move(screen.right() - timer.width() - 20, screen.bottom() - timer.height() - 20)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
