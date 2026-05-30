# CDA Family-Availability Census (P0 scouting draft)

**Purpose:** check that ≥6 test families / ≈18–24 total (per `power/POWER-ANALYSIS.md`) can actually be sourced *before* the P0 freeze. This is scouting, not committed selection.
**Status:** DRAFT — every lineage claim carries an **evidence tier** and many need verification (flagged `VERIFY`). Nothing here is labeled ground truth until run through the §6.5 labeling protocol.
**Constraints applied:** copyleft/disputed inputs are first-class (verbatim-with-notices); proprietary/leaked-code reimplementations excluded (no Claude-Code clones). **Cross-language ST/PB is ENABLED (PI decision, spec v0.6):** `XLANG` edges (JS→Py ports etc.) are now **in-scope**, compared cross-language and reported as a **separate stratum** from within-language pairs (BH is the more robust cross-language signal).

**Evidence tiers:** **A** = documented by maintainer / official docs · **B** = widely reported / secondary · **C** = inferred, needs a source.

---

## 1. Candidate families (one row per domain)

The scarce cells are **natural DERIVED edge** and **same-spec INDEPENDENT pair**; EVOLVED (adjacent releases) and UNRELATED (any cross-domain pair) are free for every family and not enumerated here.

| # | Domain | DERIVED edge (natural) | tier | INDEPENDENT same-spec pair | tier | License / redist | Build / BH | Split |
|---|---|---|---|---|---|---|---|---|
| 1 | **char-encoding detect** | **(i)** Mozilla `universalchardet` (C++, MPL/tri-license) → `chardet` (Pilgrim, Python port) `XLANG` — original Mozilla→non-Mozilla rewrite; **(ii)** chardet 6.x→7.0 (LGPL→MIT, AI rewrite, *disputed*, in-Python); **(iii)** chardet → `charade` (Py3 fork, in-Python, merged back) | A / B / A | chardet ↔ charset_normalizer (MIT) | A | MPL/LGPL/MIT → verbatim+notices | pure-Py, easy; BH: bytes→encoding label | **TEST** (held out, mandatory) |
| 2 | **TOML parse** | tomli → CPython `tomllib` (vendored/adapted) | A | tomli ↔ tomlkit ↔ toml(uiri) ↔ rtoml | A | MIT/PSF/Apache, permissive | easy (rtoml native); BH: TOML→norm dict | train |
| 3 | **JSON (de)serialize** | simplejson → CPython `json` stdlib | A | simplejson ↔ ujson ↔ orjson ↔ json | A | MIT/PSF, permissive | ujson/orjson native (build risk); BH: roundtrip | train |
| 4 | **fuzzy / edit distance** | **fuzzywuzzy (GPL) → RapidFuzz (MIT)** reimplementation+relicense (human analog of chardet); python-Levenshtein (GPL) → `Levenshtein` fork (maxbachmann) | A / A | editdistance ↔ jellyfish ↔ RapidFuzz ↔ Levenshtein | A | GPL/MIT → copyleft **first-class** (verbatim+notices) | native ext (build); BH: (s1,s2)→score, easy | train |
| 5 | **YAML parse** | PyYAML → ruamel.yaml (**fork**) | A | PyYAML ↔ pyyaml-pure (Fadel, MIT, pure-Py) `VERIFY-indep` | C | MIT, permissive | pure-Py opt; BH: YAML→dict | train |
| 5a | **imaging** | PIL → Pillow (**fork**) | A | Pillow ↔ imageio/wand (scope differs) `WEAK` | C | PIL-MIT-ish / HPND | native, **heavy build/BH risk** | train |
| 6 | **Markdown render** | markdown-it (JS)→markdown-it-py (port) `XLANG` | A | Python-Markdown ↔ mistune ↔ markdown2 | A | MIT/BSD, permissive | pure-Py; BH: md→HTML (normalize) | TEST? |
| 7 | **semantic versioning** | node-semver (JS)→python ports `XLANG` | C | python-semver ↔ semantic_version (rbarrois) | A | MIT/BSD, permissive | pure-Py; BH: (ver,op)→bool, easy | train |
| 8 | **short-id / hashids** | hashids.js→hashids-python (official port) `XLANG` | A | hashids ↔ *(sqids = same-author successor → DERIVED, not indep)* `WEAK` | B | MIT, permissive | pure-Py; BH: int↔id roundtrip | train |
| 9 | **MessagePack** | (official per-lang impls — not a derivation) | — | msgpack-python ↔ u-msgpack-python ↔ ormsgpack | A | Apache/MIT, permissive | native (build risk); BH: pack/unpack roundtrip | TEST? |
| 10 | **slugify** | awesome-slugify ⇠ python-slugify (shared root?) `VERIFY` | C | python-slugify ↔ awesome-slugify ↔ slugify | B | MIT/GPL, permissive-ish | pure-Py; BH: str→slug | train |
| 11 | **base58/base-N codec** | base58 ports across langs `XLANG` | B | base58 ↔ based58 ↔ pybase62 | B | MIT, permissive | pure-Py; BH: bytes↔str roundtrip | train |
| 12 | **humanize / sizes** | humanize ⇠ jinja-humanize? `VERIFY` | C | humanize ↔ humanfriendly | B | MIT, permissive | pure-Py; BH: num→str | UNREL filler |

