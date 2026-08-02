# voigt-antons.de — persönliche Website

Statische Website ohne Build-Kette, ohne Framework, ohne Abhängigkeiten. Direkt auf GitHub Pages
lauffähig. Ein einziges optionales Python-Skript generiert die Publikations-Detailseiten.

---

## Struktur

```
/
├── index.html                  Startseite
├── 404.html                    Fehlerseite (GitHub Pages nutzt sie automatisch)
├── .nojekyll                   verhindert Jekyll-Verarbeitung
├── robots.txt
├── sitemap.xml                 generiert, 251 URLs
│
├── assets/
│   ├── style.css               gemeinsames Stylesheet (Light-first + Dark-Toggle)
│   └── main.js                 Theme-Toggle, Mobile-Nav, Scroll-Reveal
│
├── data/
│   ├── publications.json       232 Einträge — Quelle für alles Publikationsbezogene
│   ├── posts.json              generiert aus content/posts/
│   └── redirects.json          alte → neue Publikations-URLs
│
├── content/posts/*.md          5 Blogbeiträge als Markdown (Quelldateien)
│
├── research/index.html         5 Forschungslinien ausführlich
├── projects/index.html         Fördertabelle (18 Zeilen), Detailblöcke
├── publications/index.html     Filterbare Liste (Jahr, Typ, Thema, Volltextsuche)
├── cv/index.html               CV inkl. Service, Gremien, Standardisierung
├── teaching/index.html         Lehrportfolio und Betreuung
├── blog/index.html             Übersicht mit Tag-Filter
├── tags/index.html             Weiterleitung alter /tags/#slug-Links
├── impressum/index.html        Impressum + Datenschutz (Gerüst, siehe unten)
│
├── publication/<id>/index.html 232 generierte Detailseiten mit BibTeX
├── posts/JJJJ/MM/<slug>/       5 generierte Beitragsseiten
└── tools/
    ├── build_publication_pages.py
    ├── build_posts.py
    ├── build_redirects.py
    ├── build_sitemap.py
    └── check_site.py
```

Beide Generatoren brauchen nur Python 3 und die Standardbibliothek. Nach inhaltlichen Änderungen:

```bash
python3 tools/build_publication_pages.py
python3 tools/build_posts.py
python3 tools/build_redirects.py
python3 tools/build_sitemap.py
```

**Fehlt noch, muss von dir ergänzt werden:**

- `images/profile.png` — Portrait (empfohlen: zusätzlich `profile.webp`, ~800 px)
- `images/og-card.png` — Social-Preview, 1200 × 630 px
- `files/cv.pdf` — der CV-Download ist der primäre Call-to-Action im Hero

Diese drei Pfade stehen in `tools/check_site.py` unter `ALLOW_MISSING` und lassen die Prüfung
deshalb nicht fehlschlagen. Sobald die Dateien im Repo liegen, kannst du sie dort entfernen.

---

## Publikationen pflegen

Alle Publikationen liegen in **`data/publications.json`**. Die Übersichtsseite lädt die Datei
zur Laufzeit; die Detailseiten werden daraus generiert.

Ein Eintrag:

```json
{
  "id": "2026-06-01-C102",
  "y": 2026,
  "t": "conference",
  "ti": "Experiencing the Path: Comparing Visual Cues …",
  "a": "Henning, J., Vona, F., Hinzmann, S., Amer, M. & Voigt-Antons, J.-N.",
  "v": "18th International Conference on Quality of Multimedia Experience (QoMEX 2026), Cardiff, UK",
  "tp": "xr",
  "d": "https://doi.org/10.1145/…",
  "n": "Best Paper Award"
}
```

| Feld | Bedeutung | Werte |
|---|---|---|
| `id` | **URL-Schlüssel — stabil, wird nicht mehr geändert** | `JJJJ-MM-TT-<Nr>` |
| `ref` | **Nummer aus dem Publikationsverzeichnis, wird angezeigt** | z. B. `C102`, `J37` |
| `t` | Publikationstyp | `journal`, `conference`, `chapter`, `book`, `standard` |
| `tp` | Forschungslinie | `xr`, `qoe`, `psychophysiology`, `digital-health` |
| `d` | DOI oder Paper-URL | optional |
| `n` | Auszeichnung, „In press" o. Ä. | optional |

