from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QTextEdit, QCheckBox,
    QDateTimeEdit, QSpinBox, QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDateTime

import database as db
from models import Customer, Project, Task, TimeEntry

DIALOG_STYLE = """
    QDialog { background-color: #1e272e; color: #ecf0f1; }
    QLabel { color: #ecf0f1; }
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit {
        background-color: #2c3e50; color: #ecf0f1;
        border: 1px solid #34495e; border-radius: 4px; padding: 4px 8px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { background-color: #2c3e50; color: #ecf0f1; selection-background-color: #3498db; }
    QPushButton {
        background-color: #2c3e50; color: #ecf0f1; border: 1px solid #34495e;
        border-radius: 5px; padding: 6px 16px;
    }
    QPushButton:hover { background-color: #34495e; }
    QCheckBox { color: #ecf0f1; }
    QDialogButtonBox QPushButton[text="OK"] {
        background-color: #3498db; color: white; border: none;
    }
"""


class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer: Optional[Customer] = None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle("Kunde bearbeiten" if customer else "Neuer Kunde")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(360)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.number_edit = QLineEdit()
        self.number_edit.setPlaceholderText("z.B. K-001")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Firmenname")

        if self.customer:
            self.number_edit.setText(self.customer.number)
            self.name_edit.setText(self.customer.name)

        form.addRow("Kundennummer *:", self.number_edit)
        form.addRow("Name *:", self.name_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def _save(self):
        number = self.number_edit.text().strip()
        name = self.name_edit.text().strip()
        if not number or not name:
            QMessageBox.warning(self, "Fehler", "Bitte alle Pflichtfelder ausfüllen.")
            return
        c = Customer(id=self.customer.id if self.customer else None, number=number, name=name)
        try:
            db.save_customer(c)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))


