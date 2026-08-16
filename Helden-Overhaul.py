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

Aufruf:  python helden-overhaul.py MeinCharakter.html
Ausgabe: MeinCharakter_modern.html
"""

import argparse
import re
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

MODERN_CSS = r"""
:root {
  --bg:#eef1f5;
  --surface:#fff;
  --soft:#f7f8fa;
  --text:#202733;
  --muted:#667085;
  --heading:#172033;
  --accent:#7b2f2f;
  --accent-dark:#542020;
  --accent-light:#f4e7e7;
  --border:#d9dee7;
  --radius:14px;
  --shadow:0 8px 24px rgba(31,41,55,.08);
  --max:1500px;
}

body.dark-mode {
  --bg:#12141a;
  --surface:#1e2128;
  --soft:#2a2e37;
  --text:#e2e8f0;
  --muted:#94a3b8;
  --heading:#f8fafc;
  --accent:#e55353;
  --accent-dark:#991b1b;
  --accent-light:#331a1a;
  --border:#334155;
  --shadow:0 8px 24px rgba(0,0,0,.4);
}

* { box-sizing:border-box; }
html { scroll-behavior:smooth; }

body {
  margin:0;
  padding:0 20px 50px;
  background:
    radial-gradient(circle at top left, rgba(123,47,47,.07), transparent 32rem),
    var(--bg);
  color:var(--text);
  font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:15px;
  line-height:1.45;
  transition:background .3s ease,color .3s ease;
}

body > table {
  width:min(100%,var(--max));
  margin:0 auto 18px;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:var(--radius);
  box-shadow:var(--shadow);
  border-collapse:separate;
  border-spacing:0;
  overflow:hidden;
  transition:background .3s ease,border-color .3s ease,box-shadow .3s ease;
}

.heldenname {
  width:min(100%,var(--max));
  margin:28px auto 20px;
  padding:28px 30px;
  color:#fff;
  background:linear-gradient(135deg,var(--accent-dark),var(--accent));
  border-radius:18px;
  box-shadow:0 12px 30px rgba(84,32,32,.22);
  font-size:clamp(2rem,5vw,4rem);
  font-weight:750;
  line-height:1.05;
  letter-spacing:-.035em;
  text-align:left;
}

.titel {
  display:block;
  padding:13px 17px;
  color:var(--heading);
  background:linear-gradient(90deg,var(--accent-light),var(--surface));
  border-bottom:1px solid var(--border);
  font-size:1.08rem;
  font-weight:750;
  text-align:left;
}

body > table > tbody > tr > td { padding:16px; }

body table table {
  width:100%;
  margin:0;
  border-collapse:collapse;
  border-spacing:0;
  background:transparent;
}

body table table th {
  padding:9px 10px;
  color:var(--muted);
  background:var(--soft);
  border-bottom:1px solid var(--border);
  font-size:.78rem;
  font-weight:750;
  text-transform:uppercase;
}

body table table td {
  padding:8px 10px;
  border-bottom:1px solid var(--border);
  vertical-align:middle;
}

body > table > tbody > tr:nth-child(even) td { background:rgba(247,248,250,.5); }
body.dark-mode > table > tbody > tr:nth-child(even) td { background:rgba(255,255,255,.03); }

.name { color:var(--heading); font-weight:650; }
.aktuell { font-weight:750; }
.taw,.zfw { min-width:3em; color:var(--accent); font-weight:800; text-align:right; }
.eigenschaften td.aktuell { color:var(--accent); font-size:1.08rem; font-weight:800; }
.eigenschaften td.modifikator { color:var(--muted); }

.talentgruppe td.name { color:var(--heading); font-weight:650; }
.talentgruppe .probe { color:var(--muted); }
.eig-mittel { color:var(--accent); font-weight:800; text-align:center; white-space:nowrap; }
.zauber .name { color:var(--heading); font-weight:650; }
.zauber .merkmale { color:var(--muted); text-align:left; }
.nkwaffen td.name,.fkwaffen td.name,.schilde td.name { color:var(--heading); font-weight:650; }
.beschreibung .eintrag { min-width:8em; }
.persoenliches .name,.umfeld .name { white-space:nowrap; }

img { max-width:100%; height:auto; border-radius:8px; }
a { color:var(--accent); text-decoration-thickness:1px; text-underline-offset:2px; }
a:hover { color:var(--accent-dark); }