### Warum `id` und `ref` getrennt sind

Die Nummern im Publikationsverzeichnis verschieben sich, sobald du mittendrin etwas einfügst:
Wird ein Artikel zu `[J36]`, rutschen `[J36]`–`[J38]` eine Position weiter. Steckte die Nummer
in der URL, bräuchte **jede** nachfolgende Publikation eine neue Adresse und eine Weiterleitung.

Deshalb: `id` ist ein einmal vergebener, stabiler Schlüssel. `ref` trägt die Nummer aus dem
Verzeichnis und wird auf Detailseite und in der Liste als `[C102]` angezeigt. Eine
Renummerierung ändert damit nur `ref` — kein Link bricht, keine Weiterleitung nötig.

Praxisbeweis: Beim Nachtragen von `[J36]` sind drei Nummern verrutscht — geändert wurden vier
`ref`-Werte, sonst nichts. Keine URL, keine Weiterleitung, kein toter Link.

Nach jeder Änderung:

```bash
python3 tools/build_publication_pages.py
```

Das Skript schreibt `/publication/<id>/index.html` neu — inklusive automatisch erzeugtem BibTeX,
Schema.org-Metadaten und Vor/Zurück-Navigation. Es braucht nur die Standardbibliothek.

### Wichtig: die alten Publikations-URLs bleiben erhalten

Deine bisherigen Detailseiten (`/publication/2024-10-01-C78`) sind in Papers zitiert, von Scholar
verlinkt und indexiert. Das Generator-Skript reproduziert exakt dieses URL-Schema — deshalb gibt es
die Detailseiten überhaupt, statt nur eine Liste.

### Datenstand

`data/publications.json` enthält **232 Einträge, 2010–2026** — importiert aus
`04_Publikationsverzeichnis_Voigt-Antons.docx`.

Aufteilung: 163 Konferenzbeiträge · 45 Journalartikel · 17 Standardisierungsbeiträge ·
5 Buchkapitel · 2 Bücher.

Themen: 65 Psychophysiology · 63 XR · 62 Digital Health · 42 QoE.

Bibliometrie (Google Scholar, 2. August 2026): 2.987 Zitationen · h-Index 29 · i10-Index 83.
Die Zahlen stehen auf Startseite, Publikationsseite und im CV sowie unter `meta.bibliometrics`
in `data/publications.json`. Halbjährlich aktualisieren.

Nummernstand: `B1–B2`, `BC1–BC5`, `C1–C103`, `J1–J39`, `OC1–OC54`, `OJ1–OJ6`, `S1–S17` —
alle Reihen lückenlos und ohne Doppelvergabe. `tools/check_site.py` prüft das bei jedem Lauf.

Beim Import aufgefallen:

1. **Ein Paper fehlte zunächst im Verzeichnis** — „Multimodal Assistance in Rehabilitation…"
   (Virtual Worlds 5(1), 15). Inzwischen als `[J36]` nachgetragen; `[J36]`–`[J38]` sind dafür
   auf `[J37]`–`[J39]` gerückt. Weil die Verzeichnisnummer im Feld `ref` und nicht in der URL
   steckt, hat diese Verschiebung **keinen einzigen Link verändert**.
