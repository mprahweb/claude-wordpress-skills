# Zeiterfassung

Lokale Desktop-Anwendung zur Zeiterfassung mit System-Tray-Widget, Backend-Oberfläche und PDF-Export.

## Voraussetzungen

- Python 3.10+
- Windows (getestet), funktioniert auch auf macOS/Linux

## Installation

```bash
pip install -r requirements.txt
```

## Starten

```bash
python main.py
```

## Funktionen

### Timer-Widget
- Schwebendes, immer-vorne-liegendes Fenster (rechts unten)
- Start / Stopp per Knopfdruck
- Dauer wird auf **15 Minuten aufgerundet**
- Nach dem Stopp: Zuweisung zu Kunde, Projekt, Aufgabe + Notiz
- Tray-Icon zum Ein-/Ausblenden

### Backend-Oberfläche
| Tab | Inhalt |
|-----|--------|
| Zeiteinträge | Filter (Monat / Zeitraum / Kunde / Projekt), Tabelle, CRUD |
| Kunden | Kundenverwaltung mit Kundennummer |
| Projekte | Projekte je Kunde |
| Aufgaben | Globale und projektspezifische Aufgaben |

### PDF-Export
- Vormonat, nicht fakturierte Einträge
- Gegliedert nach Kunde → Projekt
- Mit Aufgaben, Notizen, Einzelzeiten und Summen
- Eigener Speicherpfad per Dialog

## Datenbankpfad

`zeiterfassung.db` (SQLite) im Programmverzeichnis.