**chardet lineage chain (family 1, the motivating case):** Mozilla `universalchardet` (C++, MPL/tri-license) → `chardet` (Python port by Mark Pilgrim, LGPL) → { `chardet` 7.0 (MIT, AI rewrite) ; `charset_normalizer` (independent reimplementation, MIT) }. Edge **(i)** is a documented cross-language port carrying a relicense (Mozilla MPL/tri → LGPL) at the port boundary — the original Mozilla→non-Mozilla rewrite; edge **(ii)** is the disputed in-Python AI relicense (LGPL→MIT). The independent leg (`charset_normalizer`) makes this one domain populate **both** DERIVED and INDEPENDENT under a single spec — which is why it is the held-out TEST family. Note edge (i) is `XLANG` (C++→Python), so under the Python-only P0–P5 scope it is an exploratory/PB-only edge unless the cross-language scope decision (§2b) is taken.

---

## 2. Tally against the power-analysis floors

| requirement (`power/`) | needed | census supply | status |
|---|---|---|---|
| Domains with **both** a strong DERIVED edge **and** strong INDEPENDENT pair | ≥6 (≥6 test) | **~5 within-language** (char-encoding 1, TOML 2, JSON 3, fuzzy/edit-dist 4; YAML 5/imaging 5a partial) **+ now ~3 cross-language** (markdown 6, semver 7, hashids 8) = **~8** | 🟢 **CLEARS the floor** (with cross-lang stratum) |
| Total families | ≈18–24 | ~13 domains drafted (×EVOLVED/UNREL multiplies pairs, not families) | ⚠️ add ~5–10 more domains |
| Constructed seeds for RQ4 | ≥6–8 | ample (see §3) | ✅ |
| Proprietary/leaked excluded | — | enforced | ✅ |

**Headline finding (revised after verification, feeds back to `power/`):** the scarce cell is a **within-Python natural DERIVED edge co-located with independent same-spec implementations** — but the **fork / reimplementation route supplies more than the first draft credited**. Verified in-Python edges: chardet→`charade` (fork), tomli→tomllib, simplejson→`json` stdlib, PyYAML→ruamel (fork), PIL→Pillow (fork), python-Levenshtein→`Levenshtein` (fork), and **fuzzywuzzy (GPL)→RapidFuzz (MIT)** (reimplementation + relicense — a *human* analog of chardet). That is **~7 in-Python DERIVED edges, ≥4–5 co-located with independents** (char-encoding, JSON, fuzzy/edit-distance, TOML; YAML/imaging partial). **The cross-language scope decision (§2b) has now been TAKEN (spec v0.6)**, so the JS→Py port edges (markdown-it→py, node-semver→py, hashids→py) add ~3 more both-class domains as a separate cross-language stratum → **~8 both-class domains, comfortably clearing K_test ≥ 6.**