class ProjectDialog(QDialog):
    def __init__(self, parent=None, project: Optional[Project] = None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Projekt bearbeiten" if project else "Neues Projekt")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.customer_combo = QComboBox()
        customers = db.get_all_customers()
        for c in customers:
            self.customer_combo.addItem(f"{c.number} – {c.name}", c.id)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Projektname")
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Kurze Beschreibung (optional)")

        if self.project:
            for i in range(self.customer_combo.count()):
                if self.customer_combo.itemData(i) == self.project.customer_id:
                    self.customer_combo.setCurrentIndex(i)
                    break
            self.name_edit.setText(self.project.name)
            self.desc_edit.setText(self.project.description or "")

        form.addRow("Kunde *:", self.customer_combo)
        form.addRow("Projektname *:", self.name_edit)
        form.addRow("Beschreibung:", self.desc_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def _save(self):
        cid = self.customer_combo.currentData()
        name = self.name_edit.text().strip()
        desc = self.desc_edit.text().strip()
        if not cid or not name:
            QMessageBox.warning(self, "Fehler", "Bitte Kunde und Projektname ausfüllen.")
            return
        p = Project(
            id=self.project.id if self.project else None,
            customer_id=cid, name=name, description=desc
        )
        db.save_project(p)
        self.accept()


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: Optional[Task] = None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle("Aufgabe bearbeiten" if task else "Neue Aufgabe")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(380)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Aufgabenname")

        self.global_check = QCheckBox("Globale Aufgabe (für alle Projekte)")
        self.global_check.setChecked(True)
        self.global_check.toggled.connect(self._on_global_toggled)

        self.project_combo = QComboBox()
        self.project_combo.addItem("– kein Projekt –", None)
        for p in db.get_projects():
            self.project_combo.addItem(f"{p.customer_name}: {p.name}", p.id)
        self.project_combo.setEnabled(False)

        if self.task:
            self.name_edit.setText(self.task.name)
            self.global_check.setChecked(self.task.is_global)
            if not self.task.is_global and self.task.project_id:
                self.project_combo.setEnabled(True)
                for i in range(self.project_combo.count()):
                    if self.project_combo.itemData(i) == self.task.project_id:
                        self.project_combo.setCurrentIndex(i)
                        break

        form.addRow("Name *:", self.name_edit)
        form.addRow("", self.global_check)
        form.addRow("Projekt:", self.project_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_global_toggled(self, checked: bool):
        self.project_combo.setEnabled(not checked)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Bitte einen Namen eingeben.")
            return
        is_global = self.global_check.isChecked()
        pid = None if is_global else self.project_combo.currentData()
        t = Task(
            id=self.task.id if self.task else None,
            name=name, is_global=is_global, project_id=pid
        )
        db.save_task(t)
        self.accept()


class StopTimerDialog(QDialog):
    """Wird nach dem Stoppen des Timers gezeigt – Kunde/Projekt/Aufgabe/Notiz."""

    def __init__(self, parent, start_time: datetime, end_time: datetime, duration_minutes: int):
        super().__init__(parent)
        self.start_time = start_time
        self.end_time = end_time
        self.duration_minutes = duration_minutes
        self.setWindowTitle("Zeiteintrag speichern")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(440)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Info-Banner
        h = self.duration_minutes // 60
        m = self.duration_minutes % 60
        info = QLabel(
            f"Zeitraum: {self.start_time.strftime('%d.%m.%Y %H:%M')} – "
            f"{self.end_time.strftime('%H:%M')}\n"
            f"Dauer (auf 15 Min aufgerundet): {h:02d}:{m:02d} h = {self.duration_minutes} Min"
        )
        info.setStyleSheet("background-color: #2c3e50; border-radius: 6px; padding: 8px; color: #3498db;")
        layout.addWidget(info)

        form = QFormLayout()

        self.customer_combo = QComboBox()
        self.customer_combo.addItem("– Bitte wählen –", None)
        for c in db.get_all_customers():
            self.customer_combo.addItem(f"{c.number} – {c.name}", c.id)
        self.customer_combo.currentIndexChanged.connect(self._on_customer_changed)

        self.project_combo = QComboBox()
        self.project_combo.addItem("– Bitte wählen –", None)
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)

        self.task_combo = QComboBox()
        self.task_combo.addItem("– keine –", None)
        for t in db.get_tasks():
            self.task_combo.addItem(t.name, t.id)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Notiz (optional)...")
        self.note_edit.setMaximumHeight(80)

        form.addRow("Kunde *:", self.customer_combo)
        form.addRow("Projekt *:", self.project_combo)
        form.addRow("Aufgabe:", self.task_combo)
        form.addRow("Notiz:", self.note_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Speichern")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_customer_changed(self):
        cid = self.customer_combo.currentData()
        self.project_combo.clear()
        self.project_combo.addItem("– Bitte wählen –", None)
        if cid:
            for p in db.get_projects(cid):
                self.project_combo.addItem(p.name, p.id)

    def _on_project_changed(self):
        pid = self.project_combo.currentData()
        self.task_combo.clear()
        self.task_combo.addItem("– keine –", None)
        for t in db.get_tasks(pid):
            self.task_combo.addItem(t.name, t.id)

    def _save(self):
        cid = self.customer_combo.currentData()
        pid = self.project_combo.currentData()
        if not cid or not pid:
            QMessageBox.warning(self, "Fehler", "Bitte Kunde und Projekt auswählen.")
            return
        entry = TimeEntry(
            id=None,
            customer_id=cid,
            project_id=pid,
            task_id=self.task_combo.currentData(),
            start_time=self.start_time.isoformat(timespec="seconds"),
            end_time=self.end_time.isoformat(timespec="seconds"),
            duration_minutes=self.duration_minutes,
            note=self.note_edit.toPlainText().strip(),
        )
        db.save_time_entry(entry)
        self.accept()


class TimeEntryDialog(QDialog):
    """Eintrag manuell anlegen oder bearbeiten."""

    def __init__(self, parent=None, entry: Optional[TimeEntry] = None):
        super().__init__(parent)
        self.entry = entry
        self.setWindowTitle("Zeiteintrag bearbeiten" if entry else "Neuer Zeiteintrag")
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(460)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        now = QDateTime.currentDateTime()

        self.start_edit = QDateTimeEdit(now.addSecs(-3600))
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat("dd.MM.yyyy HH:mm")

        self.end_edit = QDateTimeEdit(now)
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDisplayFormat("dd.MM.yyyy HH:mm")

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(15, 9999)
        self.duration_spin.setSingleStep(15)
        self.duration_spin.setSuffix(" Min")
        self.duration_spin.setValue(60)

        self.customer_combo = QComboBox()
        self.customer_combo.addItem("– Bitte wählen –", None)
        for c in db.get_all_customers():
            self.customer_combo.addItem(f"{c.number} – {c.name}", c.id)
        self.customer_combo.currentIndexChanged.connect(self._on_customer_changed)

        self.project_combo = QComboBox()
        self.project_combo.addItem("– Bitte wählen –", None)
        self.project_combo.currentIndexChanged.connect(self._on_project_changed)

        self.task_combo = QComboBox()
        self.task_combo.addItem("– keine –", None)
        for t in db.get_tasks():
            self.task_combo.addItem(t.name, t.id)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Notiz (optional)...")
        self.note_edit.setMaximumHeight(80)

        self.invoiced_check = QCheckBox("Bereits fakturiert")

        if self.entry:
            self.start_edit.setDateTime(QDateTime.fromString(self.entry.start_time[:16], "yyyy-MM-ddTHH:mm"))
            self.end_edit.setDateTime(QDateTime.fromString(self.entry.end_time[:16], "yyyy-MM-ddTHH:mm"))
            self.duration_spin.setValue(self.entry.duration_minutes)
            # Set customer
            for i in range(self.customer_combo.count()):
                if self.customer_combo.itemData(i) == self.entry.customer_id:
                    self.customer_combo.setCurrentIndex(i)
                    break
            # Project loaded by signal; set after
            self.note_edit.setPlainText(self.entry.note or "")
            self.invoiced_check.setChecked(self.entry.invoiced)

        form.addRow("Beginn *:", self.start_edit)
        form.addRow("Ende *:", self.end_edit)
        form.addRow("Dauer *:", self.duration_spin)
        form.addRow("Kunde *:", self.customer_combo)
        form.addRow("Projekt *:", self.project_combo)
        form.addRow("Aufgabe:", self.task_combo)
        form.addRow("Notiz:", self.note_edit)
        form.addRow("", self.invoiced_check)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)

        # Pre-select project after customer was set
        if self.entry:
            for i in range(self.project_combo.count()):
                if self.project_combo.itemData(i) == self.entry.project_id:
                    self.project_combo.setCurrentIndex(i)
                    break
            for i in range(self.task_combo.count()):
                if self.task_combo.itemData(i) == self.entry.task_id:
                    self.task_combo.setCurrentIndex(i)
                    break

    def _on_customer_changed(self):
        cid = self.customer_combo.currentData()
        self.project_combo.clear()
        self.project_combo.addItem("– Bitte wählen –", None)
        if cid:
            for p in db.get_projects(cid):
                self.project_combo.addItem(p.name, p.id)

    def _on_project_changed(self):
        pid = self.project_combo.currentData()
        self.task_combo.clear()
        self.task_combo.addItem("– keine –", None)
        for t in db.get_tasks(pid):
            self.task_combo.addItem(t.name, t.id)

    def _save(self):
        cid = self.customer_combo.currentData()
        pid = self.project_combo.currentData()
        if not cid or not pid:
            QMessageBox.warning(self, "Fehler", "Bitte Kunde und Projekt auswählen.")
            return

        start_str = self.start_edit.dateTime().toString("yyyy-MM-ddTHH:mm:ss")
        end_str = self.end_edit.dateTime().toString("yyyy-MM-ddTHH:mm:ss")

        entry = TimeEntry(
            id=self.entry.id if self.entry else None,
            customer_id=cid,
            project_id=pid,
            task_id=self.task_combo.currentData(),
            start_time=start_str,
            end_time=end_str,
            duration_minutes=self.duration_spin.value(),
            note=self.note_edit.toPlainText().strip(),
            invoiced=self.invoiced_check.isChecked(),
        )
        db.save_time_entry(entry)
        self.accept()