.talente > tbody > tr > td { vertical-align:top !important; }
.talente .links_innen,
.talente .rechts_innen {
  margin-top:0 !important;
  padding-top:0 !important;
  position:static !important;
  top:auto !important;
  bottom:auto !important;
  float:none !important;
  vertical-align:top !important;
}
.talente table.rechts_innen,
.talente .rechts_innen table { margin-top:0 !important; }

.wuerfelziel {
  cursor:pointer;
  transition:background .15s ease,box-shadow .15s ease,transform .1s ease;
}
.wuerfelziel:hover > td {
  background:var(--accent-light) !important;
  box-shadow:inset 0 0 0 9999px var(--accent-light);
}
.wuerfelziel:active { transform:scale(.995); }
.wuerfelziel:focus-visible {
  outline:3px solid rgba(123,47,47,.35);
  outline-offset:-2px;
}
.eigenschaft-wuerfel .aktuell,
.initiative-wuerfel .aktuell { cursor:pointer; }

.wuerfel-overlay {
  position:fixed;
  inset:0;
  z-index:2000;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:20px;
  background:rgba(15,23,42,.58);
  backdrop-filter:blur(5px);
}
.wuerfel-dialog {
  width:min(720px,100%);
  max-height:min(90vh,900px);
  overflow:auto;
  padding:24px;
  color:var(--text);
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:18px;
  box-shadow:0 24px 70px rgba(0,0,0,.3);
}
.wuerfel-dialog h2 { margin:0 0 5px; color:var(--heading); font-size:1.5rem; }
.wuerfel-dialog-subtitle { margin:0 0 20px; color:var(--muted); }
.wuerfel-proben {
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:12px;
  margin:18px 0;
}
.wuerfel-probe {
  padding:15px 12px;
  text-align:center;
  background:var(--soft);
  border:1px solid var(--border);
  border-radius:12px;
}
.wuerfel-probe-eigenschaft { color:var(--muted); font-size:.82rem; font-weight:700; }
.wuerfel-probe-wurf {
  margin:4px 0;
  color:var(--accent);
  font-size:2rem;
  font-weight:850;
  line-height:1;
}
.wuerfel-probe-wert { font-weight:750; }
.wuerfel-probe-differenz { margin-top:5px; font-weight:800; }
.wuerfel-probe-differenz.plus { color:#18794e; }
.wuerfel-probe-differenz.minus { color:#b42318; }
body.dark-mode .wuerfel-probe-differenz.plus { color:#6ce0a6; }
body.dark-mode .wuerfel-probe-differenz.minus { color:#ff8c8c; }

.wuerfel-zusammenfassung {
  margin:16px 0;
  padding:14px 16px;
  background:var(--soft);
  border:1px solid var(--border);
  border-radius:12px;
}
.wuerfel-zusammenfassung p { margin:5px 0; }
.wuerfel-ergebnis {
  margin:18px 0;
  padding:15px;
  border-radius:12px;
  font-size:1.15rem;
  font-weight:800;
  text-align:center;
}
.wuerfel-ergebnis.erfolg { color:#166534; background:#dcfce7; border:1px solid #86efac; }
.wuerfel-ergebnis.misserfolg { color:#991b1b; background:#fee2e2; border:1px solid #fca5a5; }
body.dark-mode .wuerfel-ergebnis.erfolg { color:#bbf7d0; background:#143a27; border-color:#27633f; }
body.dark-mode .wuerfel-ergebnis.misserfolg { color:#fecaca; background:#451b1b; border-color:#7f3030; }

.wuerfel-buttons {
  display:flex;
  justify-content:flex-end;
  gap:9px;
  flex-wrap:wrap;
  margin-top:18px;
}
.wuerfel-button {
  padding:9px 14px;
  color:var(--text);
  background:var(--soft);
  border:1px solid var(--border);
  border-radius:9px;
  cursor:pointer;
  font:inherit;
  font-weight:700;
}
.wuerfel-button.primary { color:#fff; background:var(--accent); border-color:var(--accent); }
.wuerfel-button:hover { filter:brightness(.97); }

.wuerfel-einzel {
  display:flex;
  align-items:center;
  justify-content:center;
  gap:18px;
  margin:20px 0;
  padding:24px;
  background:var(--soft);
  border:1px solid var(--border);
  border-radius:14px;
}
.wuerfel-einzel-wurf {
  color:var(--accent);
  font-size:3rem;
  font-weight:900;
  line-height:1;
}
.wuerfel-einzel-rechnung { font-size:1.1rem; }
.wuerfel-einzel-rechnung strong { color:var(--accent); }

@media (max-width:900px) {
  body > table > tbody > tr > td:not(.beschreibung td) { display:block; width:100%; }
  .beschreibung table { display:table !important; }
  .beschreibung table tr { display:table-row !important; }
  .beschreibung table td { display:table-cell !important; }
}
@media (max-width:600px) {
  body { padding:0 7px 30px; font-size:14px; }
  .heldenname { margin-top:8px; margin-bottom:10px; padding:20px; border-radius:13px; font-size:2rem; }
  .modern-nav { top:5px; margin-bottom:10px; border-radius:9px; }
  #theme-toggle { width:34px; height:32px; font-size:19px; }
  body > table { margin-bottom:10px; border-radius:10px; }
  .titel { padding:11px 13px; font-size:1rem; }
  body > table > tbody > tr > td { padding:8px; }
  body table table th,body table table td { padding:7px 8px; }
  .wuerfel-proben { grid-template-columns:1fr; }
  .wuerfel-dialog { padding:17px; }
}
@media print {
  .modern-nav,.wuerfel-overlay { display:none !important; }
  body { background:#fff; color:#000; }
  body > table { box-shadow:none; }
  .heldenname { color:#000; background:#fff; border:2px solid #000; box-shadow:none; }
  .titel { color:#000; background:#eee; }
}

.modern-nav {
  position:sticky;
  top:12px;
  z-index:1000;
  width:min(100%,var(--max));
  margin:0 auto 20px;
  padding:8px;
  display:flex;
  gap:7px;
  align-items:center;
  overflow-x:auto;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:12px;
  box-shadow:0 6px 20px rgba(31,41,55,.09);
  backdrop-filter:blur(12px);
  scrollbar-width:thin;
}
.modern-nav a {
  flex:0 0 auto;
  display:block;
  padding:7px 11px;
  color:var(--muted);
  background:var(--soft);
  border:1px solid var(--border);
  border-radius:8px;
  font-size:.82rem;
  font-weight:650;
  text-decoration:none;
  white-space:nowrap;
}
.modern-nav a:hover { color:#fff; background:var(--accent); border-color:var(--accent); }

#theme-toggle {
  order:-1;
  flex:0 0 auto;
  width:36px;
  height:34px;
  padding:0;
  display:flex;
  align-items:center;
  justify-content:center;
  color:var(--muted);
  background:var(--soft);
  border:1px solid var(--border);
  border-radius:8px;
  cursor:pointer;
  font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:20px;
  line-height:1;
  text-decoration:none !important;
}
#theme-toggle:hover { color:#fff; background:var(--accent); border-color:var(--accent); }
#theme-toggle:active { transform:scale(.96); }
#theme-toggle:focus-visible { outline:3px solid rgba(123,47,47,.35); outline-offset:2px; }

.nav-dice {
  flex:0 0 auto;
  margin-left:4px;
  padding:7px 11px;
  color:var(--muted);
  background:var(--soft);
  border:1px solid var(--border);
  border-radius:8px;
  cursor:pointer;
  font:inherit;
  font-size:.82rem;
  font-weight:650;
  white-space:nowrap;
}
.nav-dice:first-of-type { margin-left:auto; }
.nav-dice:hover { color:#fff; background:var(--accent); border-color:var(--accent); }
.nav-dice:active { transform:scale(.96); }
.nav-dice:focus-visible { outline:3px solid rgba(123,47,47,.35); outline-offset:2px; }
"""


# ============================================================
# JAVASCRIPT: NACHTMODUS + WÜRFEL
# ============================================================

THEME_AND_DICE_JAVASCRIPT = r"""
(function () {
  "use strict";

  var STORAGE_KEY = "charakterbogen-dark-mode";

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
    """Fügt modernes CSS in den <head> ein."""
    head = soup.head
    if head is None:
        head = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head)
        else:
            soup.insert(0, head)

    style = soup.new_tag("style")
    style["type"] = "text/css"
    style["id"] = "modern-character-sheet-style"
    style.string = MODERN_CSS
    head.append(style)


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

    header = soup.find("h1", class_="heldenname")
    if header:
        header.insert_after(nav)
    elif soup.body:
        soup.body.insert(0, nav)


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
