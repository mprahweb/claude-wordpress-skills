from datetime import datetime, date
from typing import List, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDateEdit,
    QCheckBox, QTabWidget, QMessageBox, QAbstractItemView, QFrame,
    QSizePolicy, QGroupBox, QSpacerItem
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont

import database as db
from models import Customer, Project, Task, TimeEntry


STYLE = """
    QMainWindow, QWidget { background-color: #1e272e; color: #ecf0f1; font-size: 13px; }
    QTabWidget::pane { border: 1px solid #34495e; }
    QTabBar::tab { background: #2c3e50; color: #bdc3c7; padding: 8px 20px; border-radius: 4px 4px 0 0; }
    QTabBar::tab:selected { background: #3498db; color: white; }
    QGroupBox { border: 1px solid #34495e; border-radius: 6px; margin-top: 8px; padding-top: 8px; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; color: #3498db; font-weight: bold; }
    QPushButton {
        background-color: #2c3e50; color: #ecf0f1; border: 1px solid #34495e;
        border-radius: 5px; padding: 6px 14px; font-size: 12px;
    }
    QPushButton:hover { background-color: #34495e; }
    QPushButton.primary { background-color: #3498db; color: white; border: none; }
    QPushButton.primary:hover { background-color: #2980b9; }
    QPushButton.danger { background-color: #e74c3c; color: white; border: none; }
    QPushButton.danger:hover { background-color: #c0392b; }
    QPushButton.success { background-color: #27ae60; color: white; border: none; }
    QPushButton.success:hover { background-color: #2ecc71; }
    QComboBox { background-color: #2c3e50; color: #ecf0f1; border: 1px solid #34495e; border-radius: 4px; padding: 4px 8px; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { background-color: #2c3e50; color: #ecf0f1; selection-background-color: #3498db; }
    QDateEdit { background-color: #2c3e50; color: #ecf0f1; border: 1px solid #34495e; border-radius: 4px; padding: 4px 8px; }
    QTableWidget {
        background-color: #2c3e50; color: #ecf0f1; border: 1px solid #34495e;
        gridline-color: #34495e; border-radius: 4px;
    }
    QTableWidget::item:selected { background-color: #3498db; color: white; }
    QHeaderView::section { background-color: #1e272e; color: #bdc3c7; padding: 6px; border: none; border-bottom: 1px solid #34495e; }
    QCheckBox { color: #ecf0f1; }
    QLabel { color: #ecf0f1; }
    QScrollBar:vertical { background: #2c3e50; width: 8px; }
    QScrollBar::handle:vertical { background: #34495e; border-radius: 4px; }
"""


def _btn(text: str, css_class: str = "") -> QPushButton:
    btn = QPushButton(text)
    if css_class:
        btn.setProperty("class", css_class)
        if css_class == "primary":
            btn.setStyleSheet("background-color: #3498db; color: white; border: none; border-radius: 5px; padding: 6px 14px;")
        elif css_class == "danger":
            btn.setStyleSheet("background-color: #e74c3c; color: white; border: none; border-radius: 5px; padding: 6px 14px;")
        elif css_class == "success":
            btn.setStyleSheet("background-color: #27ae60; color: white; border: none; border-radius: 5px; padding: 6px 14px;")
    return btn


class BackendWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zeiterfassung – Backend")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(STYLE)

        tabs = QTabWidget()
        tabs.addTab(self._build_entries_tab(), "Zeiteinträge")
        tabs.addTab(self._build_customers_tab(), "Kunden")
        tabs.addTab(self._build_projects_tab(), "Projekte")
        tabs.addTab(self._build_tasks_tab(), "Aufgaben")
        self.setCentralWidget(tabs)
        self.tabs = tabs

    # ══════════════════════════════════════════════════════════════════════
    # Tab: Zeiteinträge
    # ══════════════════════════════════════════════════════════════════════

    def _build_entries_tab(self) -> QWidget:
        from dialogs import TimeEntryDialog
        self._entry_dialog_class = TimeEntryDialog

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── Filter ────────────────────────────────────────────────────────
        filter_box = QGroupBox("Filter")
        f_layout = QHBoxLayout(filter_box)
        f_layout.setSpacing(10)

        self.period_combo = QComboBox()
        self.period_combo.addItems(["Aktueller Monat", "Letzter Monat", "Benutzerdefiniert"])
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)

        self.date_from = QDateEdit(QDate.currentDate().addDays(1 - QDate.currentDate().day()))
        self.date_from.setCalendarPopup(True)
        self.date_from.setEnabled(False)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setEnabled(False)

        self.filter_customer_combo = QComboBox()
        self.filter_customer_combo.setMinimumWidth(160)
        self.filter_project_combo = QComboBox()
        self.filter_project_combo.setMinimumWidth(160)
        self.filter_customer_combo.currentIndexChanged.connect(self._on_filter_customer_changed)

        btn_filter = _btn("Filtern", "primary")
        btn_filter.clicked.connect(self.load_entries)

        f_layout.addWidget(QLabel("Zeitraum:"))
        f_layout.addWidget(self.period_combo)
        f_layout.addWidget(QLabel("Von:"))
        f_layout.addWidget(self.date_from)
        f_layout.addWidget(QLabel("Bis:"))
        f_layout.addWidget(self.date_to)
        f_layout.addWidget(QLabel("Kunde:"))
        f_layout.addWidget(self.filter_customer_combo)
        f_layout.addWidget(QLabel("Projekt:"))
        f_layout.addWidget(self.filter_project_combo)
        f_layout.addWidget(btn_filter)
        f_layout.addStretch()

        # ── Tabelle ───────────────────────────────────────────────────────
        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(9)
        self.entries_table.setHorizontalHeaderLabels([
            "Datum", "Kunde", "Projekt", "Aufgabe",
            "Beginn", "Ende", "Dauer (Min)", "Notiz", "Fakturiert"
        ])
        self.entries_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entries_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.entries_table.verticalHeader().setVisible(False)
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setStyleSheet(
            "QTableWidget { alternate-background-color: #273746; }"
        )
        self.entries_table.doubleClicked.connect(self._edit_entry)

        # ── Aktionsleiste ─────────────────────────────────────────────────
        action_layout = QHBoxLayout()
        btn_new = _btn("+ Neu", "primary")
        btn_new.clicked.connect(self._new_entry)
        btn_edit = _btn("Bearbeiten")
        btn_edit.clicked.connect(self._edit_entry)
        btn_del = _btn("Löschen", "danger")
        btn_del.clicked.connect(self._delete_entry)
        btn_inv = _btn("Als fakturiert markieren", "success")
        btn_inv.clicked.connect(lambda: self._set_invoiced(True))
        btn_uninv = _btn("Fakturierung aufheben")
        btn_uninv.clicked.connect(lambda: self._set_invoiced(False))

        from pdf_export import export_pdf
        btn_pdf = _btn("PDF Export (Vormonat)")
        btn_pdf.clicked.connect(self._export_pdf)
        self._export_pdf_func = export_pdf

        self.sum_label = QLabel("Gesamt: 0 Min (0,00 h)")
        self.sum_label.setStyleSheet("color: #3498db; font-weight: bold;")

        action_layout.addWidget(btn_new)
        action_layout.addWidget(btn_edit)
        action_layout.addWidget(btn_del)
        action_layout.addWidget(btn_inv)
        action_layout.addWidget(btn_uninv)
        action_layout.addStretch()
        action_layout.addWidget(self.sum_label)
        action_layout.addWidget(btn_pdf)

        layout.addWidget(filter_box)
        layout.addWidget(self.entries_table)
        layout.addLayout(action_layout)

        self._refresh_filter_combos()
        self.load_entries()
        return w

    def _on_period_changed(self, idx: int):
        custom = idx == 2
        self.date_from.setEnabled(custom)
        self.date_to.setEnabled(custom)
        if idx == 0:  # Aktueller Monat
            today = QDate.currentDate()
            self.date_from.setDate(QDate(today.year(), today.month(), 1))
            self.date_to.setDate(today)
        elif idx == 1:  # Letzter Monat
            today = QDate.currentDate()
            first_this = QDate(today.year(), today.month(), 1)
            last_month_end = first_this.addDays(-1)
            last_month_start = QDate(last_month_end.year(), last_month_end.month(), 1)
            self.date_from.setDate(last_month_start)
            self.date_to.setDate(last_month_end)

    def _on_filter_customer_changed(self):
        self._refresh_project_filter()

    def _refresh_filter_combos(self):
        self.filter_customer_combo.blockSignals(True)
        self.filter_customer_combo.clear()
        self.filter_customer_combo.addItem("Alle Kunden", None)
        for c in db.get_all_customers():
            self.filter_customer_combo.addItem(f"{c.number} – {c.name}", c.id)
        self.filter_customer_combo.blockSignals(False)
        self._refresh_project_filter()

    def _refresh_project_filter(self):
        cid = self.filter_customer_combo.currentData()
        self.filter_project_combo.clear()
        self.filter_project_combo.addItem("Alle Projekte", None)
        for p in db.get_projects(cid):
            self.filter_project_combo.addItem(p.name, p.id)

    def load_entries(self):
        idx = self.period_combo.currentIndex()
        if idx == 0:
            today = date.today()
            df = date(today.year, today.month, 1).isoformat()
            dt = today.isoformat()
        elif idx == 1:
            today = date.today()
            first_this = date(today.year, today.month, 1)
            lm_end = date(first_this.year, first_this.month, 1).replace(day=1) - __import__("datetime").timedelta(days=1)
            lm_start = lm_end.replace(day=1)
            df = lm_start.isoformat()
            dt = lm_end.isoformat()
        else:
            df = self.date_from.date().toString("yyyy-MM-dd")
            dt = self.date_to.date().toString("yyyy-MM-dd")

        cid = self.filter_customer_combo.currentData()
        pid = self.filter_project_combo.currentData()

        entries = db.get_time_entries(df, dt, cid, pid)
        self._populate_entries_table(entries)

    def _populate_entries_table(self, entries: List[TimeEntry]):
        self.entries_table.setRowCount(0)
        total_minutes = 0
        for e in entries:
            row = self.entries_table.rowCount()
            self.entries_table.insertRow(row)
            start_dt = datetime.fromisoformat(e.start_time)
            date_str = start_dt.strftime("%d.%m.%Y")
            begin_str = start_dt.strftime("%H:%M")
            end_str = datetime.fromisoformat(e.end_time).strftime("%H:%M")
            items = [
                date_str,
                f"{e.customer_number} – {e.customer_name}" if e.customer_number else e.customer_name or "",
                e.project_name or "",
                e.task_name or "",
                begin_str,
                end_str,
                str(e.duration_minutes),
                e.note or "",
                "✓" if e.invoiced else "",
            ]
            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, e.id)
                if e.invoiced:
                    item.setForeground(QColor("#27ae60"))
                self.entries_table.setItem(row, col, item)
            total_minutes += e.duration_minutes

        hours = total_minutes / 60
        self.sum_label.setText(f"Gesamt: {total_minutes} Min ({hours:.2f} h)")
        self.entries_table.resizeColumnsToContents()
        self.entries_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

    def _selected_entry_id(self) -> Optional[int]:
        row = self.entries_table.currentRow()
        if row < 0:
            return None
        return self.entries_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _new_entry(self):
        from dialogs import TimeEntryDialog
        dlg = TimeEntryDialog(self)
        if dlg.exec():
            self.load_entries()
            self._refresh_filter_combos()

    def _edit_entry(self):
        eid = self._selected_entry_id()
        if eid is None:
            return
        entries = db.get_time_entries()
        entry = next((e for e in entries if e.id == eid), None)
        if entry is None:
            return
        from dialogs import TimeEntryDialog
        dlg = TimeEntryDialog(self, entry)
        if dlg.exec():
            self.load_entries()

    def _delete_entry(self):
        eid = self._selected_entry_id()
        if eid is None:
            return
        if QMessageBox.question(self, "Löschen", "Eintrag wirklich löschen?") == QMessageBox.StandardButton.Yes:
            db.delete_time_entry(eid)
            self.load_entries()

    def _set_invoiced(self, invoiced: bool):
        selected_rows = set(idx.row() for idx in self.entries_table.selectedIndexes())
        ids = [
            self.entries_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            for row in selected_rows
        ]
        if ids:
            db.set_invoiced(ids, invoiced)
            self.load_entries()

    def _export_pdf(self):
        from pdf_export import export_pdf
        import os
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF speichern", "zeiterfassung_export.pdf", "PDF-Dateien (*.pdf)"
        )
        if path:
            export_pdf(path, parent_widget=self)
            QMessageBox.information(self, "Export", f"PDF gespeichert:\n{path}")

    # ══════════════════════════════════════════════════════════════════════
    # Tab: Kunden
    # ══════════════════════════════════════════════════════════════════════

    def _build_customers_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(3)
        self.customers_table.setHorizontalHeaderLabels(["Kundennummer", "Name", "Angelegt am"])
        self.customers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.customers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.customers_table.verticalHeader().setVisible(False)
        self.customers_table.doubleClicked.connect(self._edit_customer)

        btn_layout = QHBoxLayout()
        btn_new = _btn("+ Neu", "primary")
        btn_new.clicked.connect(self._new_customer)
        btn_edit = _btn("Bearbeiten")
        btn_edit.clicked.connect(self._edit_customer)
        btn_del = _btn("Löschen", "danger")
        btn_del.clicked.connect(self._delete_customer)
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()

        layout.addWidget(self.customers_table)
        layout.addLayout(btn_layout)
        self.load_customers()
        return w

    def load_customers(self):
        customers = db.get_all_customers()
        self.customers_table.setRowCount(0)
        for c in customers:
            row = self.customers_table.rowCount()
            self.customers_table.insertRow(row)
            for col, text in enumerate([c.number, c.name, c.created_at or ""]):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, c.id)
                self.customers_table.setItem(row, col, item)
        self.customers_table.resizeColumnsToContents()
        self.customers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

    def _selected_customer_id(self) -> Optional[int]:
        row = self.customers_table.currentRow()
        if row < 0:
            return None
        return self.customers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _new_customer(self):
        from dialogs import CustomerDialog
        dlg = CustomerDialog(self)
        if dlg.exec():
            self.load_customers()
            self._refresh_filter_combos()

    def _edit_customer(self):
        cid = self._selected_customer_id()
        if cid is None:
            return
        customers = db.get_all_customers()
        customer = next((c for c in customers if c.id == cid), None)
        if customer is None:
            return
        from dialogs import CustomerDialog
        dlg = CustomerDialog(self, customer)
        if dlg.exec():
            self.load_customers()
            self._refresh_filter_combos()

    def _delete_customer(self):
        cid = self._selected_customer_id()
        if cid is None:
            return
        if QMessageBox.question(self, "Löschen", "Kunden und alle zugehörigen Daten löschen?") == QMessageBox.StandardButton.Yes:
            db.delete_customer(cid)
            self.load_customers()
            self._refresh_filter_combos()

    # ══════════════════════════════════════════════════════════════════════
    # Tab: Projekte
    # ══════════════════════════════════════════════════════════════════════

    def _build_projects_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.projects_table = QTableWidget()
        self.projects_table.setColumnCount(4)
        self.projects_table.setHorizontalHeaderLabels(["Kunde", "Projektname", "Beschreibung", "Angelegt am"])
        self.projects_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.projects_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.projects_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.projects_table.verticalHeader().setVisible(False)
        self.projects_table.doubleClicked.connect(self._edit_project)

        btn_layout = QHBoxLayout()
        btn_new = _btn("+ Neu", "primary")
        btn_new.clicked.connect(self._new_project)
        btn_edit = _btn("Bearbeiten")
        btn_edit.clicked.connect(self._edit_project)
        btn_del = _btn("Löschen", "danger")
        btn_del.clicked.connect(self._delete_project)
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()

        layout.addWidget(self.projects_table)
        layout.addLayout(btn_layout)
        self.load_projects()
        return w

    def load_projects(self):
        projects = db.get_projects()
        self.projects_table.setRowCount(0)
        for p in projects:
            row = self.projects_table.rowCount()
            self.projects_table.insertRow(row)
            for col, text in enumerate([
                p.customer_name or "", p.name, p.description or "", p.created_at or ""
            ]):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, p.id)
                self.projects_table.setItem(row, col, item)
        self.projects_table.resizeColumnsToContents()
        self.projects_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

    def _selected_project_id(self) -> Optional[int]:
        row = self.projects_table.currentRow()
        if row < 0:
            return None
        return self.projects_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _new_project(self):
        from dialogs import ProjectDialog
        dlg = ProjectDialog(self)
        if dlg.exec():
            self.load_projects()
            self._refresh_filter_combos()

    def _edit_project(self):
        pid = self._selected_project_id()
        if pid is None:
            return
        projects = db.get_projects()
        project = next((p for p in projects if p.id == pid), None)
        if project is None:
            return
        from dialogs import ProjectDialog
        dlg = ProjectDialog(self, project)
        if dlg.exec():
            self.load_projects()
            self._refresh_filter_combos()

    def _delete_project(self):
        pid = self._selected_project_id()
        if pid is None:
            return
        if QMessageBox.question(self, "Löschen", "Projekt und alle Zeiteinträge löschen?") == QMessageBox.StandardButton.Yes:
            db.delete_project(pid)
            self.load_projects()
            self._refresh_filter_combos()

    # ══════════════════════════════════════════════════════════════════════
    # Tab: Aufgaben
    # ══════════════════════════════════════════════════════════════════════

    def _build_tasks_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(3)
        self.tasks_table.setHorizontalHeaderLabels(["Aufgabe", "Global", "Projekt"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tasks_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tasks_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tasks_table.verticalHeader().setVisible(False)
        self.tasks_table.doubleClicked.connect(self._edit_task)

        btn_layout = QHBoxLayout()
        btn_new = _btn("+ Neu", "primary")
        btn_new.clicked.connect(self._new_task)
        btn_edit = _btn("Bearbeiten")
        btn_edit.clicked.connect(self._edit_task)
        btn_del = _btn("Löschen", "danger")
        btn_del.clicked.connect(self._delete_task)
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_del)
        btn_layout.addStretch()

        layout.addWidget(self.tasks_table)
        layout.addLayout(btn_layout)
        self.load_tasks()
        return w

    def load_tasks(self):
        tasks = db.get_tasks()
        self.tasks_table.setRowCount(0)
        projects = {p.id: p.name for p in db.get_projects()}
        for t in tasks:
            row = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row)
            for col, text in enumerate([
                t.name,
                "✓" if t.is_global else "",
                projects.get(t.project_id, "") if t.project_id else ""
            ]):
                item = QTableWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, t.id)
                self.tasks_table.setItem(row, col, item)
        self.tasks_table.resizeColumnsToContents()
        self.tasks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def _selected_task_id(self) -> Optional[int]:
        row = self.tasks_table.currentRow()
        if row < 0:
            return None
        return self.tasks_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _new_task(self):
        from dialogs import TaskDialog
        dlg = TaskDialog(self)
        if dlg.exec():
            self.load_tasks()

    def _edit_task(self):
        tid = self._selected_task_id()
        if tid is None:
            return
        tasks = db.get_tasks()
        task = next((t for t in tasks if t.id == tid), None)
        if task is None:
            return
        from dialogs import TaskDialog
        dlg = TaskDialog(self, task)
        if dlg.exec():
            self.load_tasks()

    def _delete_task(self):
        tid = self._selected_task_id()
        if tid is None:
            return
        if QMessageBox.question(self, "Löschen", "Aufgabe löschen?") == QMessageBox.StandardButton.Yes:
            db.delete_task(tid)
            self.load_tasks()