2. **Zwei DOIs standen doppelt im Verzeichnis** — behoben, aber im Word-Dokument noch drin:
   `10.1007/s00103-024-03917-2` bei `[OC43]` und `[J29]`, sowie `10.1024/1662-9647/a000210`
   bei `[OC12]` und `[J14]`. Über Crossref geprüft: beide DOIs gehören eindeutig dem jeweiligen
   Journalartikel (Bundesgesundheitsblatt 67(8), 921–930 bzw. GeroPsych 32(3), 135–144). Die
   Konferenzbeiträge `[OC43]` (DKVF 2024) und `[OC12]` (IAGG-ER 2019) hatten den DOI nur
   mitkopiert und stehen jetzt ohne. Eigene DOIs waren für sie nicht auffindbar — falls es
   welche gibt, gehören sie ins Feld `d`.

   Beim Prüfen ist außerdem aufgefallen, dass Crossref den englischen Titel von `[OC43]`
   („What importance does outpatient care have…") als Zweittitel desselben Journalartikels
   führt. Die beiden Einträge beschreiben also womöglich dieselbe Arbeit in zwei Fassungen.

3. **Hinweise stehen im Word-Dokument teils hinter dem DOI** — Auszeichnungen und Fußnoten wie
   „Shared first authorship". Beim ersten Import wurden sie verschluckt, weil der Parser nach der
   URL abgeschnitten hat. Betroffen waren `[J15]`, `[J16]` und `[J18]`; alle sind nachgetragen.
   **Bei künftigen Importen darauf achten.**
4. **Abgleich mit dem Google-Scholar-Export (August 2026).** 193 bereinigte Scholar-Einträge
   gegen die Seite geprüft: 175 Treffer. Ergebnis:

   *Drei Titel im Verzeichnis waren veraltet* — es standen die eingereichten statt der
   erschienenen Fassungen. Korrigiert und über Crossref bzw. Scholar belegt:
   `[J32]` → „Interactive digital twins enabling responsible extended reality applications"
   (Sci Rep 15, 34539) · `[J34]` → „A Modular Questionnaire for Target-Group-Specific
   Evaluation of Event Formats…" (Virtual Worlds 5(1), 10) · `[J31]` → „Outcomes of an
   App-Based Intervention… With Poststroke Aphasia" (JMIR mHealth 13(1), e67711).
   **Diese Titel gehören auch im Word-Dokument berichtigt.**

   *Fünf weitere Arbeiten fehlten im Verzeichnis* und stehen jetzt ohne `ref` auf der Seite:
   „Assessing Differences in Flow State Induced by an Adaptive Music Learning Software"
   (QoMEX 2020) · „From Interaction to Purchase" (HCII 2026) · „Designing Adaptive Virtual
   Health Assistants…" (HCII 2025) · zwei Kongressabstracts in Z Gerontol Geriatr (2024, 2022).

   *Bewusst nicht aufgenommen:* vier Preprints (arXiv, PsyArXiv, OSF, PeerJ), der
   DigiOnTrack-Projektbericht, das Einleitungskapitel von `[B2]` und die PflegeTab-Broschüre.

5. **Eine hochzitierte Arbeit fehlt im Verzeichnis:** „Influence of Hand Tracking as a Way of
   Interaction in Virtual Reality on User Experience" (QoMEX 2020, Athlone) — Erstautorschaft und
   laut Google Scholar mit 148 Zitationen die drittmeistzitierte Arbeit überhaupt. Sie steht als
   `2020-05-26-hand-tracking-vr` ohne `ref` auf der Seite und sollte ins Word-Dokument
   nachgetragen werden. Hinterlegt ist die arXiv-DOI (`10.48550/arXiv.2004.12642`); die
   IEEE-Proceedings-DOI habe ich nicht sicher ermitteln können und deshalb nicht geraten.

`tools/check_site.py` schlägt Alarm bei doppelten DOIs, doppelt vergebenen Nummern und
Lücken in einer Nummernreihe.

### Das Feld `n` (Notizen)

Enthält ausschließlich Belegbares: Auszeichnungen und Autorschafts-Fußnoten aus dem
Word-Dokument, dazu „In press" für noch nicht erschienene Arbeiten.

Beim Relaunch standen dort zunächst drei „Forthcoming"-Markierungen, die aus der alten Website
stammten und inzwischen überholt waren (die Konferenzen hatten stattgefunden), sowie ein
„Most-cited work" ohne Quelle. Beides ist entfernt. Faustregel: **Was in `n` steht, muss im
Publikationsverzeichnis oder in einer anderen belegbaren Quelle stehen.**

Alle 125 bereits existierenden Publikations-URLs sind unverändert erhalten.

### Themen-Tags

Die `tp`-Werte wurden komplett neu vergeben — nach Schlagwortregeln plus einer kuratierten
Korrekturliste für Fälle, in denen die Regeln danebenliegen (etwa VR-Exergame-Studien, die wegen
„Exergame" fälschlich unter Digital Health landeten, oder EEG-Arbeiten, die als XR getaggt waren).
Die früher gemeldeten Fehlzuordnungen der GPS-Mobilitätsstudien sind damit behoben.

Zum Nachjustieren genügt es, `tp` im jeweiligen Eintrag zu ändern — erlaubt sind `xr`, `qoe`,
`psychophysiology`, `digital-health`.

---

## Blog

Alle fünf bestehenden Beiträge sind übernommen und liegen als Markdown in `content/posts/`:

```
content/posts/
├── 2026-02-25-human-centered-xr-metrics.md
├── 2026-03-30-ar-navigation.md
├── 2026-04-08-mmve-2026.md
├── 2026-04-14-chi-2026.md
└── 2026-04-22-ariadne.md
```

Neuen Beitrag anlegen: Datei mit Front Matter in `content/posts/` ablegen, dann

```bash
python3 tools/build_posts.py
```

Das Skript erzeugt `/posts/<JJJJ>/<MM>/<slug>/index.html` — **wieder exakt dein altes URL-Schema** —
und schreibt `data/posts.json` neu, aus der die Blog-Übersicht lädt.

Front Matter:

```yaml
---
title: "Titel (in Anführungszeichen, wenn er einen Doppelpunkt enthält)"
date: 2026-08-01
slug: url-segment
tags: [extended reality, quality of experience]
summary: Ein Satz für Übersicht und Meta-Description.
---
```

Der Markdown-Parser ist bewusst minimal: Überschriften (`##`, `###`), Absätze, Aufzählungen,
nummerierte Listen, Links, **fett**, *kursiv*. Mehr brauchen deine Beiträge nicht, und so bleibt
das Skript ohne externe Abhängigkeiten.

Interne Links zu Papers schreibst du als `/publication/<id>` — die Detailseiten existieren.

**Tag-Filter:** Die Blog-Übersicht filtert per Klick nach Tag (`?tag=…`). Deine alten Tag-Links
(`/tags/#ariadne`) leiten über `tags/index.html` automatisch dorthin um.

---

## Deployment auf GitHub Pages

**Du musst nichts lokal ausführen.** Es genügt, eine Quelldatei zu ändern und zu pushen —
oder sie direkt auf github.com zu bearbeiten und auf „Commit changes" zu klicken.

`.github/workflows/deploy.yml` erledigt den Rest:

1. **build** — lässt `build_publication_pages.py` und `build_posts.py` laufen, **committet die
   erzeugten Seiten automatisch zurück** in den Branch, und prüft anschließend mit
   `check_site.py` auf tote Links, kaputte Anker, ungültiges JSON-LD und unbalanciertes HTML.
2. **deploy** — veröffentlicht das Repository-Root auf GitHub Pages. Nur auf dem Default-Branch.

Der Bot-Commit trägt `[skip ci]` und wird mit `GITHUB_TOKEN` gemacht — beides verhindert, dass
sich der Workflow selbst erneut auslöst. Eine Endlosschleife ist ausgeschlossen.

Einmalig einzustellen:

1. **Settings → Pages → Source: „GitHub Actions"** (nicht „Deploy from a branch").
   Custom Domain eintragen, „Enforce HTTPS" aktivieren.
2. **Settings → Actions → General → Workflow permissions: „Read and write permissions".**
   Ohne das kann der Workflow die generierten Seiten nicht zurückcommitten. Die Seite wird
   trotzdem deployt, aber das Repository läuft dem Live-Stand hinterher — der Workflow gibt
   dann eine Warnung aus.

Der Branch dieses Repositorys heißt **`master`**. Der Workflow reagiert auf `master` und `main`;
die Deploy-Bedingung hängt am Default-Branch des Repositorys und übersteht eine Umbenennung.

Falls du es doch lokal machen willst — etwa um das Ergebnis vor dem Push zu sehen:

```bash
python3 tools/build_publication_pages.py
python3 tools/build_posts.py
python3 tools/build_redirects.py
python3 tools/build_sitemap.py
python3 tools/check_site.py
```

### Warum überhaupt Generatoren statt einfach HTML schreiben?

Weil Konsistenz über 130 Dateien von Hand nicht durchzuhalten ist. Eine Änderung an Navigation
oder Footer trifft jede einzelne Publikations- und Beitragsseite — das Skript macht das in einer
Sekunde identisch. Und weil das Ergebnis reproduzierbar ist: gleiche Quelle rein, byte-gleiches
HTML raus. Nur deshalb kann die CI überhaupt prüfen, ob etwas auseinandergelaufen ist.

Inhalte (Texte, BibTeX-Daten, Zusammenfassungen) schreibst du oder ein LLM. Das Umwandeln in
gleichförmiges HTML ist Mechanik — dafür ist ein Skript das richtige Werkzeug.

DNS beim Registrar:

| Typ | Name | Wert |
|---|---|---|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | jantons.github.io |

Die Datei `.nojekyll` ist bereits vorhanden und nötig — sonst ignoriert GitHub Pages Ordner, die mit
`_` beginnen, und verarbeitet die Seiten unnötig durch Jekyll.

### Lokal testen

Die Publikations- und Blogseiten laden JSON per `fetch`. Über `file://` blockiert das die
Same-Origin-Policy. Deshalb lokal immer über einen Server öffnen:

```bash
python3 -m http.server 8000
# http://localhost:8000
```

---

## Design

- **Light-first**, Dark über den Toggle rechts oben; die Wahl wird in `localStorage` gemerkt.
- Akzentfarbe **Violett** `#5645f5` statt des üblichen Akademiker-Blaus, Teal `#0d9488` für
  Venue-Badges. Beide Werte stehen als CSS-Variablen ganz oben in `assets/style.css` — ein
  Zeilentausch färbt die ganze Site um.
- **Inter** für Fließtext, **JetBrains Mono** für Zahlen, Labels und Tags.
- Reduzierte Bewegung wird respektiert (`prefers-reduced-motion`).
- Die CV-Seite hat ein eigenes Print-Stylesheet — `Strg/Cmd+P` ergibt ein brauchbares PDF.

---

## Offene Punkte

1. **Google Fonts selbst hosten.** Aktuell laden Inter und JetBrains Mono von Googles Servern, das
   überträgt IP-Adressen in die USA. Für eine deutsche Professorenseite ist das ein vermeidbares
   DSGVO-Risiko. Dateien nach `assets/fonts/` legen, `@font-face` in `style.css` ergänzen, die drei
   `<link>`-Zeilen in allen Seiten entfernen.
2. **Impressum und Datenschutz vervollständigen.** `impressum/index.html` ist ein Gerüst mit
   Platzhaltern in eckigen Klammern und muss rechtlich geprüft werden.
3. **Bibliometrie aktuell halten.** Stand 2. August 2026. Halbjährlich nachziehen — veraltete
   Zitationszahlen fallen negativ auf.
4. **Projektzahl klären.** Die Fördertabelle listet 18 Projekte, im Text steht an zehn Stellen 19.
5. **Zweisprachigkeit.** Falls die Seite auch deutschen Berufungsverfahren dienen soll, wäre eine
   deutsche Fassung der Startseite unter `/de/` sinnvoll.

---

## Zur Zielsetzung

Die Seite arbeitet auf zwei Ebenen, ohne dass eine die andere stört:

- **Bewerbungen** — Kennzahlenleiste und „Track record" auf der Startseite liefern in unter
  30 Sekunden, was eine Berufungskommission prüft: Drittmittel, Publikationsleistung, Lehre,
  Betreuung, Leitungserfahrung, Standardisierung, Auszeichnungen. Der CV-Download ist der
  prominenteste Button der Seite.
- **Kollaborationen** — Forschungslinien, laufende Projekte und die Collaborate-Sektion nennen
  konkrete Andockpunkte statt einer allgemeinen Kontaktadresse.

Nachwuchsgewinnung ist bewusst nicht Teil dieser Seite und wird an
[immersive-reality-lab.de](https://immersive-reality-lab.de) verwiesen.