Remaining levers if a pilot still comes up short:
- **(a)** lower θ_LB to 0.60 (per the power map) — cheapest;
- **(b)** ~~cross-language scope~~ — **done (v0.6)**;
- **(c)** lean on **EVOLVED** (every project's adjacent releases) + **constructed** positives.

**Bonus finding:** **fuzzywuzzy→RapidFuzz is a genuine GPL→MIT relicensing-by-reimplementation** (human, pre-AI) — a high-value natural DERIVED-with-license-change row that parallels chardet, and (being GPL) it directly **validates the v0.4 copyleft-first-class input rule**. The census makes the availability risk concrete *before* the freeze rather than mid-build.

---

## 3. Constructed-derivative seeds (RQ4 dose-response; ≥6–8)
Small, permissive, pure-Python, well-tested seeds — fed to the mechanical and LLM-rewrite tracks (§6.4). Abundant: semver parser, hashids, levenshtein, base58 codec, a slugify, a roman-numeral converter, a small descriptive-stats util (mean/median/var), a TOML-subset parser, a CSV-lite reader. Pick ≥8; depth graded independently of the transform.

## 4. Real-world AI-relicense DERIVED edges (from the news scan)
Candidate natural DERIVED rows with documented (if disputed) lineage — see memory `cda-ai-relicense-cases`:
- **chardet v6→v7** (LGPL→MIT) — row 1, TEST.
- **Heretic → reaper-abliteration** (AGPL→PolyForm Noncommercial) — abliteration-tool domain; verify lineage; PolyForm is non-OSS (redistribution check).
- **MinIO** Apache→AGPL relicense + AI resurrection — large/native, BH-hermetic risk; likely metadata-only.
- **rEFui** (JS signal lib laundered) — `XLANG`/JS, out of Python scope for now.
- **Malus / PHALUS** — not benchmark *pairs*; candidate *generators* for the constructed LLM-rewrite track (PHALUS is OSS, self-hostable).

## 5. Open verification queue (before these can be labeled)
- **RESOLVED this pass:** fuzzy/edit-distance lineage (4) — `python-Levenshtein` (GPL) → `Levenshtein` fork by maxbachmann (GitHub issue #1 / PyPI confirm the rename-fork); `fuzzywuzzy` (GPL) → `RapidFuzz` (MIT) per RapidFuzz README ("based on an older MIT version of fuzzywuzzy"). chardet→`charade` Py3 fork confirmed via Blanchard's account. PIL→Pillow fork — tier A (well-known).
- **Still `VERIFY`:** YAML independent = `pyyaml-pure` (Fadel, MIT) — confirm it is *independent* of PyYAML, not derivative (alpha, low usage); slugify root (10); humanize lineage (12); imaging INDEPENDENT pair (5a) weak.
- **`XLANG`** rows are now **in-scope** (cross-language enabled, v0.6) but must pass the cross-language ST-descriptor validation (known port scores high vs independent cross-language same-spec scores lower, spec §13) and are reported as a separate stratum. **Disputed:** chardet v6→v7 evidence tier; Heretic fork claim; PolyForm/AGPL redistribution for Heretic / MinIO.
- Every row goes through §6.5 (≥2 raters, κ) before confirmatory use.

## 6. Backlog: additional candidate domains (to reach ≈18–24 families)
INDEPENDENT-rich domains (multiple same-spec Python impls) — most need a DERIVED edge found/verified before they count as both-class; all give EVOLVED + UNRELATED for free:
- **XML** — ElementTree (stdlib) ↔ lxml ↔ xmltodict; DERIVED: `cElementTree`→stdlib (`VERIFY`).
- **HTTP client** — requests ↔ httpx ↔ urllib3 ↔ aiohttp; DERIVED edge weak.
- **datetime** — dateutil ↔ arrow ↔ pendulum; DERIVED weak.
- **templating** — jinja2 ↔ mako ↔ chameleon; DERIVED weak.
- **HTML parse** — html.parser ↔ lxml ↔ html5lib; DERIVED: BeautifulSoup 3→4 rewrite (`VERIFY` EVOLVED-vs-DERIVED).
- **INI/config** — configparser ↔ configobj; thin.
- **CSV** — csv (stdlib) ↔ (pandas read_csv differs in scope).
- **fuzzy successor** — fuzzywuzzy → `thefuzz` (seatgeek successor/rename) — another DERIVED edge in domain 4.
- **DB driver** — MySQLdb → `mysqlclient` (**fork**, tier A) ↔ PyMySQL (independent same-protocol) — both-class candidate; native build.
- **test framework** — `nose` → `nose2` (successor/fork) ↔ pytest/unittest; DERIVED `VERIFY`.
- **JSON-schema** — jsonschema ↔ fastjsonschema (independent); DERIVED weak.

Most promising *additional* both-class domains to verify next: **DB driver (MySQLdb→mysqlclient fork + PyMySQL indep)** and **HTML/XML**. Target: lock ≥6 strong both-class test domains + ~12 train-side families.
