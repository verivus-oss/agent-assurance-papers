# Clean-room / software-copyright case law → what CDA should measure

Research note (exa, 2026-05-30). How courts decide "derived vs independent," what evidentiary *signals* drive the ruling, and how that maps onto CDA's signal families. **Not legal advice** (§14); used to align the instrument's construct with the legal one it informs.

## 1. Clean-room / reverse-engineering rulings (the "is reimplementation infringement?" line)

- **Sega v. Accolade, 977 F.2d 1510 (9th Cir. 1992)** — *Ruling:* disassembling object code to reach the **unprotected functional/interface elements** was **fair use**. Notably the court said a "clean room" would *not* have avoided infringement, because disassembly (intermediate copying) was still necessary to learn the functional specs. *Signal that mattered:* purpose = accessing non-protectable function, not appropriating expression; the TMSS trademark string found in Accolade's object code was the copying evidence.
- **Sony v. Connectix, 203 F.3d 596 (9th Cir. 2000)** — *Ruling:* intermediate copying to reverse-engineer the PlayStation BIOS for a compatible emulator was **fair use**; methods (emulated-environment observation + partial disassembly) were "necessary" to reach unprotected functional elements. Intermediate copying does **not** defeat fair use.
- **Takeaway:** reproducing *function / interface* (even with full access to the original) is generally **not** infringement; only copying protectable **expression** is. Clean-room is risk-reduction, **not a guaranteed shield** (an intermediate team can still copy protected expression).

## 2. The substantial-similarity test — Abstraction-Filtration-Comparison (AFC)

**Computer Associates v. Altai, 982 F.2d 693 (2d Cir. 1992)** — the controlling test for *non-literal* copying. Holding: Altai's clean rewrite (OSCAR 3.5) did **not** infringe.
1. **Abstraction** — decompose the program into hierarchical levels (idea → architecture → modules → code).
2. **Filtration** — at each level **remove the UNPROTECTABLE**: ideas; elements **dictated by efficiency**; elements **dictated by external factors** (hardware, **compatibility/interoperability**, industry standards, target APIs); and **public-domain / scènes-à-faire** material.
3. **Comparison** — compare only the surviving **"golden nugget" of protectable expression** for substantial similarity.

## 3. Proving copying — access + (probative/striking) similarity, and *fingerprint* evidence

- **Two prongs** (9th Cir. model instructions; *Three Boys Music v. Bolton*): **access** + **substantial similarity** → presumption of copying, rebuttable by **independent creation**. **"Striking similarity"** can substitute for access.
- **Fingerprint evidence courts find most probative of copying** (because it has *no functional reason* to be shared — survives AFC filtration):
  - **identical / subtle shared BUGS and defects** (unlikely to arise independently);
  - **idiosyncratic naming** conventions;
  - **comments** (even paraphrased) in both;
  - **dead code / unreachable paths / unused functions** copied along;
  - **repeated typos / spelling mistakes**;
  - **watermarks / identity stamps / Easter eggs**;
  - **architectural choices not dictated by the problem domain**.

## 4. Mapping to CDA — this realigns the signal families

The legal framework essentially **tells CDA what to measure**, and it confirms M1 (retention ≠ copying):

| legal concept | CDA implication |
|---|---|
| **AFC filtration removes efficiency/compatibility/standards/domain elements** | The pilot's high **coarse structural** numbers (control-flow histogram 0.99 *for independents too*, topology, node-hist) are exactly the **"dictated by the domain"** elements the law **filters out** → they should be **down-weighted / treated as baseline**, not evidence. This is the legal basis for the **mandatory baseline panel** (§9) and the M1 "domain convergence ≠ derivation" point. |
| **The post-filtration "golden nugget" = arbitrary, non-functional expression** | This is CDA's **PB / provenance-quirk family**, not ST/BH. The pilot's iteration-4 signals (message strings, constants, vocabulary) are the right *kind*; the law says **add bug/defect, comment, dead-code, typo, and watermark fingerprints** — the legally-probative ones. |
| **Clean-room rulings: reproducing function ≠ infringement** | Legally validates that **BH agreement and structural retention are NOT the copying signal**; an AI rewrite that reproduces behavior but not arbitrary expression is the kind of clean reimplementation those cases generally treated as **fair-use reimplementation rather than infringement** — but CDA renders no verdict (§14). |
| **Access prong** | The chardet case has **admitted access** (Claude read v6 + training data), so the legal question collapses to substantial similarity of **protected expression** = the non-functional quirks — which the pilot found **small but non-zero** (residual 13 raw identifiers, mostly kept era-enum naming + stdlib false positives; data tables regenerated). **Under AFC this is genuinely contestable — CDA renders no verdict** (§14); the measurement leans toward clean reimplementation (consistent with the pilot and Blanchard) but is not zero. |
| **"Striking similarity"** | CDA's PB-quirk signals operationalize it: arbitrary features so improbable to share that they imply copying. |

## 5. Concrete changes this suggests for the spec
- **PB family (§5.2):** add legally-probative provenance-quirk signals — **shared bugs/defects, comments, dead/unreachable code, idiosyncratic identifiers, typos, watermarks** — as the copying-specific signals, alongside literal/data-table carryover.
- **Construct (§3, §5):** frame CDA's target to mirror **AFC**: *filter functionally-dictated similarity (baseline), measure retention of arbitrary protectable expression.* State that high ST/BH is "fair-use-consistent reimplementation" territory unless PB-quirks fire.
- **Baseline panel (§9):** the legal grounding for subtracting the domain baseline — "filtration" in code.
- **Related Work (§19):** add Sega, Sony, **Altai/AFC**, and the access+substantial-similarity / fingerprint-evidence doctrine.
- **chardet TEST framing (§4):** the calibrated read (ST/BH high but at the domain-baseline; PB literal carryover ~0 but a small non-zero arbitrary-name residual) is **contestable** — stated as measurement, never a verdict (§14).
