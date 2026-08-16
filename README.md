# Helden-Overhaul 🎲

**Helden-Overhaul** ist ein Tool, das alte HTML-Charakterbögen aus der "Helden-Software" (DSA / Das Schwarze Auge) modernisiert. Es verwandelt statische, veraltete Webseiten in interaktive, moderne Dashboards mit Dark-Mode-Unterstützung und integrierten Würfel-Funktionen – ohne die originalen Charakterdaten zu verändern.

## ✨ Features

- **Modernes Design:** Verwandelt das alte Layout in ein sauberes, responsives Interface.
- **Interaktive Würfel:** Klicke auf Eigenschaften (MU, KL, IN...), Talente oder Zauber, um direkt im Browser zu würfeln. Die Ergebnisse werden mathematisch korrekt gegen die Charakterwerte berechnet.
- **Dark Mode:** Ein integrierter Umschalter für Tag- und Nachtmodus (speichert die Präferenz im Browser).
- **Intelligente Proben:** Automatische Berechnung von Differenzen und Unterstützung für komplexe Proben (z.B. TaW/ZfW-Verbrauch).
- **Elfen-Modus:** Erkennt automatisch, ob der Charakter ein Elf ist, und kann Zauberproben in der elfischen Notation (z.B. IN statt KL) darstellen.
- **Non-Destructive:** Das Original wird nicht überschrieben. Es wird eine neue Datei mit dem Suffix `_modern.html` erstellt.
- **Encoding-Fix:** Konvertiert alte Windows-1252/CP1252 Dateien automatisch in sauberes UTF-8.

---

## 🚀 Verwendung

Je nach Vorliebe kannst du entweder die fertige ausführbare Datei nutzen oder das Skript direkt über Python starten.

### Option A: Für Endanwender (`.exe`)
Wenn du das Programm aus einem GitHub-Release herunterlädst:
1. Starte die `Helden-Overhaul.exe`.
2. Ein Dateiauswahldialog öffnet sich.
3. Wähle deinen originalen Charakterbogen (`.html`) aus.
4. Falls der Charakter ein Elf ist, fragt dich das Programm in der Konsole, ob Zauber in elfischer Notation dargestellt werden sollen.
5. Fertig! Im selben Ordner findest du deine neue, moderne Datei.

### Option B: Für Entwickler & Power-User (`.py`)
Wenn du Python installiert hast, kannst du das Skript direkt über die Kommandozeile nutzen:

**1. Voraussetzungen:**
Du benötigst die Bibliothek `beautifulsoup4`. Installiere sie mit:
```bash
pip install beautifulsoup4
```

**2. Ausführung:**
Du kannst das Skript entweder ohne Argumente starten (öffnet einen Dialog) oder den Pfad direkt angeben:
```bash
# Mit Dateidialog
python Helden-Overhaul.py

# Mit direktem Pfad
python Helden-Overhaul.py "C:/Pfad/zu/deinem/Charakter.html"
```

---

## 🛠 Technische Details

Das Programm nutzt **Python** und **BeautifulSoup4**, um den DOM der HTML-Datei zu analysieren. Es injiziert:
- **Custom CSS:** Ein modernes Stylesheet für das visuelle Upgrade.
- **Vanilla JavaScript:** Ein mächtiges Skript für die Würfel-Logik, die Navigation und das Theme-Management. Es ist komplett autark und benötigt keine Internetverbindung (keine externen CDNs wie jQuery!).

### Funktionsweise der Würfel
Das Skript erkennt spezifische Klassen und Datenattribute (`data-probe`, `data-skill-value` etc.) innerhalb der HTML-Tabellen. Dadurch wird die Würfelfunktion "smart": Sie weiß genau, welcher Wert für die Probe relevant ist und wie die Differenz berechnet werden muss.
---
*Viel Spaß beim Würfeln und Abenteuern!* ⚔️
