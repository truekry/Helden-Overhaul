#!/usr/bin/env python3
"""
Helden-Overhaul.py

Modernisiert einen alten HTML-Charakterbogen, ohne die Charakterdaten
zu verändern.

Interaktive Würfel:
- Klick auf MU/KL/IN/CH/FF/GE/KO/KK: 1W20 gegen aktuellen Wert
- Klick auf Initiative: aktueller Wert + 1W6
- Klick auf Talent/Zauber: 3× W20 mit TaW/ZfW-Verrechnung
- Wiederholungsbutton, Light/Dark Mode
- Würfel-log

Aufruf:  python helde-overhaul.py MeinCharakter.html
Ausgabe: MeinCharakter_modern.html
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False


# ============================================================
# MODERNES CSS
# ============================================================

if getattr(sys, "frozen", False):
    CSS_DATEI = Path(sys.executable).resolve().parent / "heldenstyle.css"
else:
    CSS_DATEI = Path(__file__).resolve().parent / "heldenstyle.css"


def lade_modernes_css():
    """Lädt das externe CSS aus heldenstyle.css neben dem Script."""
    try:
        with open(CSS_DATEI, "r", encoding="utf-8") as datei:
            return datei.read()
    except FileNotFoundError:
        print(f"Fehler: CSS-Datei nicht gefunden: {CSS_DATEI}")
        print("Bitte lege eine heldenstyle.css neben Helden-Overhaul.py ab.")
        sys.exit(1)
    except UnicodeDecodeError as fehler:
        print("Fehler beim Lesen von heldenstyle.css als UTF-8:")
        print(fehler)
        sys.exit(1)
    except OSError as fehler:
        print(f"Fehler beim Lesen von heldenstyle.css: {fehler}")
        sys.exit(1)



# ============================================================
# JAVASCRIPT: NACHTMODUS + WÜRFEL
# ============================================================

THEME_AND_DICE_JAVASCRIPT = r"""
(function () {
  "use strict";

  var STORAGE_KEY = "charakterbogen-dark-mode";

  // Würfellog: absichtlich nur im JavaScript-Speicher.
  // Dadurch bleibt er nur so lange erhalten, wie diese Seite geöffnet ist.
  var ROLL_LOG = [];

  function rollDie(sides) {
    return Math.floor(Math.random() * sides) + 1;
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function signed(value) {
    return value > 0 ? "+" + value : String(value);
  }

  function setDarkMode(enabled, savePreference) {
    var body = document.body;
    var button = document.getElementById("theme-toggle");
    if (!body || !button) return;

    if (enabled) body.classList.add("dark-mode");
    else body.classList.remove("dark-mode");

    if (enabled) {
      button.textContent = "☀";
      button.setAttribute("aria-label", "Light Mode aktivieren");
      button.setAttribute("title", "Light Mode");
      button.setAttribute("aria-pressed", "true");
    } else {
      button.textContent = "☾";
      button.setAttribute("aria-label", "Dark Mode aktivieren");
      button.setAttribute("title", "Dark Mode");
      button.setAttribute("aria-pressed", "false");
    }

    if (savePreference) {
      try { localStorage.setItem(STORAGE_KEY, enabled ? "1" : "0"); }
      catch (error) {}
    }
  }

  function getSavedMode() {
    var saved = null;
    try { saved = localStorage.getItem(STORAGE_KEY); }
    catch (error) { saved = null; }

    if (saved === "1") return true;
    if (saved === "0") return false;

    try {
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
        return true;
      }
    } catch (error) {}
    return false;
  }

  function getRollTime() {
    var now = new Date();
    return String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0") + ":" + String(now.getSeconds()).padStart(2, "0");
  }

  // Jeder Wurf erzeugt genau EINEN Log-Eintrag.
  // Format: [Uhrzeit][Talent/Eigenschaft/Zauber][Wurf1/Wurf2/Wurf3][✓|X]
  function addRollLog(type, name, rolls, success) {
    ROLL_LOG.push({
      time: getRollTime(),
      type: type,
      name: name,
      rolls: rolls.map(function (value) { return Number(value); }),
      success: success
    });
  }

  function formatRollLogEntry(entry) {
    var status = entry.success === null ? "–" : (entry.success ? "✓" : "X");
    var category = entry.type + (entry.name ? ": " + entry.name : "");
    var rolls = entry.rolls.join("/");
    var statusClass = entry.success === null ? "neutral" : (entry.success ? "erfolg" : "misserfolg");

    // Absichtlich eine einzige, ungebrochene Textzeile.
    return '<div class="wuerfel-log-eintrag" title="' + escapeHtml(category) + '">' +
      '<span class="wuerfel-log-zeile">' +
        '<span class="wuerfel-log-zeit">[' + escapeHtml(entry.time) + ']</span>' +
        '<span class="wuerfel-log-art">[' + escapeHtml(category) + ']</span>' +
        '<span class="wuerfel-log-wuerfe">[' + escapeHtml(rolls) + ']</span>' +
        '<span class="wuerfel-log-status ' + statusClass + '">[' + status + ']</span>' +
      '</span>' +
    '</div>';
  }

  function showRollLog() {
    var entries = ROLL_LOG.slice().reverse();
    var content = entries.length
      ? entries.map(formatRollLogEntry).join("")
      : '<div class="wuerfel-log-leer">Noch keine Würfe in dieser Sitzung.</div>';

    var html =
      '<div class="wuerfel-log-titelzeile">' +
        '<div><h2>Würfellog</h2><p class="wuerfel-dialog-subtitle">Nur diese Browser-Sitzung · [Uhrzeit][Art][Wurf1/Wurf2/Wurf3][✓|X]</p></div>' +
        '<button type="button" class="wuerfel-log-leeren" data-action="clear-log">Log leeren</button>' +
      '</div>' +
      '<div class="wuerfel-log-liste">' + content + '</div>' +
      '<div class="wuerfel-buttons"><button type="button" class="wuerfel-button" data-action="close">Schließen</button></div>';

    showDialog(html);

    var close = document.querySelector('[data-action="close"]');
    var clear = document.querySelector('[data-action="clear-log"]');
    if (close) close.addEventListener("click", closeDialog);
    if (clear) clear.addEventListener("click", function () {
      ROLL_LOG.length = 0;
      showRollLog();
    });
  }

  function initRollLogButton() {
    var button = document.getElementById("roll-log-toggle");
    if (!button) return;
    button.addEventListener("click", showRollLog);
  }

  function closeDialog() {
    var overlay = document.querySelector(".wuerfel-overlay");
    if (overlay) overlay.remove();
  }

  function showDialog(html) {
    closeDialog();
    var overlay = document.createElement("div");
    overlay.className = "wuerfel-overlay";
    overlay.innerHTML =
      '<div class="wuerfel-dialog" role="dialog" aria-modal="true">' + html + '</div>';
    document.body.appendChild(overlay);

    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) closeDialog();
    });

    document.addEventListener("keydown", function escapeHandler(event) {
      if (event.key === "Escape") {
        closeDialog();
        document.removeEventListener("keydown", escapeHandler);
      }
    });
  }

  function showPropertyRoll(name, value) {
    var roll = rollDie(20);
    var difference = value - roll;
    var success = difference >= 0;
    addRollLog("Eigenschaft", name, [roll], success);
    var html =
      '<h2>' + escapeHtml(name) + '</h2>' +
      '<p class="wuerfel-dialog-subtitle">Eigenschaftsprobe mit 1W20</p>' +
      '<div class="wuerfel-einzel">' +
        '<div class="wuerfel-einzel-wurf">🎲 ' + roll + '</div>' +
        '<div class="wuerfel-einzel-rechnung">' +
          escapeHtml(name) + ': <strong>' + value + '</strong><br>' +
          'Wurf: <strong>' + roll + '</strong><br>' +
          'Differenz: <strong>' + signed(difference) + '</strong>' +
        '</div>' +
      '</div>' +
      '<div class="wuerfel-ergebnis ' + (success ? 'erfolg' : 'misserfolg') + '">' +
        (success ? '✓ Probe gelungen' : '✗ Probe misslungen') +
      '</div>' +
      '<div class="wuerfel-buttons">' +
        '<button type="button" class="wuerfel-button" data-action="close">Schließen</button>' +
        '<button type="button" class="wuerfel-button primary" data-action="reroll-property">Nochmal würfeln</button>' +
      '</div>';

    showDialog(html);

    var reroll = document.querySelector('[data-action="reroll-property"]');
    var close = document.querySelector('[data-action="close"]');
    if (reroll) reroll.addEventListener("click", function () { showPropertyRoll(name, value); });
    if (close) close.addEventListener("click", closeDialog);
  }

  function showInitiativeRoll(value) {
    var roll = rollDie(6);
    var total = value + roll;

    var html =
      '<h2>Initiative</h2>' +
      '<p class="wuerfel-dialog-subtitle">Initiative = aktueller Wert + 1W6</p>' +
      '<div class="wuerfel-einzel">' +
        '<div class="wuerfel-einzel-wurf">🎲 ' + roll + '</div>' +
        '<div class="wuerfel-einzel-rechnung">' +
          'Initiative: <strong>' + value + '</strong><br>' +
          '+ 1W6: <strong>' + roll + '</strong><br>' +
          'Ergebnis: <strong>' + total + '</strong>' +
        '</div>' +
      '</div>' +
      '<div class="wuerfel-ergebnis erfolg">⚔ Initiative: ' + total + '</div>' +
      '<div class="wuerfel-buttons">' +
        '<button type="button" class="wuerfel-button" data-action="close">Schließen</button>' +
        '<button type="button" class="wuerfel-button primary" data-action="reroll-initiative">Nochmal würfeln</button>' +
      '</div>';

    showDialog(html);

    var reroll = document.querySelector('[data-action="reroll-initiative"]');
    var close = document.querySelector('[data-action="close"]');
    if (reroll) reroll.addEventListener("click", function () { showInitiativeRoll(value); });
    if (close) close.addEventListener("click", closeDialog);
  }

  function parseProbe(text) {
    var cleaned = String(text || "")
      .toUpperCase()
      .replace(/Ä/g, "A")
      .replace(/Ö/g, "O")
      .replace(/Ü/g, "U");
    var matches = cleaned.match(/MU|KL|IN|CH|FF|GE|KO|KK/g);
    return matches ? matches.slice(0, 3) : [];
  }

  function getArmorBE() {
    var tables = document.querySelectorAll("table.zonenruestungen, table.ruestungen");
    for (var t = 0; t < tables.length; t++) {
      var rows = tables[t].querySelectorAll("tr");
      for (var r = 0; r < rows.length; r++) {
        var nameCell = rows[r].querySelector("td.name");
        if (!nameCell) continue;
        if (nameCell.textContent.replace(/\s+/g, " ").trim().toLowerCase() !== "gesamt") continue;
        var beCell = rows[r].querySelector("td.be");
        if (!beCell) continue;
        var n = parseInt(beCell.textContent.replace(/[^\d-]/g, ""), 10);
        if (Number.isFinite(n)) return n;
      }
    }
    return null;
  }

  function computeBEPenalty(beText, armorBE) {
    var t = String(beText || "").replace(/\s+/g, "").toUpperCase();
    if (!t) return 0;
    var m;
    if ((m = t.match(/^BEX(\d+)$/))) return armorBE * Number(m[1]);
    if ((m = t.match(/^BE-(\d+)$/))) return Math.max(0, armorBE - Number(m[1]));
    if ((m = t.match(/^BE\+(\d+)$/))) return armorBE + Number(m[1]);
    if (t === "BE") return armorBE;
    return armorBE;
  }

  function showSkillRoll(config) {
    var properties = window.__charakterEigenschaften || {};
    var probe = parseProbe(config.probe);

    if (probe.length !== 3) {
      showDialog(
        '<h2>' + escapeHtml(config.name) + '</h2>' +
        '<p>Die Probe konnte nicht eindeutig gelesen werden.</p>' +
        '<div class="wuerfel-buttons"><button type="button" class="wuerfel-button" data-action="close">Schließen</button></div>'
      );
      var closeError = document.querySelector('[data-action="close"]');
      if (closeError) closeError.addEventListener("click", closeDialog);
      return;
    }

    var remaining = Number(config.skillValue);
    var maxSkill = remaining;
    var results = [];

    for (var i = 0; i < probe.length; i++) {
      var abbreviation = probe[i];
      var value = Number(properties[abbreviation]);
      var roll = rollDie(20);
      var difference = value - roll;

      // Nur misslungene Teilproben verbrauchen TaW/ZfW
      if (difference < 0) remaining += difference;
      remaining = Math.min(maxSkill, remaining);

      results.push({ abbreviation: abbreviation, value: value, roll: roll, difference: difference });

    }

    var bePenalty = 0;
    var beNote = "";
    var nameNorm = String(config.name || "").toLowerCase()
      .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss");
    var isSinnenschaerfe = nameNorm.indexOf("sinnensch") === 0;
    if (config.be && !isSinnenschaerfe) {
      var armorBE = getArmorBE();
      if (armorBE !== null) {
        bePenalty = computeBEPenalty(config.be, armorBE);
        remaining -= bePenalty;
        beNote = "BE (" + escapeHtml(config.be) + ") aus Rüstung Gesamt " +
          armorBE + " → Abzug " + bePenalty;
      }
    }

    var success = remaining >= 0;
    addRollLog(config.kind || "Talent/Zauber", config.name,
      results.map(function (result) { return result.roll; }), success);

    var cards = results.map(function (result) {
      var cls = result.difference >= 0 ? "plus" : "minus";
      return '<div class="wuerfel-probe">' +
        '<div class="wuerfel-probe-eigenschaft">' + escapeHtml(result.abbreviation) + '</div>' +
        '<div class="wuerfel-probe-wurf">🎲 ' + result.roll + '</div>' +
        '<div class="wuerfel-probe-wert">Wert: ' + result.value + '</div>' +
        '<div class="wuerfel-probe-differenz ' + cls + '">Differenz: ' + signed(result.difference) + '</div>' +
      '</div>';
    }).join("");

    var html =
      '<h2>' + escapeHtml(config.name) + '</h2>' +
      '<p class="wuerfel-dialog-subtitle">Probe: ' + escapeHtml(probe.join(" / ")) + '</p>' +
      '<div class="wuerfel-proben">' + cards + '</div>' +
      '<div class="wuerfel-zusammenfassung">' +
        '<p><strong>' + escapeHtml(config.skillLabel) + ':</strong> ' + config.skillValue + '</p>' +
        (beNote ? '<p><strong>Behinderung:</strong> ' + beNote + '</p>' : '') +
        '<p><strong>Nach den drei Teilproben' + (bePenalty ? ' und BE' : '') + ':</strong> ' + signed(remaining) + '</p>' +
        '<p><small>Nur misslungene Teilproben verbrauchen TaW/ZfW. Erfolgreiche Teilproben geben keine Punkte zurück.</small></p>' +
      '</div>' +
      '<div class="wuerfel-ergebnis ' + (success ? 'erfolg' : 'misserfolg') + '">' +
        (success ? '✓ Probe gelungen' : '✗ Probe misslungen') +
      '</div>' +
      '<div class="wuerfel-buttons">' +
        '<button type="button" class="wuerfel-button" data-action="close">Schließen</button>' +
        '<button type="button" class="wuerfel-button primary" data-action="reroll-skill">Nochmal würfeln</button>' +
      '</div>';

    showDialog(html);

    var reroll = document.querySelector('[data-action="reroll-skill"]');
    var close = document.querySelector('[data-action="close"]');
    if (reroll) reroll.addEventListener("click", function () { showSkillRoll(config); });
    if (close) close.addEventListener("click", closeDialog);
  }

  function initDiceTargets() {
    var properties = {};

    document.querySelectorAll(".eigenschaft-wuerfel").forEach(function (row) {
      var key = row.getAttribute("data-eigenschaft");
      var value = Number(row.getAttribute("data-wert"));
      if (key && Number.isFinite(value)) properties[key] = value;

      row.setAttribute("tabindex", "0");
      row.setAttribute("role", "button");
      row.addEventListener("click", function () {
        showPropertyRoll(row.getAttribute("data-name"), Number(row.getAttribute("data-wert")));
      });
      row.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          showPropertyRoll(row.getAttribute("data-name"), Number(row.getAttribute("data-wert")));
        }
      });
    });

    window.__charakterEigenschaften = properties;

    document.querySelectorAll(".initiative-wuerfel").forEach(function (row) {
      row.setAttribute("tabindex", "0");
      row.setAttribute("role", "button");
      row.addEventListener("click", function () {
        showInitiativeRoll(Number(row.getAttribute("data-wert")));
      });
      row.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          showInitiativeRoll(Number(row.getAttribute("data-wert")));
        }
      });
    });

    document.querySelectorAll(".talent-wuerfel, .zauber-wuerfel").forEach(function (row) {
      row.setAttribute("tabindex", "0");
      row.setAttribute("role", "button");
      function rollFromRow() {
        showSkillRoll({
          name: row.getAttribute("data-name"),
          kind: row.classList.contains("zauber-wuerfel") ? "Zauber" : "Talent",
          probe: row.getAttribute("data-probe"),
          skillValue: Number(row.getAttribute("data-skill-value")),
          skillLabel: row.getAttribute("data-skill-label"),
          be: row.getAttribute("data-be") || ""
        });
      }
      row.addEventListener("click", rollFromRow);
      row.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          rollFromRow();
        }
      });
    });
  }

  function showFreeRoll(sides) {
    var roll = rollDie(sides);
    // Freie Würfe haben keine Probe. Das letzte Feld bleibt deshalb neutral.
    addRollLog("Freier Wurf", "1W" + sides, [roll], null);
    var html =
      '<h2>1W' + sides + '</h2>' +
      '<p class="wuerfel-dialog-subtitle">Freier Wurf</p>' +
      '<div class="wuerfel-einzel">' +
        '<div class="wuerfel-einzel-wurf">🎲 ' + roll + '</div>' +
        '<div class="wuerfel-einzel-rechnung">Ergebnis: <strong>' + roll + '</strong></div>' +
      '</div>' +
      '<div class="wuerfel-ergebnis erfolg">Ergebnis: ' + roll + '</div>' +
      '<div class="wuerfel-buttons">' +
        '<button type="button" class="wuerfel-button" data-action="close">Schließen</button>' +
        '<button type="button" class="wuerfel-button primary" data-action="reroll-free">Nochmal würfeln</button>' +
      '</div>';
    showDialog(html);
    var reroll = document.querySelector('[data-action="reroll-free"]');
    var close = document.querySelector('[data-action="close"]');
    if (reroll) reroll.addEventListener("click", function () { showFreeRoll(sides); });
    if (close) close.addEventListener("click", closeDialog);
  }

  function initFreeDice() {
    document.querySelectorAll(".nav-dice").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var sides = Number(btn.getAttribute("data-sides"));
        if (sides) showFreeRoll(sides);
      });
    });
  }

  function initTheme() {
    var body = document.body;
    var button = document.getElementById("theme-toggle");
    if (!body || !button) return;

    setDarkMode(getSavedMode(), false);
    button.addEventListener("click", function () {
      setDarkMode(!body.classList.contains("dark-mode"), true);
    });
  }

  function init() {
    initTheme();
    initDiceTargets();
    initFreeDice();
    initRollLogButton();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
"""


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def lade_html(dateipfad):
    """Lädt HTML-Datei (cp1252) und gibt BeautifulSoup-Objekt zurück."""
    try:
        with open(dateipfad, "r", encoding="cp1252") as datei:
            return BeautifulSoup(datei, "html.parser")
    except FileNotFoundError:
        print(f"Fehler: Datei nicht gefunden: {dateipfad}")
        sys.exit(1)
    except UnicodeDecodeError as fehler:
        print("Fehler beim Lesen der Datei als Windows-1252/Cp1252:")
        print(fehler)
        sys.exit(1)
    except OSError as fehler:
        print(f"Fehler beim Lesen der Datei: {fehler}")
        sys.exit(1)


def entferne_altes_css(soup):
    """Entfernt vorhandene <style>-Tags und held.css-Links."""
    for style in soup.find_all("style"):
        style.decompose()

    for link in soup.find_all("link"):
        rel = link.get("rel", [])
        if isinstance(rel, str):
            rel = [rel]
        rel_lower = {str(value).lower() for value in rel}
        href = str(link.get("href", "")).lower()

        if "stylesheet" in rel_lower and (
            "held.css" in href or link.get("title") == "Benutzer Stil"
        ):
            link.decompose()


def fuege_modernes_css_ein(soup):
    """Verknüpft die externe heldenstyle.css im <head>."""
    # CSS-Datei beim Konvertieren prüfen/einlesen, damit ein fehlendes oder
    # beschädigtes Benutzer-Stylesheet frühzeitig gemeldet wird.
    lade_modernes_css()

    head = soup.head
    if head is None:
        head = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head)
        else:
            soup.insert(0, head)

    link = soup.new_tag("link")
    link["rel"] = "stylesheet"
    link["type"] = "text/css"
    link["href"] = "heldenstyle.css"
    link["title"] = "Benutzer Stil"
    head.append(link)


def kopiere_modernes_css(ausgabedatei):
    """Legt heldenstyle.css neben der erzeugten HTML-Datei ab."""
    ziel = ausgabedatei.parent / "heldenstyle.css"
    try:
        if CSS_DATEI.resolve() != ziel.resolve():
            shutil.copy2(CSS_DATEI, ziel)
    except OSError as fehler:
        print(f"Fehler beim Kopieren von heldenstyle.css: {fehler}")
        sys.exit(1)


def erzeuge_id(text, nummer):
    """Erzeugt eine gültige HTML-ID aus einem Bereichsnamen."""
    text = text.lower()
    for alt, neu in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        text = text.replace(alt, neu)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "bereich"
    return f"section-{text}-{nummer}"


def markiere_hauptbereiche(soup):
    """Markiert Haupt-Tabellen mit IDs und gibt Liste der Bereiche zurück."""
    bereiche = []
    if not soup.body:
        return bereiche

    for element in soup.body.find_all(recursive=False):
        if element.name != "table":
            continue
        titel = element.select_one("th.titel")
        if titel is None:
            continue
        name = titel.get_text(" ", strip=True)
        if not name:
            continue

        klassen = list(element.get("class", []))
        if "modern-section" not in klassen:
            klassen.append("modern-section")
        element["class"] = klassen
        section_id = erzeuge_id(name, len(bereiche) + 1)
        element["id"] = section_id
        bereiche.append((section_id, name))

    return bereiche


def normalisiere_eigenschaft(text):
    """Liefert die DSA-Kurzbezeichnung für eine Eigenschaft."""
    text = re.sub(r"\s+", " ", text.strip()).lower()
    return {
        "mut": "MU", "klugheit": "KL", "intuition": "IN", "charisma": "CH",
        "fingerfertigkeit": "FF", "gewandtheit": "GE", "konstitution": "KO",
        "körperkraft": "KK", "koerperkraft": "KK",
    }.get(text)


def parse_zahl(text):
    """Extrahiert die erste ganze Zahl aus einem Text."""
    match = re.search(r"-?\d+", text.replace("\xa0", " "))
    return int(match.group(0)) if match else None


def markiere_eigenschaften_als_wuerfelziele(soup):
    """Markiert Eigenschaftszeilen als klickbare Würfelziele."""
    table = soup.select_one("table.eigenschaften")
    if table is None:
        return 0

    anzahl = 0
    for row in table.find_all("tr"):
        name_cell = row.find("td", class_="name")
        aktuell_cell = row.find("td", class_="aktuell")
        if name_cell is None or aktuell_cell is None:
            continue

        name = name_cell.get_text(" ", strip=True)
        kurz = normalisiere_eigenschaft(name)
        wert = parse_zahl(aktuell_cell.get_text(" ", strip=True))
        if kurz is None or wert is None:
            continue

        classes = list(row.get("class", []))
        if "wuerfelziel" not in classes:
            classes.append("wuerfelziel")
        if "eigenschaft-wuerfel" not in classes:
            classes.append("eigenschaft-wuerfel")
        row["class"] = classes
        row["data-eigenschaft"] = kurz
        row["data-name"] = name
        row["data-wert"] = str(wert)
        row["title"] = f"{name} würfeln (1W20 gegen {wert})"
        anzahl += 1

    return anzahl


def markiere_initiative_als_wuerfelziel(soup):
    """Markiert die Initiative-Zeile als Würfelziel."""
    for table in soup.select("table.basiswerte"):
        for row in table.find_all("tr"):
            name_cell = row.find("td", class_="name")
            aktuell_cell = row.find("td", class_="aktuell")
            if name_cell is None or aktuell_cell is None:
                continue
            if name_cell.get_text(" ", strip=True).casefold() != "initiative":
                continue

            wert = parse_zahl(aktuell_cell.get_text(" ", strip=True))
            if wert is None:
                continue

            classes = list(row.get("class", []))
            if "wuerfelziel" not in classes:
                classes.append("wuerfelziel")
            if "initiative-wuerfel" not in classes:
                classes.append("initiative-wuerfel")
            row["class"] = classes
            row["data-wert"] = str(wert)
            row["title"] = f"Initiative würfeln: {wert} + 1W6"
            return 1
    return 0


def probe_kurztext(text):
    """Normalisiert z.B. '(MU/IN/GE)' zu 'MU/IN/GE'."""
    text = re.sub(r"\s+", "", text.upper())
    match = re.search(
        r"\(?((?:MU|KL|IN|CH|FF|GE|KO|KK)(?:/(?:MU|KL|IN|CH|FF|GE|KO|KK)){2})\)?",
        text,
    )
    return match.group(1) if match else ""


def markiere_talente_und_zauber(soup):
    """Markiert Talent- und Zauberzeilen als Würfelziele. Gibt (talente, zauber) zurück."""
    talente = 0
    zauber = 0

    for table in soup.select("table.talentgruppe"):
        for row in table.find_all("tr"):
            name_cell = row.find("td", class_="name", recursive=False)
            probe_cell = row.find("td", class_="probe", recursive=False)
            taw_cell = row.find("td", class_="taw", recursive=False)
            if name_cell is None or probe_cell is None or taw_cell is None:
                continue

            name = name_cell.get_text(" ", strip=True)
            probe = probe_kurztext(probe_cell.get_text(" ", strip=True))
            taw = parse_zahl(taw_cell.get_text(" ", strip=True))
            if not name or not probe or taw is None:
                continue

            be_cell = row.find("td", class_="be", recursive=False)
            be_text = ""
            if be_cell is not None:
                be_text = be_cell.get_text(" ", strip=True).replace("\xa0", "").strip()

            classes = list(row.get("class", []))
            if "wuerfelziel" not in classes:
                classes.append("wuerfelziel")
            if "talent-wuerfel" not in classes:
                classes.append("talent-wuerfel")
            row["class"] = classes
            row["data-name"] = name
            row["data-probe"] = probe
            row["data-skill-value"] = str(taw)
            row["data-skill-label"] = "TaW"
            if be_text:
                row["data-be"] = be_text
            title = f"{name}: Probe {probe}, TaW {taw}"
            if be_text:
                title += f", BE {be_text}"
            row["title"] = title
            talente += 1

    for table in soup.select("table.zauber"):
        if table.find("table", class_="zauber") is not None:
            continue  # äußere Tabelle überspringen

        for row in table.find_all("tr"):
            name_cell = row.find("td", class_="name", recursive=False)
            probe_cell = row.find("td", class_="probe", recursive=False)
            zfw_cell = row.find("td", class_="zfw", recursive=False)
            if name_cell is None or probe_cell is None or zfw_cell is None:
                continue

            name = name_cell.get_text(" ", strip=True)
            probe = probe_kurztext(probe_cell.get_text(" ", strip=True))
            zfw = parse_zahl(zfw_cell.get_text(" ", strip=True))
            if not name or not probe or zfw is None:
                continue

            classes = list(row.get("class", []))
            if "wuerfelziel" not in classes:
                classes.append("wuerfelziel")
            if "zauber-wuerfel" not in classes:
                classes.append("zauber-wuerfel")
            row["class"] = classes
            row["data-name"] = name
            row["data-probe"] = probe
            row["data-skill-value"] = str(zfw)
            row["data-skill-label"] = "ZfW"
            row["title"] = f"{name}: Probe {probe}, ZfW {zfw}"
            zauber += 1

    return talente, zauber


def markiere_wuerfelziele(soup):
    """Markiert alle Würfelziele und gibt Statistik zurück."""
    eigenschaften = markiere_eigenschaften_als_wuerfelziele(soup)
    initiative = markiere_initiative_als_wuerfelziel(soup)
    talente, zauber = markiere_talente_und_zauber(soup)
    return eigenschaften, initiative, talente, zauber


def erstelle_navigation(soup, bereiche):
    """Erstellt sticky Navigationsleiste mit Theme-Toggle und Freiwürfeln."""
    if not bereiche:
        return

    nav = soup.new_tag("nav")
    nav["class"] = "modern-nav"
    nav["aria-label"] = "Charakterbogen Navigation"

    button = soup.new_tag("button")
    button["type"] = "button"
    button["id"] = "theme-toggle"
    button["aria-label"] = "Dark Mode aktivieren"
    button["title"] = "Dark Mode"
    button["aria-pressed"] = "false"
    button.string = "☾"
    nav.append(button)

    for section_id, name in bereiche:
        display = "Basiswerte" if name == "Eigenschaften und Basiswerte" else name
        link = soup.new_tag("a", href=f"#{section_id}")
        link.string = display
        nav.append(link)

    for sides, label in ((6, "🎲6"), (20, "🎲20")):
        btn = soup.new_tag("button")
        btn["type"] = "button"
        btn["class"] = "nav-dice"
        btn["data-sides"] = str(sides)
        btn["title"] = f"1W{sides} würfeln"
        btn["aria-label"] = f"1W{sides} würfeln"
        btn.string = label
        nav.append(btn)

    # Der Würfellog sitzt unabhängig vom Scrollen immer unten rechts.
    log_button = soup.new_tag("button")
    log_button["type"] = "button"
    log_button["id"] = "roll-log-toggle"
    log_button["class"] = "roll-log-toggle"
    log_button["title"] = "Würfellog öffnen"
    log_button["aria-label"] = "Würfellog öffnen"
    log_button.string = "📜"

    header = soup.find("h1", class_="heldenname")
    if header:
        header.insert_after(nav)
    elif soup.body:
        soup.body.insert(0, nav)

    if soup.body:
        soup.body.append(log_button)


def fuege_theme_javascript_ein(soup):
    """Fügt Theme- und Würfel-JavaScript am Ende des Body ein."""
    if not soup.body:
        return
    script = soup.new_tag("script")
    script["type"] = "text/javascript"
    script["id"] = "modern-theme-and-dice-script"
    script.string = "\n" + THEME_AND_DICE_JAVASCRIPT + "\n"
    soup.body.append(script)


def aktualisiere_encoding(soup):
    """Setzt alle Meta-Charset-Angaben auf UTF-8."""
    for meta in soup.find_all("meta"):
        if meta.get("charset"):
            meta["charset"] = "UTF-8"
        content = meta.get("content", "")
        if "charset=" in content.lower():
            meta["content"] = re.sub(
                r"charset\s*=\s*[^;\s]+",
                "charset=UTF-8",
                content,
                flags=re.IGNORECASE,
            )


def entferne_leere_elemente(soup):
    """Entfernt leere Tabellenzeilen und Tabellen."""
    for tr in soup.find_all("tr"):
        if not tr.get_text(strip=True) and not tr.find("img"):
            tr.decompose()
            continue
        cells = tr.find_all(["td", "th"])
        if cells and all(
            not cell.get_text(strip=True) and not cell.find("img") for cell in cells
        ):
            tr.decompose()

    for table in soup.find_all("table"):
        if not table.get_text(strip=True) and not table.find("img"):
            table.decompose()


def erstelle_ausgabedatei(dateipfad):
    """Erzeugt den Ausgabepfad mit Suffix _modern."""
    return dateipfad.with_name(f"{dateipfad.stem}_modern{dateipfad.suffix}")


def speichere_html(soup, ausgabedatei):
    """Speichert das HTML als UTF-8 und ersetzt alte Encoding-Angaben."""
    try:
        html = soup.encode("utf-8", formatter="html").decode("utf-8")

        for pattern in (
            r'encoding\s*=\s*["\']?cp1252["\']?',
            r'encoding\s*=\s*["\']?windows-1252["\']?',
            r'charset\s*=\s*["\']?cp1252["\']?',
            r'charset\s*=\s*["\']?windows-1252["\']?',
        ):
            html = re.sub(pattern, 'encoding="UTF-8"' if "encoding" in pattern else 'charset=UTF-8', html, flags=re.IGNORECASE)

        if not re.match(r"\s*<!doctype\s+html>", html, flags=re.IGNORECASE):
            html = "<!doctype html>\n" + html

        with open(ausgabedatei, "w", encoding="utf-8", newline="") as datei:
            datei.write(html)
    except OSError as fehler:
        print(f"Fehler beim Speichern: {fehler}")
        sys.exit(1)


def hole_eigenschaften(soup):
    """Liest aktuelle Eigenschaftswerte aus table.eigenschaften."""
    props = {}
    table = soup.select_one("table.eigenschaften")
    if table is None:
        return props
    mapping = {
        "mut": "MU", "klugheit": "KL", "intuition": "IN", "charisma": "CH",
        "fingerfertigkeit": "FF", "gewandtheit": "GE", "konstitution": "KO",
        "körperkraft": "KK", "koerperkraft": "KK",
    }
    for row in table.find_all("tr"):
        name_cell = row.find("td", class_="name")
        aktuell_cell = row.find("td", class_="aktuell")
        if name_cell is None or aktuell_cell is None:
            continue
        name = name_cell.get_text(" ", strip=True).casefold()
        kurz = mapping.get(name)
        if not kurz:
            continue
        wert = parse_zahl(aktuell_cell.get_text(" ", strip=True))
        if wert is not None:
            props[kurz] = wert
    return props


def wende_elf_probe_an(probe, properties):
    """Ersetzt höchstens einmal KL durch IN, wenn IN > KL und nicht 3× IN."""
    kl = properties.get("KL")
    inn = properties.get("IN")
    if kl is None or inn is None or not (inn > kl):
        return probe, False
    parts = probe.split("/")
    in_count = sum(1 for p in parts if p == "IN")
    changed = False
    for i, p in enumerate(parts):
        if p != "KL":
            continue
        if in_count + 1 >= 3:
            break
        parts[i] = "IN"
        changed = True
        break
    return "/".join(parts), changed


def aktualisiere_zauber_proben_elf(soup):
    """Schreibt geänderte Proben (elfische Representation) in Zaubertabelle und data-probe."""
    properties = hole_eigenschaften(soup)
    if not properties:
        return 0
    anzahl = 0
    for table in soup.select("table.zauber"):
        if table.find("table", class_="zauber") is not None:
            continue
        for row in table.find_all("tr"):
            probe_cell = row.find("td", class_="probe", recursive=False)
            if probe_cell is None:
                continue
            original = probe_kurztext(probe_cell.get_text(" ", strip=True))
            if not original:
                continue
            neu, changed = wende_elf_probe_an(original, properties)
            if not changed:
                continue
            text = probe_cell.get_text()
            if "(" in text and ")" in text:
                probe_cell.clear()
                probe_cell.append(f" ({neu})")
            else:
                probe_cell.clear()
                probe_cell.append(neu)
            if row.get("data-probe") is not None:
                row["data-probe"] = neu
            if row.get("title"):
                row["title"] = row["title"].replace(f"Probe {original}", f"Probe {neu}")
            anzahl += 1
    return anzahl


def ist_elf_rasse(soup):
    """Prüft, ob die Rasse des Helden 'Elf' enthält."""
    for table in soup.select("table.heldendaten, table.personendaten"):
        for row in table.find_all("tr"):
            name_cell = row.find("td", class_="name")
            entry_cell = row.find("td", class_="eintrag")
            if name_cell is None or entry_cell is None:
                continue
            if name_cell.get_text(" ", strip=True).casefold() != "rasse":
                continue
            return "elf" in entry_cell.get_text(" ", strip=True).casefold()
    return False


def frage_elf_representation(soup):
    """Fragt interaktiv, ob elfische Representation für Zauber angewendet werden soll."""
    if not ist_elf_rasse(soup):
        return False
    print()
    print("Elfen-Rasse erkannt.")
    antwort = input(
        "Zauber standardmäßig in elfischer Representation wirken? [j/y/n]: "
    ).strip().lower()
    return antwort[:1] in ("j", "y")


def waehle_html_datei():
    """Öffnet Dateiauswahldialog für HTML-Datei (Doppelklick-Modus)."""
    if not HAS_TK:
        print("Fehler: Keine GUI verfügbar. Bitte Datei als Argument übergeben.")
        sys.exit(1)
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    pfad = filedialog.askopenfilename(
        title="Helden-Charakterbogen wählen",
        filetypes=[("HTML-Dateien", "*.html;*.htm"), ("Alle Dateien", "*.*")],
    )
    root.destroy()
    if not pfad:
        sys.exit(0)
    return pfad


def parse_argumente():
    """Parst Kommandozeilenargumente oder öffnet Dateidialog."""
    parser = argparse.ArgumentParser(
        description=(
            "Modernisiert den alten HTML-Charakterbogen der Helden-Software (Layout, Dark Mode, "
            "interaktive Würfel), ohne die Charakterdaten zu verändern."
        ),
        epilog="Beispiel: Helden-Overhaul.exe MeinCharakter.html",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "datei",
        nargs="?",
        default=None,
        help="Pfad zur originalen HTML-Datei",
    )
    args = parser.parse_args()
    if args.datei is None:
        args.datei = waehle_html_datei()
    return args


# ============================================================
# MAIN
# ============================================================

def main():
    """Hauptablauf: Laden, modernisieren, speichern."""
    args = parse_argumente()
    eingabedatei = Path(args.datei)

    if not eingabedatei.exists():
        print(f"Fehler: Datei existiert nicht: {eingabedatei}")
        sys.exit(1)

    print()
    print("=" * 65)
    print("Helden-Overhaul: Modernisierung des Charakterbogens")
    print("=" * 65)
    print(f"Eingabe: {eingabedatei}")

    soup = lade_html(eingabedatei)

    entferne_altes_css(soup)
    fuege_modernes_css_ein(soup)

    bereiche = markiere_hauptbereiche(soup)
    entferne_leere_elemente(soup)

    wuerfelstatistik = markiere_wuerfelziele(soup)

    elf_rep = frage_elf_representation(soup)
    elf_proben = 0
    if elf_rep:
        elf_proben = aktualisiere_zauber_proben_elf(soup)

    erstelle_navigation(soup, bereiche)
    fuege_theme_javascript_ein(soup)
    aktualisiere_encoding(soup)

    ausgabedatei = erstelle_ausgabedatei(eingabedatei)
    kopiere_modernes_css(ausgabedatei)
    speichere_html(soup, ausgabedatei)

    eigenschaften, initiative, talente, zauber = wuerfelstatistik

    print()
    print(f"Hauptbereiche gefunden: {len(bereiche)}")
    print(f"Eigenschaften würfelbar: {eigenschaften}")
    print(f"Initiative würfelbar:    {initiative}")
    print(f"Talente würfelbar:       {talente}")
    print(f"Zauber würfelbar:        {zauber}")
    print()
    print(f"Ausgabe: {ausgabedatei}")
    print(f"Stylesheet: {ausgabedatei.parent / 'heldenstyle.css'}")
    print()
    print("Das Original wurde nicht überschrieben.")
    print("Alle Charakterdaten bleiben erhalten.")
    print("Ausgabeformat: UTF-8")
    print("Nachtmodus: aktiviert")
    print("Würfelfunktion: aktiviert")
    print(f"Elfische Representation: {'ja' if elf_rep else 'nein'}")
    if elf_rep:
        print(f"Zauber-Proben angepasst: {elf_proben}")
    print("Farbschema: benutzerdefiniertes Farbschema")
    print()
    print("Fertig!")


if __name__ == "__main__":
    main()
