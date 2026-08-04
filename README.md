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
├── sitemap.xml                 generiert, 253 URLs
│
├── assets/
│   ├── style.css               gemeinsames Stylesheet (Light-first + Dark-Toggle)
│   └── main.js                 Theme-Toggle, Mobile-Nav, Scroll-Reveal
│
├── data/
│   ├── publications.json       234 Einträge — Quelle für alles Publikationsbezogene
│   ├── projects.json           22 Drittmittelvorhaben — Quelle für Seite UND Bewerbung
│   ├── i18n.json               deutsche Übersetzungen, Schlüssel = englischer Satz
│   ├── posts.json              generiert aus content/posts/
│   └── redirects.json          alte → neue Publikations-URLs
│
├── content/posts/*.md          5 Blogbeiträge als Markdown (Quelldateien)
│
├── research/index.html         5 Forschungslinien ausführlich
├── projects/index.html         Förderverzeichnis (generiert), Detailblöcke (von Hand)
├── publications/index.html     Filterbare Liste (Jahr, Typ, Thema, Volltextsuche)
├── cv/index.html               CV inkl. Service, Gremien, Standardisierung
├── teaching/index.html         Lehrportfolio und Betreuung
├── blog/index.html             Übersicht mit Tag-Filter
├── tags/index.html             Weiterleitung alter /tags/#slug-Links
├── impressum/index.html        Impressum + Datenschutz (vollständig)
├── de/                         deutsche Fassung der fünf Kernseiten (generiert)
│
├── publication/<id>/index.html 234 generierte Detailseiten mit BibTeX
├── posts/JJJJ/MM/<slug>/       5 generierte Beitragsseiten
└── tools/
    ├── build_publication_pages.py
    ├── build_posts.py
    ├── build_projects.py       Fördertabelle aus data/projects.json
    ├── build_i18n.py           deutsche Seiten unter /de/
    ├── i18n_lib.py            Textextraktion für build_i18n.py
    ├── build_artifacts.py      nachnutzbare Daten und Instrumente auf /research/
    ├── build_jsonld.py         eine Entität, in alle Seiten geschrieben
    ├── build_llms_txt.py       llms.txt für Sprachmodelle
    ├── build_redirects.py
    ├── build_sitemap.py
    ├── check_site.py
    └── export_projects_docx.py Förderverzeichnis als Word-Datei
```

Die Seitengeneratoren brauchen nur Python 3 und die Standardbibliothek. Die vier PDF-Dokumente
brauchen zusätzlich **reportlab** — die Action installiert es selbst, du musst dafür nichts tun.

**Die Reihenfolge ist nicht beliebig:** `build_statement.py` schreibt die Konzeptseite und muss
deshalb vor `build_i18n.py` laufen; `build_i18n.py` erzeugt `/de/` und muss vor
`build_cv_pdf.py` laufen, das `de/cv/index.html` für die deutsche Fassung liest;
`build_jsonld.py` schreibt die Strukturdaten in **beide** Sprachfassungen und muss deshalb
nach `build_i18n.py` laufen, sonst trüge die deutsche Seite eine Kopie des englischen Blocks;
`build_record_pdfs.py` schreibt die Liste auf `/downloads/` und läuft zuletzt, wenn jedes
Dokument existiert, das es auflistet.

Nach inhaltlichen Änderungen:

```bash
python3 tools/build_publication_pages.py
python3 tools/build_posts.py
python3 tools/build_projects.py
python3 tools/build_supervision.py
python3 tools/build_artifacts.py
python3 tools/build_statement.py
python3 tools/build_i18n.py
python3 tools/build_jsonld.py
python3 tools/build_llms_txt.py
python3 tools/build_cv_pdf.py --all
python3 tools/build_record_pdfs.py --all
python3 tools/build_redirects.py
python3 tools/build_sitemap.py
```

### Social-Preview-Karte

`images/og-card.png` ist das Bild, das erscheint, wenn jemand einen Link auf diese Seite bei
LinkedIn, Slack, Mastodon oder in einer Mail teilt. **251 Seiten zeigen darauf** — ohne die Datei
rendert jeder geteilte Link als graue Fläche.

```bash
python3 tools/build_og_card.py            # hell, schreibt images/og-card.png
python3 tools/build_og_card.py --dark     # dunkle Variante
```

Die Zahlen auf der Karte werden aus `data/publications.json` und `data/projects.json` gelesen,
nie eingetippt. Die Karte kann also nicht eine andere Publikationszahl behaupten als die Seite,
an der sie hängt — genau der Fehler, den die Startseite mit „226 publications" hatte. Nach einer
Aktualisierung der Bibliometrie das Skript einmal laufen lassen.

Zwei Abhängigkeiten, die der Rest des Repos nicht hat: **Pillow** ist Pflicht
(`pip install Pillow`). **fontTools und brotli** sind optional — mit ihnen zeichnet das Skript in
Inter aus `assets/fonts/`, ohne sie in der nächstbesten Grotesk des Systems. Es sagt beim Lauf,
welche Schrift es genommen hat. Das Skript gehört bewusst **nicht** zum CI-Build; die Karte ist
ein einmaliges Asset, das committet wird.

### Zweisprachigkeit

Fünf Kernseiten gibt es auf Deutsch: `/de/`, `/de/research/`, `/de/projects/`, `/de/cv/`,
`/de/teaching/`. Publikationsliste, die 234 Detailseiten und der Blog bleiben englisch —
Titel, Venues und Abstracts sind es ohnehin, und eine übersetzte Literaturangabe wäre
unbrauchbar zum Zitieren.

**Die deutschen Seiten sind nichts, was du bearbeitest.** Sie werden bei jedem Lauf aus der
englischen Seite plus `data/i18n.json` neu erzeugt. Du pflegst also weiterhin nur die englische
Fassung.

Der Schlüssel in `data/i18n.json` ist **der englische Satz selbst**:

```json
"What sets this work apart": "Was diese Arbeit auszeichnet"
```

Das ist die ganze Idee. Änderst du den englischen Satz, ändert sich sein Schlüssel — und
`build_i18n.py` meldet ihn als unübersetzt und bricht ab, statt still eine deutsche Seite
auszuliefern, die noch das Alte behauptet. Genau diese Sorte Drift ist hier schon zweimal
aufgetreten: ein Absatz, der auf zwei Seiten stand und auseinanderlief, und eine Kennzahl, die
an vier Stellen von Hand stand und veraltete.

Übersetzt werden Blockelemente (`<p>`, `<li>`, Überschriften) sowie `<a>`, `<div>` und `<span>`
mit bestimmten Klassen (Buttons, Breadcrumbs, Tags, Fußzeile) und Metadaten-Attribute.
Publikationstitel bleiben unangetastet. Der Generator setzt außerdem `lang`, `canonical`,
wechselseitige `hreflang`-Verweise samt `x-default`, den DE/EN-Umschalter in der Navigation und
schreibt interne Links auf `/de/...` um, wo es eine deutsche Entsprechung gibt.

**Seiten, die es nur auf Englisch gibt**, bekommen trotzdem einen Umschalter: `/publications/`,
`/blog/` und `/404.html` führen zurück auf `/de/`. Wer aus der deutschen Navigation heraus auf
„Publikationen" klickt, fiele sonst still aus dem deutschen Bereich heraus und fände keinen
markierten Weg zurück. Das Label sagt die Wahrheit statt „diese Seite auf Deutsch" zu versprechen:
*„Zur deutschen Startseite — diese Seite gibt es nur auf Englisch."* Die Navigationslinks der
deutschen Seiten tragen dazu `hreflang="en"`, damit Screenreader den Sprachwechsel ansagen.

`/impressum/` bekommt bewusst **keinen**: die Seite ist bereits deutsch, und der Rechtstext ist in
dieser Sprache bindend. Eine englische Fassung müsste als unverbindlich gekennzeichnet werden —
stattdessen steht oben ein kurzer englischer Hinweis.

`tools/check_site.py` prüft: jede Kernseite hat ihr deutsches Gegenstück, `lang="de"`, korrekte
Canonical, wechselseitige hreflang-Paare auf **beiden** Seiten, Umschalter vorhanden, keine leere
Übersetzung, die drei englischen Seiten haben einen Rückweg nach `/de/` — und die Kennzahlen auch
in deutscher Schreibweise („2.987 Zitationen", „h-Index").

Neue Seite zweisprachig machen: Pfad in `PAGES` in `tools/build_i18n.py` und in `TRANSLATED` in
`tools/build_sitemap.py` eintragen, Skript laufen lassen, die gemeldeten Sätze in
`data/i18n.json` ergänzen.

### Schriften kommen von dieser Domain, nicht von Google

`assets/fonts/*.woff2` enthält Inter und JetBrains Mono; die `@font-face`-Regeln stehen in
`assets/style.css` zwischen `/* BEGIN fonts */` und `/* END fonts */` und werden von
`tools/fetch_fonts.py` erzeugt.

Grund: ein `<link>` auf `fonts.googleapis.com` lässt den Browser jedes Besuchers Google
kontaktieren, bevor die Seite rendert, und überträgt dabei dessen IP-Adresse. Das LG München I
hat genau das für rechtswidrig erklärt (3 O 17493/20, 20.01.2022). Die Seite stellt jetzt
**keine einzige Anfrage an Dritte** — das vereinfacht auch die Datenschutzerklärung.

Du musst dafür nichts tun: fehlen die Dateien, lädt die GitHub Action sie einmalig und committet
sie. `tools/check_site.py` bricht ab, wenn eine Seite wieder auf Google verlinkt, wenn der
Font-Block leer ist oder wenn eine `@font-face`-Regel auf eine fehlende Datei zeigt.

Neue Schriftversion holen: `assets/fonts/` löschen und pushen — oder lokal
`python3 tools/fetch_fonts.py`. Beide Familien stehen unter der SIL Open Font License 1.1,
die das Weiterverbreiten erlaubt; der Lizenztext liegt in `assets/fonts/OFL.txt`.

### Impressum und Datenschutz

`impressum/index.html` ist vollständig, Anschrift eingetragen und bestätigt.

`tools/check_site.py` bricht ab, sobald irgendwo ein Platzhalter in eckigen Klammern steht
(`[Anzupassen…]`, `[Straße…]`, `[PLZ…]`, `[TODO…]`). Eine Seite mit Platzhalter-Impressum online
zu stellen wäre schlimmer als gar keine. § 5 DDG verlangt eine *ladungsfähige* Anschrift —
ein Postfach genügt nicht.

Die Datenschutzerklärung deckt ab: Verantwortlicher, GitHub Pages als Hoster samt
Server-Logfiles und USA-Transfer (EU-US Data Privacy Framework, Angemessenheitsbeschluss vom
10.07.2023), selbst gehostete Schriften, `localStorage` für das Farbschema (§ 25 Abs. 2 Nr. 2
TDDDG, einwilligungsfrei), externe Links, Kontakt per E-Mail und die Betroffenenrechte.
Ein Cookie-Banner ist nicht nötig — die Seite setzt keine Cookies und lädt nichts von Dritten.

Nachziehen, wenn sich etwas ändert: sobald du Analytics, ein Kontaktformular, eingebettete
Videos oder Karten ergänzt, ist die Erklärung nicht mehr vollständig.

**Ich bin kein Anwalt** — der Text ist sorgfältig, aber ungeprüft. Für ein privates
Wissenschaftsangebot ohne Tracking ist das Risiko gering; sicher bist du erst nach anwaltlicher
Durchsicht.

**Fehlt noch, muss von dir ergänzt werden:**

Nichts mehr — Porträt, Social-Preview und CV liegen alle im Repo, `ALLOW_MISSING` in
`tools/check_site.py` ist leer. Jeder verlinkte Pfad wird geprüft.

### Fünf Dokumente, alle erzeugt

Unter `/downloads/` liegen drei Dokumente in je zwei Sprachen:

| Datei | Inhalt | Quelle |
|---|---|---|
| `cv.pdf` · `cv-de.pdf` | Lebenslauf, 5 Seiten | `cv/index.html` + JSON |
| `publications.pdf` · `-de` | alle 234 Publikationen nach Kategorien, 13 Seiten | `data/publications.json` |
| `funding.pdf` · `-de` | alle 22 Vorhaben mit Partnern und Rollensummen, 2 Seiten | `data/projects.json` |
| `statement.pdf` · `-de` | Forschungs- und Lehrkonzept, 3 Seiten | `data/statement.json` |

```bash
python3 tools/build_cv_pdf.py --all
python3 tools/build_record_pdfs.py --all     # schreibt auch die Downloads-Seite
python3 tools/build_statement.py
```

**Erzeugt statt hochgeladen** — aus demselben Grund, den die Bewerbungsunterlage vom Juli 2026
vorführt: ihre Rollenaufstellung zählt 6+3+9+2 = 20 Vorhaben, die Summenzeile sagt 19, und die
Projekttabelle bleibt 304 T€ unter ihrer eigenen Summe, weil PflegeTab in den Summen steckt, aber
in der Tabelle fehlt. Gezählte Zahlen können das nicht.

Die Dokumente nennen bewusst **keine Kennziffer einer Ausschreibung, keine Privatanschrift und
keine Telefonnummer**. Sie sind zum Verlinken gedacht, nicht als Dossier — ein Dossier verrät der
nächsten Kommission, wo man sich sonst beworben hat.

`/downloads/` listet, was tatsächlich existiert, mit echter Seitenzahl und Dateigröße; ein neues
Dokument kann dort nicht vergessen werden. `check_site.py` meldet jedes PDF als veraltet, sobald
seine Quellen sich bewegen.

### Das Forschungs- und Lehrkonzept

`data/statement.json` hält **beide Sprachen nebeneinander**. `tools/build_statement.py` erzeugt
daraus die Seite `/research/statement/` und beide PDFs; `build_i18n.py` erntet die Sprachpaare
direkt aus der JSON, statt sie ein zweites Mal in `data/i18n.json` zu verlangen.

Der Text stammt aus der Wuppertal-Bewerbung, ist aber von allem befreit, was zu jener Stelle
gehörte: keine Hochschule, keine Kennziffer, keine benannten Nachbarlehrstühle oder lokalen
Zentren. Übrig bleibt, was überall gilt — drei Forschungslinien mit Vorarbeiten und geplanten
Vorhaben, ein Lehrverständnis, eine Drittmittelstrategie und der Aufbauplan. Auch der Abschnitt
„Wo ich schwächer bin" zur bisher europäisch geprägten Förderhistorie ist geblieben; er ist das
Glaubwürdigste am ganzen Dokument.

### Der CV als PDF

Zwei Fassungen, je vier Seiten: `files/cv.pdf` (englisch) und `files/cv-de.pdf` (deutsch).

```bash
python3 tools/build_cv_pdf.py --all
```

Die deutsche Fassung ist **kein zweites Dokument**, sondern wird aus `de/cv/index.html` geparst
— der Seite, die `build_i18n.py` ohnehin erzeugt. Eine gepflegte CV-Seite, zwei PDFs. Die
deutschen Seiten verlinken automatisch auf `cv-de.pdf`, die englischen auf `cv.pdf`.

Sprachabhängig sind nur die Dokumentbestandteile, die nicht auf der Seite stehen — Titelzeile,
Kennzahlenbeschriftungen, Tabellenköpfe, Fußzeile — sowie die Zahlenschreibweise
(`4,609 Mio. €` und `2.987` statt `€4.609 M` und `2,987`). Die vier Rollenbezeichnungen der
Fördertabelle kommen aus `data/i18n.json`, damit sie nicht zweimal übersetzt werden.

**Der Fließtext wird aus `cv/index.html` geparst, die Zahlen kommen aus
`data/publications.json` und `data/projects.json`.** Du pflegst also weiterhin nur die CV-Seite;
das PDF zieht nach. Es gibt keine zweite Textfassung, die man zu ändern vergessen könnte — und
das PDF kann keine anderen Zahlen nennen als die Website, was der Bewerbung vom Juli passiert
ist (Rollenaufstellung 20 Vorhaben, Gesamtangabe 19, 304 T€ Differenz).

Die Publikationsauswahl folgt einer festen Regel statt Geschmack: erst alles mit Auszeichnung,
dann die neuesten Zeitschriftenaufsätze, gedeckelt bei 14. Die Regel steht im Dokument, die
vollständige Liste bleibt auf der Website.

Was so nicht ausgeschlossen ist: ein **veraltetes** PDF. Deshalb legt das Skript
neben jedem PDF einen Fingerabdruck seiner Quellen ab (`cv.build.json`, `cv-de.build.json`),
und `tools/check_site.py` vergleicht beide bei jedem Lauf — ändert sich die Datenlage, ohne dass
du neu baust, bricht der Build mit „files/cv-de.pdf is out of date" ab.

Braucht **reportlab** (`pip install reportlab`) und gehört bewusst nicht zum CI-Build.
Gesetzt in Liberation Sans; Inter scheitert am woff2-Format, das reportlab nicht liest.

### Porträt

`images/profile.jpg` und `.webp` (500 px) sowie `profile@2x` (1000 px), aus dem Original auf
500 × 575 beschnitten — dasselbe Seitenverhältnis, das der Hero reserviert, damit beim Laden
nichts springt. Die Startseite bindet sie über `<picture>` mit `srcset` ein: WebP zuerst, JPEG
als Rückfallebene, Auflösung nach Displaydichte.

Das spart deutlich: 12 KB statt der 908 KB, die dieselbe Bildhöhe als PNG gekostet hätte.
Das Porträt ist das größte Element im ersten Bildschirm und bestimmt damit den LCP-Wert.

Neues Foto einsetzen: Original nach `images/` legen und die vier Fassungen erzeugen — der
Zuschnitt orientiert sich am Verhältnis 500 : 575, oben etwas mehr Luft lassen als unten.

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
| `t` | Publikationstyp | `journal`, `conference`, `chapter`, `book`, `standard`, `position` |
| `tp` | Forschungslinie | `xr`, `qoe`, `psychophysiology`, `digital-health` |
| `d` | DOI oder Paper-URL | optional |
| `n` | Auszeichnung, „In press" o. Ä. | optional |

### Zwei bewusste Abweichungen, die keine Fehler sind

Beide sind geprüft und bestätigt — nicht „korrigieren", wenn sie beim nächsten Durchsehen
auffallen:

- **`[J39]` trägt „In press".** Korrekt, die Arbeit ist angenommen und noch nicht erschienen.
  Beim Erscheinen den Vermerk `n` entfernen und den DOI in `d` eintragen. Bis dahin taucht der
  Eintrag bewusst nicht in der Publikationsauswahl des CV-PDF auf.
- **`[OJ6]` hat als einziger Eintrag einen deutschen Titel.** Ebenfalls korrekt: das ist der
  Titel, unter dem die Arbeit erschienen ist. Publikationstitel werden nirgends übersetzt,
  auch nicht in der deutschen Fassung der Seite — die zitierfähige Form bleibt, wie sie ist.

### Warum `id` und `ref` getrennt sind

Die Nummern im Publikationsverzeichnis verschieben sich, sobald du mittendrin etwas einfügst:
Wird ein Artikel zu `[J36]`, rutschen `[J36]`–`[J38]` eine Position weiter. Steckte die Nummer
in der URL, bräuchte **jede** nachfolgende Publikation eine neue Adresse und eine Weiterleitung.

Deshalb: `id` ist ein einmal vergebener, stabiler Schlüssel. `ref` trägt die Nummer aus dem
Verzeichnis. Eine Renummerierung ändert damit nur `ref` — kein Link bricht, keine Weiterleitung
nötig.

**Wo die Nummer erscheint — und wo nicht.** In der Publikationsliste steht sie nicht. Dort
stand sie in derselben 64 px breiten Spalte wie die Jahreszahl, mit `white-space:nowrap`;
`2026[C58]` passte nicht hinein und lief in den Titel hinein — auf Laptop und Mobil sichtbar
überlagert. Wichtiger als der Fehler ist aber, dass sie dort ohnehin nichts beiträgt: es ist
*deine* Verzeichnisnummer, für Lesende der Seite eine Zahl ohne Bedeutung.

Ihr einziger echter Zweck ist der Abgleich — jemand hält deine Bewerbungsunterlage mit `[C58]`
in der Hand und sucht dieselbe Arbeit auf der Seite. Das leistet die Volltextsuche, die `ref`
seit jeher mitdurchsucht; im Suchfeld steht `C58` jetzt als Beispiel. Auf der **Detailseite**
bleibt die Nummer als Badge sichtbar, auf allen 234.

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

`data/publications.json` enthält **234 Einträge, 2010–2026** — importiert aus
`2026-08-03-List_of_publications_Voigt-Antons_full_new.docx`.

Aufteilung: 163 Konferenzbeiträge · 45 Journalartikel · 17 Standardisierungsbeiträge ·
5 Buchkapitel · 2 Bücher · 2 VDE-Positionspapiere.

Themen: 65 Psychophysiology · 63 XR · 62 Digital Health · 42 QoE.

Bibliometrie (Google Scholar, 2. August 2026): 2.987 Zitationen · h-Index 29 · i10-Index 83.
Die Zahlen stehen auf Startseite, Publikationsseite und im CV sowie unter `meta.bibliometrics`
in `data/publications.json`. Halbjährlich aktualisieren.

`tools/check_site.py` vergleicht jede im Fließtext genannte Zahl zu Publikationen, Zitationen,
h-Index und i10-Index mit `data/publications.json`. Nötig wurde das, weil im Hero der Startseite
lange „226 publications" stand, während die Liste längst 234 Einträge hatte — solche Zahlen
stehen an vier Stellen von Hand und veralten unbemerkt. Zeilen mit „Scopus" bleiben ausgenommen,
die zitieren bewusst eine andere Datenbank.

Nummernstand: `B1–B2`, `BC1–BC5`, `C1–C105`, `J1–J39`, `OC1–OC58`, `OJ1–OJ6`, `P1–P2`, `S1–S17` —
alle 234 Einträge nummeriert, alle Reihen lückenlos, keine Doppelvergabe.
`tools/check_site.py` prüft das bei jedem Lauf.

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

   *Stand 3. August 2026:* Alle Funde sind ins Verzeichnis übernommen; die Seite ist damit
   vollständig synchron. Beim Abgleich der neuen Fassung fielen zwei Datenfehler auf, die du
   inzwischen behoben hast — `[OC45]`/`[OC46]` waren doppelt vergeben und `[C44]` hatte als
   Titel nur noch „s.". Beides fand `tools/check_site.py` bzw. der Import-Abgleich.

   *Nachgetragen als eigener Typ `position`:* die beiden VDE-Positionspapiere „Gestaltung
   Digitalisierung im Gesundheitswesen" (VDE ITG/DGBMT, 2022) und „Vernetzte und intelligente
   Medizintechnik als Treiber eines modernen Gesundheitssystems" (VDE DGBMT, 2026). Bewusst
   **nicht** unter `conference` — es gibt weder Konferenz noch Peer Review; das hätte die Zahl
   der begutachteten Konferenzbeiträge verfälscht. Beim 2026er-Papier widersprechen sich
   Impressum („Juni 2026") und empfohlene Zitierweise („April 2026"); hinterlegt ist nur das Jahr.

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

## Drittmittelprojekte pflegen

Alle Vorhaben liegen in **`data/projects.json`** — die einzige Quelle. Daraus entsteht sowohl
der Abschnitt „Full funding record" auf `/projects/` als auch die Tabelle für
Bewerbungsunterlagen. Beträge in Tausend Euro.

```json
{
  "id": "ariadne",
  "from": 2024, "to": 2026,
  "name": "SDK for high-precision, multimodal, AR-integrated pedestrian navigation",
  "short": "ARiadne",
  "funder": "ZIM (BMWE)",
  "role": "subproject",
  "volume": 208,
  "partners": "SWCode",
  "ongoing": true
}
```

Rollen: `sole` (alleiniger Antragsteller) · `coordinator` (Verbundkoordinator) ·
`subproject` (Teilprojektleiter) · `co` (Mitantragsteller). Vorhaben ohne eigenes
Fördervolumen stehen unter `without_own_volume` und zählen nicht in die Summen.

**Es gibt kein `ongoing`-Feld.** Ob ein Vorhaben läuft, wird aus dem Enddatum abgeleitet:
`(to, to_month) >= (aktuelles Jahr, aktueller Monat)`. `to_month` ist optional und steht sonst
auf 12 — **trag es ein, sobald ein Projekt mitten im Jahr endet**, sonst zeigt die Seite es bis
zum Januar weiter als laufend. Genau das war bei ARiadne der Fall (Ende Juli 2026).
`build_projects.py` weist beim Lauf auf Vorhaben hin, die im laufenden Jahr enden und noch kein
`to_month` haben. Damit kann die Seite nicht behaupten, ein abgeschlossenes Projekt
laufe noch — der Abschnitt „Ongoing projects" pflegt sich mit dem Jahreswechsel selbst.
Auch `funder_short` (Kurzform für die Karten) und `blurb` (Kartentext) leben in der JSON.

Nach jeder Änderung:

```bash
python3 tools/build_projects.py     # Website aktualisieren
```

Das Skript schreibt **zwei** Abschnitte auf `/projects/`: „Ongoing projects" (Karten) und
„Full funding record" (Tabelle), jeweils zwischen HTML-Kommentar-Markern. Die Detailblöcke
darunter bleiben handgeschrieben — `check_site.py` prüft aber, ob ihre Laufzeitangaben noch
zur JSON passen.

### Warum das eine eigene Datenquelle ist

Die Zahlen standen bisher nur als HTML auf der Seite und wurden für jede Bewerbung von Hand
in Word übertragen. Genau dort sind die Fehler entstanden, die wir gefunden haben: eine
Rollenübersicht, die sich auf 20 Vorhaben addierte, während die Summenzeile 19 sagte; 304 T€,
die in der Projektliste fehlten; drei Vorhaben, die gar nicht auftauchten.

Jetzt werden **alle Summen berechnet, nie getippt** — Rollenaufteilung, Gesamtvolumen, der
Anteil eigenständig geleiteter Vorhaben. `tools/check_site.py` rechnet zusätzlich bei jedem
Lauf nach, ob die gerenderte Seite noch zur JSON passt, und prüft Startseite und CV auf
dieselben Werte. Gegengetestet: Ändert man einen Betrag in der JSON, meldet der Check vier
Abweichungen und bricht mit Exit-Code 1 ab. Dasselbe gilt für eine Laufzeit im Detailblock,
die von der JSON abweicht — so ist aufgefallen, dass DIDYMOS-XR dort noch mit „2023–2026"
stand, obwohl das Vorhaben im Dezember 2025 endete.

### Verzeichnis für Bewerbungen erzeugen

```bash
pip install python-docx
python3 tools/export_projects_docx.py --lang de     # Drittmittelprojekte_…_2026-08-03.docx
python3 tools/export_projects_docx.py --lang en
```

Erzeugt Zusammenfassung, Rollentabelle, vollständige Projektübersicht und Stichtag — mit
denselben Zahlen wie die Website. Die Formulierungen folgen deinem bisherigen Verzeichnis.

**Offen:** Die Rolle bei `fastjets` und `virtual-institute` ist mit `"role_unconfirmed": true`
markiert; beide Skripte weisen beim Lauf darauf hin. Nach der Klärung das Flag entfernen.

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
4. **Fehlende Zeile im Drittmittelverzeichnis.** `05_Drittmittelprojekte_Voigt-Antons.pdf` nennt
   in der Zusammenfassung 4,275 Mio. € in 19 Vorhaben; die Projektübersicht darunter listet aber
   nur 3,971 Mio. €. Es fehlt **eine Zeile über 304 T€ mit der Rolle Teilprojektleiter** —
   nach deiner Bestätigung **PflegeTab (2015–2018, GKV-Spitzenverband)**. Damit ergeben sich
   20 Vorhaben, und alle Teilsummen stimmen exakt:
   6 · 546 T€ (alleiniger Antragsteller) + 3 · 841 T€ (Verbundkoordinator) +
   9 · 2.788 T€ (Teilprojektleiter) + 2 · 100 T€ (Mitantragsteller) = **20 · 4.275 T€**.
   **Im PDF fehlen außerdem zwei weitere Vorhaben:**
   „XR Emergency Training for Military Fast Jets" (2024–2025, Training Optimization Programme
   der Luftwaffe, 44 T€) und „Digitalise SÜDWESTFALEN — Virtual Institute, Initialprojekt"
   (2023–2027, Innovative Hochschule, 290 T€).

   Mit allen drei Ergänzungen steht die Website auf **22 Vorhaben · 4.609 T€**, davon
   20 eigenständig beantragt und geleitet (4.509 T€):

   | Rolle | Vorhaben | Volumen |
   |---|---|---|
   | Alleiniger Antragsteller | 7 | 590 T€ |
   | Verbundkoordinator | 3 | 841 T€ |
   | Teilprojektleiter | 10 | 3.078 T€ |
   | Mitantragsteller | 2 | 100 T€ |
   | **Summe** | **22** | **4.609 T€** |

   **Die im August 2026 verschickte Bewerbung nennt noch 19 Vorhaben / 4,275 Mio. €.**
   Das ist unkritisch: Bewerbungsunterlagen sind Momentaufnahmen zum Einreichungsdatum, und
   die Abweichung geht nach oben. Die Website trägt deshalb einen eigenen Stichtag.
   **Für künftige Bewerbungen sind die Zahlen dieser Seite maßgeblich.**

   Zwei Rollen habe ich eingeordnet, ohne sie belegen zu können: Fast Jets als *alleiniger
   Antragsteller* (analog zu GESOBAU, Augletics, Huawei) und Digitalise SÜDWESTFALEN als
   *Teilprojektleiter* (eigenes Teilvorhaben im Verbund). **Bitte prüfen.**
   Drei Signale hatten darauf gedeutet: die Rollenspalte summiert sich auf 20, es fehlten 304 T€,
   und die Einleitung sagt „kontinuierlich seit 2015", während das früheste gelistete Vorhaben
   2016 begann.
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
