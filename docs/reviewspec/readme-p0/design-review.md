# Design review: README P0 verifiable MVP (INT-1 … INT-10)

**Verdict: PASS — conditional on the binding fitness directives below.**
The frozen spec is a faithful, complete, minimal distillation of the README P0 gate. No frozen
intent is contradictory, unbuildable, or self-weakening, so no finding requires a new G2. This
review adds the boundary clarifications, the six separated failure-policy families, the false-green
inventory, and the executable fitness directions (A–G) that the build (AIM-3) must satisfy and the
independent review (AIM-4) must confirm. Every finding is classified **bounded design correction /
build directive**, not frozen-scope change.

- **Plan revision reviewed:** `7a8075ee-ff65-4a64-8cde-c6938ac6f233` (AIM-1 accepted G2 plan).
- **Reviewed SHA:** `6d6ad87f625fd4246a5b47e0dbfe8b9de4768fa9` (branch `v2/autonomous/paperclip`).
- **Tree at reviewed SHA:** `README.md`, `docs/reviewspec/readme-p0/explore.md`,
  `docs/reviewspec/readme-p0/spec.md` only — no implementation, harness, fixture, schema, CI, or
  `docs/decisions` memory exists yet. This is a pre-code design gate, as intended.

**Triage:** structural. Every intent crosses a subsystem/mode/failure-policy boundary (contracts,
provenance graph, evaluator, gate runner, CI). Full review run.

---

## Elicit (step 0)

- **Prior record:** none. No `docs/decisions/*` and no prior `design-review.md`. Fresh
  elicitation; this file becomes the record. `[artifact-verified @ git ls-files]`
- **Intent gap (goal, not solution):** give every later milestone one *executable* truth boundary —
  artifacts interoperable+traceable, fixtures intact+reproducible, evaluators correct on known
  controls, and a gate that **cannot report success when evidence is missing or invalid**. Done =
  one command exits 0 on a clean checkout with all of A–G at their stated 100% / 0 thresholds.
  `[artifact-verified @ explore.md "Real goal"; README "P0 完成門檻"]`
- **Boundary gap:** nouns (8 artifacts, fixture, manifest, evaluator, provenance edge, report,
  mode) × extremes (count 0/1/many, validity valid/malformed/tampered/stale, presence
  present/absent/partial, ordering first/retried/replayed) drove the failure map and tabletop
  below.
- **Invariant gap — what must NEVER happen (the P0 shadow):**
  1. a run reports success while a required check failed / was skipped / errored in collection;
  2. an `arrangement` (or fabricated / defaulted) event is accepted as faithful `transcription`;
  3. a downstream artifact is reused after any upstream content **or model or parameter** changed;
  4. a human-corrected artifact is scored inside an *automatic* benchmark;
  5. a metric emits an unhandled NaN / Infinity / divide-by-zero and the run still passes;
  6. any report or artifact asserts unseen-song / real-model accuracy (no holdout exists).
- **Load-bearing + unverifiable (would-ask, none blocking):** the spec is intent-level and defers
  mechanism to the build by design (reviewspec-core §2: specs are minimal). The gaps below are
  therefore resolved by *fitness directive*, not by a question to the user; none change a frozen
  intent, so none are escalated as spec ambiguity.

## Reframe (step 1)

- **Truly protects:** the *trustworthiness of every future milestone's evidence*. If P0 is wrong,
  P2–P7 build green suites on a lying baseline — the most expensive correlated error.
- **Mis-framing risk:** reading P0 as "define schemas + write validators." The real object is a
  **fail-closed evidence system**: the load-bearing behavior is what the gate does when something is
  absent/tampered/skipped, not the happy round-trip. A build that maximizes green round-trip tests
  and under-builds the negative/skip surface satisfies the letter and fails the purpose.
- **Who learns on failure, how soon:** a developer/CI at `verify-p0` exit time. There is no live
  user. So the gate's real job includes *self-diagnosis* (which check, which artifact, expected vs
  observed) and *self-preservation* (it must refuse to green a blind or partial run).
- **Outage green unit tests would still miss:** a suite that passes because it collected **zero**
  tests (import error → 0 executed → exit 0); a semantic-equality comparator that hashes so many
  fields it never matches OR so few that a real change hashes equal; a checksum guard that mocks the
  filesystem and never touches a real byte. All three are green-and-wrong. Framing did **not** need
  to change; it needed to be made explicit — done here.

---

## Intent / risk audit (INT-1 … INT-10)

Each intent is **sound and buildable**; the risk column is the false-green pitfall a naive build
hits, and the directive is the defense (expanded in Fitness Directions A–G).

| Intent | Load-bearing risk (false-green pitfall) | Directive |
|---|---|---|
| **INT-1** 8 versioned contracts | `ProcessTestReport` is both "an artifact" (INT-1) and "a run report" (INT-8); if left ambiguous, round-trip (§A) either skips it or the EvaluationReport↔ProcessTestReport link is never asserted | **D-1**: treat both as first-class artifacts under §1 metadata + §A round-trip; `EvaluationReport` = scored, provenance-bearing artifact, `ProcessTestReport` = run-level gate report that **links** the EvaluationReport(s) it gated. The link is a required, checksum-verified field. |
| **INT-2** mode + instrument semantics | "invented transcription evidence rejected" is only *structurally* decidable at P0 (evidence field present + resolvable + in-bounds of the referenced stem span). Musically-fabricated-but-resolvable evidence is a real-model question, **out of P0 scope** | **D-2a**: scope evidence checks to *referential integrity* (present, resolves to a real stem/time span, within bounds); state the boundary explicitly so the build does not overclaim detection of musical fabrication. **D-2b**: uncertainty must be expressible **per fact**, not per artifact, or "concealed default" is untestable (e.g. pitch known while pedal/tuning unknown). |
| **INT-3** compatible evolution + migration | compat/migration suite is **vacuous** unless frozen version vectors exist (only one schema version exists today) → empty test passes | **D-3**: check in frozen vectors — ≥1 supported additive-minor, ≥1 unsupported-major, ≥1 legacy-major-to-migrate; assert the compat suite is non-empty and each vector is exercised. Migration preserves musical meaning via the **single** semantic-equality comparator (D-6). |
| **INT-4** immutable fixtures | immutability guarded only by "manifest checksum vs file" is defeated by editing file **and** manifest together; licensing at P0 is self-owned synthetic, not real-corpus | **D-4**: bind each published dataset **version** to a tamper anchor above the mutable manifest — the benchmark records the exact dataset version + manifest hash it ran against (committed / in the report), so under-the-same-version edits are detected against recorded state. Carry license/purpose fields; do **not** claim third-party licensed real-song coverage. |
| **INT-5** provenance + cache integrity | invalidation keyed on upstream **content** only silently reuses cache when only **model or parameter** changed (same audio, new model) — README explicitly lists content **and** model **and** parameter | **D-5**: downstream validity keys on the full provenance tuple `{content-hash, model, params, schema_version, mode}`; changing *only* model, *only* a parameter, or *only* mode must invalidate downstream. Forgery = unresolvable source ID **or** resolvable ID whose recorded hash ≠ current content. |
| **INT-6** reproducibility | determinism broken by wall-clock / unseeded RNG / map ordering / absolute paths inside hashed fields; OR non-semantic exclusion set too wide (real change hashes equal) or too narrow (flaky) | **D-6**: one canonical/normalized form drives semantic equality; it includes **all** musical fields and excludes only a **documented, minimal** non-semantic allowlist (creation time, environment, absolute paths). A semantic-field mutation must break equality; a non-semantic mutation must not. |
| **INT-7** evaluators on controls | swapped precision/recall; double-counting when 2 predictions match 1 GT; NaN on empty/empty; undefined macro treatment of empty classes; ambiguous tolerance-boundary side | **D-7**: fix a documented matching rule (one-to-one, e.g. nearest-within-tolerance; a second prediction near the same GT is a **false positive**, never a 2nd TP). Directional invariants: deletion lowers recall only; insertion lowers precision only. Empty/empty → documented sentinel, never NaN/Inf/÷0. Tolerance boundary tested at `t-ε, t, t+ε` per the documented inclusive/exclusive side. micro/macro/per-class share one documented definition incl. empty-class handling; evaluator version + tolerance written into the report. |
| **INT-8** truthful process reports | report references an artifact that has since changed (checksum not re-verified at gate time); human-corrected upstream feeds an automatic downstream **transitively** undetected | **D-8**: report validation re-verifies every referenced artifact's checksum at gate time (mismatch → report invalid). Human-correction is a **transitive taint** through the provenance graph; an automatic run whose lineage contains any human correction is rejected or isolated to a distinct category — never scored as automatic. Missing metric/threshold/version/reason → report invalid. |
| **INT-9** two-mode deterministic pipeline | a downstream generator emits a `success` artifact from a `failed` / `needs-human` / unresolved-low-confidence upstream (status not propagated) | **D-9**: status is fail-closed and propagating — no downstream may be `success` if any upstream is `failed`/unresolved; absent target instrument → no formal `transcription` TrackIR; `arrangement` TrackIR handed to a transcription-only path → rejected; upstream edit → old downstream invalidated. |
| **INT-10** one-command clean gate | collection error counts as "0 tests, exit 0"; dirty working tree makes "exact-SHA" a lie; a single group's failure fails to force nonzero; hidden dependence on uncommitted local files | **D-10**: runner enforces an **expected-check manifest** and asserts executed == expected (0 executed or missing check → nonzero); records SHA **and** a dirty-tree flag (dirty during official verification → flagged/failed); each acceptance group A–G can independently force a nonzero exit; the command is the CI entry point on a clean checkout, retaining report + key artifacts. |

**Holdout / accuracy boundary (affirmed).** The spec makes no holdout or real-model-quality claim
(spec context line: "P0 validates deterministic contracts and evaluators, not real-model
transcription quality"). This review affirms it and adds **D-11**: no artifact or report field may
express unseen-song or real-model accuracy; reviewer-authored break cases and transparent versioned
fixtures are contract/evaluator evidence only. `[user-confirmed @ AIM-2 "Holdout boundary" ]`

---

## Artifact / provenance graph and invariants

```
SourceMedia
  → CanonicalAudio
      → SongAnalysis ┐
      → StemSet      ┘
          → TrackIR (mode ∈ {transcription, arrangement})
              → NotationIR
                  → EvaluationReport ── linked by ──> ProcessTestReport (run-level gate)
```

**Graph invariants (must hold on every edge):**

- **INV-lineage:** any final artifact resolves *every* direct and indirect ancestor; each resolved
  ID's recorded content-hash equals current content. (INT-5)
- **INV-cache:** a downstream artifact is valid only while its recorded upstream tuple
  `{content-hash, model, params, schema_version, mode}` matches current upstream. Any drift ⇒ stale
  ⇒ invalid. (INT-5, INT-9 · D-5)
- **INV-status:** status ∈ {success, low-confidence, failed, needs-human} propagates fail-closed;
  no `success` downstream from a non-success upstream. (INT-9 · D-9)
- **INV-mode:** `transcription` events carry resolvable audio/stem evidence; `arrangement` events
  carry arrangement-decision provenance; the two are non-interchangeable and cross-use is rejected.
  (INT-2, INT-9 · D-2)
- **INV-taint:** a human-correction flag is transitive; automatic benchmarks exclude tainted
  lineage. (INT-8 · D-8)
- **INV-semantic-equality:** one comparator defines "musically equal" for round-trip, migration, and
  rerun; single source of truth. (INT-3, INT-6 · D-6)
- **INV-immutable:** a published dataset version is fixed; a new version ID is required to change
  data; a run records the exact version+manifest hash used. (INT-4 · D-4)

---

## Failure map (per component: blocks-vs-reports · rollback · half-broken · surviving repair)

| Component | On failure: block or report? | Rollback? | Half-broken behavior | Surviving diagnostic entry |
|---|---|---|---|---|
| **Schema validator** (A/B) | **block** (fail-closed) with structured error | n/a (pure) | partial write of an artifact → checksum ≠ content → integrity catches it downstream | error object names field + expected + observed |
| **Checksum / provenance / cache** (C/E) | **block**; must **not** self-heal | n/a | one edge re-hashed but a sibling stale → per-edge check, no global "looks ok" shortcut | lineage walk reports first broken edge (ID, recorded vs current hash) |
| **Fixture manifest** (D) | **block** whole benchmark; never skip-then-pass | n/a | some fixtures resolve, one checksum off → benchmark terminates, not partial-pass | manifest diff: which fixture ID + version + hash mismatched |
| **Evaluator** (E) | metric-level **report**, gate-level **block** | n/a | one metric non-finite → protected sentinel, run still marked failed if below threshold | control-answer table pinpoints the wrong metric direction |
| **Reproducibility** (D/F) | **block** on rerun mismatch | n/a | two runs differ in a semantic field → mismatch surfaced by the shared comparator | diff of normalized forms (semantic field that diverged) |
| **ProcessTestReport** (F/G) | **block**: incomplete/uncheckable report is itself invalid | n/a | report references a since-changed artifact → checksum re-verify fails at gate | report validation error: which reference, recorded vs current hash |
| **verify-p0 runner** (G) | **block** = nonzero exit; 0-executed or skip ⇒ nonzero | n/a | one group errored, others green → aggregate exit nonzero, expected==executed guard trips | exit code + per-group status + retained artifacts under `--output` |

**Recursive repair check:** the gate's self-diagnosis (which check failed, expected vs observed)
lives in the *report artifact written to `--output`*, i.e. **out-of-band** of the pass/fail
computation — it survives a failing run. Good. The one dependency to guard: the expected-check
manifest must itself be committed and integrity-checked, or a blind runner (manifest deleted)
could pass with zero checks — folded into **D-10**.

---

## Tabletop (5 scenarios, each from a distinct failure-map edge)

1. **Collection error masquerading as pass (runner edge).** Observes: a harness module fails to
   import; framework collects 0 tests. Returns: **must** be nonzero (expected==executed guard trips,
   0-executed ⇒ fail). Operator next step: report names "0 of N expected checks executed." Prior
   state preserved: yes (no artifacts overwritten). *Finding if the build lets 0-executed exit 0.*
2. **Model-only change, content identical (cache edge).** Observes: upstream audio unchanged, model
   version bumped; a naive content-only hash matches. Returns: downstream **must** invalidate on the
   provenance tuple (D-5). Operator: "downstream stale: model v1→v2." Prior state: old downstream
   marked invalid, not silently reused. *Finding if only content is hashed.*
3. **Dataset edited under the same version (immutability edge).** Observes: a published fixture file
   + its manifest checksum both edited. Returns: the run's recorded dataset version+manifest hash no
   longer matches (D-4) → benchmark fails. Operator: "dataset version X hash drift." Prior state:
   the recorded baseline hash is the anchor. *Finding if immutability is only manifest-vs-file.*
4. **Human-corrected artifact upstream of an automatic run (taint edge).** Observes: an automatic
   benchmark input whose lineage two hops up contains a human correction. Returns: rejected /
   isolated to a human-in-loop category (D-8), never scored automatic. Operator: "automatic run
   contaminated at TrackIR by human correction." Prior state: preserved. *Finding if taint is not
   transitive.*
5. **Two predictions inside one GT tolerance window (evaluator edge).** Observes: one GT onset, two
   predicted onsets both within tolerance. Returns: one TP + one FP (precision drops); **not** two
   TP (D-7). Operator: control-answer report shows precision penalized, recall unchanged. Prior
   state: n/a. *Finding if matching double-counts.*

No row ends in "operator cannot tell what went wrong" or "working prior state lost" — provided the
directives are honored. Each scenario is also a required break-test in the fitness directions.

---

## Failure-policy families (step 4 — must NOT be fused into one status/error code)

Grouping by *failure response* (not by topic) yields **six** distinct vectors. Fusing any two forces
a demonstrably wrong operator action (merge reductios noted):

1. **Contract-malformation** (A/B) — terminal, refuse, provable-before-commit, accident-guard.
2. **Integrity / tamper / stale** (C/E) — terminal, refuse, provable, **corruption/adversary-guard,
   must not self-heal.** *Merge reductio vs (1):* both "reject," but a malformed field is a benign
   author bug (fix serialization); a checksum/tamper failure means the evidence chain is
   compromised and the **whole result must be discarded** — different operator action ⇒ separate.
3. **Evaluator-numeric** (E) — terminal at gate, but a *wrong number* surfaced by controls /
   non-finite protection, accident-guard. Distinct: its failure is a value, not a rejected artifact.
4. **Reproducibility (cross-run)** (D/F) — observable only across **two** runs, not provable in one.
   Distinct vector: cannot be decided before commit.
5. **Coverage / skip gate** (G) — meta: guards that the *other* checks actually ran. *Merge reductio
   vs (1):* "a check failed" = code is wrong; "a check didn't run" = the gate is **blind** — both
   nonzero, different diagnosis ⇒ separate status.
6. **Contamination / taint** (F) — human-vs-automatic isolation; integrity of the benchmark
   *category*. Distinct from (2): the data is well-formed and untampered, but wrong-category.

Directive **D-fam**: the report exposes these as six distinguishable failure families; a single
opaque "FAILED" that collapses tamper, skip, and wrong-number is a finding.

---

## Executable fitness directions (per acceptance group A–G)

These are the binding, break-test-survivable checks AIM-3 must implement and AIM-4 must confirm.
"Real boundary" per reviewspec-core: **real files, real serialization, real subprocess exit, real
checksums — no mock may stand in for a boundary a test claims to verify.**

- **A · Schema contract.** For each of the 8 artifacts: build → serialize → schema-validate →
  deserialize → assert semantic equality via the D-6 comparator on a **real** on-disk file. Required
  red cases (each must produce a *structured* rejection): missing required field; wrong type; illegal
  enum/status transition; out-of-range time/sample-rate/pitch/confidence; unsupported major
  `schema_version`; nonexistent or type-incompatible upstream ID; content changed but checksum stale.
  **Break-test:** delete one assertion → a mutated-field artifact must turn a test red.
- **B · Version compatibility.** Load frozen vectors (D-3): additive-minor read succeeds;
  unsupported-major read **rejected explicitly** (not silently ignored); migration keeps the original
  artifact, mints a new ID, records migration source, and preserves musical meaning (D-6). **Assert
  the suite is non-empty** and each vector is exercised (guards vacuous pass).
- **C · Provenance.** Walk the min chain; every final artifact resolves all ancestors with matching
  hashes. **Break-tests:** delete / replace / forge one upstream ID → integrity fails; change only
  model, only a parameter, only mode with content fixed → downstream invalidated (D-5); a
  `transcription` event lacking resolvable evidence, and an `arrangement` event mislabeled
  transcription → rejected. Cross-mode mislabel count == 0.
- **D · Fixture integrity + reproducibility.** Every manifest file's checksum matches; every fixture
  has unique ID + version + license + purpose + ground truth; rerun with same seed/params → D-6
  semantic equality. Ground-truth time unit, coordinate origin, pitch standard, instrument taxonomy
  are explicit. **Break-tests:** missing file / checksum drift / incompatible annotation version →
  the benchmark **terminates** (never skip-then-pass); under-version dataset edit detected against
  recorded version+manifest hash (D-4).
- **E · Evaluator correctness.** The full control table (perfect→optimum; out-of-tolerance
  shift→onset score down; deletion→recall down, precision not penalized; insertion→precision down,
  recall not raised; wrong pitch/drum-class→class metrics down; empty/empty→documented sentinel;
  empty/non-empty→recall 0, report still complete). Plus: tolerance boundary tested at `t-ε, t, t+ε`
  per documented side; two-preds-one-GT → one TP + one FP (no double count); micro/macro/per-class
  one documented definition incl. empty-class handling; evaluator version + tolerance in the report.
  **Assert no NaN / Infinity / divide-by-zero anywhere.**
- **F · ProcessTestReport.** Both a passing and a failing run emit a report. Every referenced input /
  artifact / log exists and its checksum is **re-verified at gate time** (D-8). Below-threshold or
  incomplete → status failed **with a reason**. Missing metric/threshold/version/reason → the report
  itself is invalid. **Break-test:** feed a human-corrected artifact into an automatic run → rejected
  / isolated (transitive taint), mixed-result count == 0.
- **G · One-command clean gate.** `./scripts/verify-p0 --output artifacts/p0/latest` run as a **real
  subprocess** from a clean checkout: exit 0 only when all of A–F pass; each group can independently
  force nonzero (inject one failure per group, assert exit ≠ 0); expected==executed check-manifest
  guard (0-executed / missing check → nonzero); report records exact SHA + dirty-tree flag; report +
  key artifacts retained under `--output` and in CI. Both legal modes (transcription, arrangement)
  and all INT-9 negatives run inside this command.

**Thresholds affirmed:** 100% for every positive/rejection/completeness group; **0** for false
acceptance, false rejection, silent skip, cross-mode acceptance, non-finite result, and
human/automatic mixing.

---

## False-green risk register (the ways a build could be green-and-wrong)

1. **Zero-executed pass** — collection/import error → 0 tests → exit 0. Guard: G expected==executed.
2. **Vacuous compat suite** — no version vectors exist, so B passes trivially. Guard: B non-empty +
   exercised.
3. **Mocked boundary** — filesystem/subprocess/checksum mocked; nothing real is verified. Guard:
   reviewspec-core real-boundary rule; break-test a real on-disk corruption.
4. **Content-only cache key** — model/param change silently reuses cache. Guard: C provenance tuple.
5. **Comparator drift / mis-scope** — three different semantic-equality checks, or one that over- or
   under-includes fields. Guard: D-6 single comparator, semantic-mutation red / non-semantic green.
6. **Non-transitive taint** — human correction two hops up passes as automatic. Guard: F transitive.
7. **Opaque FAILED** — tamper, skip, and wrong-number collapse to one code; operator can't act.
   Guard: D-fam six families.
8. **Dirty-tree "exact SHA"** — report cites a SHA while the tree has uncommitted changes. Guard: G
   dirty-tree flag.
9. **Overclaim** — any "unseen-song accuracy" wording. Guard: D-11 no holdout/accuracy claim.

## Independent review (step 6)

No independent subagent was spawned (agent policy: no spawning unless requested). I ran the
adversarial pass myself in an explicitly adversarial frame — **weaker**, because a solo pass can
share the author's blind spot. The **true** independent second pass is **AIM-4 (G4 Independent
Review)**, run by a different agent against these same fitness directions; convergence there is the
real evidence, and any divergence marks the load-bearing decision. Self-pass convergences:
fail-closed status propagation, single semantic-equality comparator, six failure families, and the
zero-executed guard are the highest-value load-bearing items and are internally consistent with the
spec. Suspected residual blind spot to probe in AIM-4: the exact semantic-equality field set (D-6)
and the tolerance-boundary inclusive/exclusive choice (D-7) — both are "documented convention"
decisions the build owns; AIM-4 should confirm the build *documented and tested the boundary it
chose*, not that it chose a particular side.

---

## Verdict

**PASS**, conditional on the eleven directives (D-1 … D-11), the six-family separation (D-fam), the
graph invariants, and the A–G fitness directions above being implemented and break-tested by
AIM-3 and confirmed by AIM-4. The frozen spec (`7a8075ee-ff65-4a64-8cde-c6938ac6f233`) at SHA
`6d6ad87f625fd4246a5b47e0dbfe8b9de4768fa9` is faithful, complete, and buildable; every finding is a
**bounded design correction / build directive**, none is a frozen-scope change, so **no new G2 is
required**. Design gate cleared.

---
---

# Design record

_Last review: 2026-08-24 · commit `6d6ad87f625fd4246a5b47e0dbfe8b9de4768fa9`_

## Decision log (append-only — newest first, never edit past entries)

### 2026-08-24 · round 1 · first review (AIM-2, G3 design gate)
- **Changed:** Established the P0 design record and the design gate verdict: **PASS with 11 binding
  directives**, six separated failure-policy families, seven graph invariants, and A–G executable
  fitness directions.
- **Supersedes:** — (first review).
- **Carried over:** — (none prior).
- **Driver provenance:** review of spec revision `7a8075ee-ff65-4a64-8cde-c6938ac6f233` at SHA
  `6d6ad87` against README P0 and `explore.md`; holdout/accuracy boundary from AIM-2
  `[user-confirmed]`.

## Purpose (why this exists)

Give every later milestone one executable truth boundary: interoperable+traceable artifacts,
intact+reproducible fixtures, correct evaluators, and a gate that cannot report success when
evidence is missing/invalid. `[artifact-verified @ explore.md; README "P0 完成門檻"]`

## Boundary conditions

- ProcessTestReport at "is it a round-tripped artifact?" → **yes**, first-class under §1/§A, and it
  **links** the EvaluationReport it gated. `[assumed → build to confirm · D-1]`
- Upstream change at "only model / only param / only mode" → **invalidate downstream**.
  `[artifact-verified @ README "C. 來源追蹤" lists content/model/parameter · D-5]`
- Evidence check at "musically fabricated but resolvable" → **out of P0 scope**; only referential
  integrity is decidable. `[artifact-verified @ README G0 "deterministic stub"; spec context line · D-2a]`
- Fixture at "edited under same version" → **detected** against recorded version+manifest hash.
  `[assumed → build to confirm · D-4]`
- Benchmark input at "human correction N hops upstream" → **rejected/isolated (transitive)**.
  `[artifact-verified @ README "F"/"4" no-mixing rule · D-8]`
- Runner at "0 checks executed / collection error" → **nonzero exit**. `[artifact-verified @ README
  "無測試被靜默跳過" · D-10]`

## Invariants / cautions (must never happen)

- success reported over a failed/skipped/0-executed run — guarded by expected==executed manifest (D-10).
- arrangement/fabricated/defaulted event accepted as transcription — guarded by INV-mode + D-2.
- stale cache reuse on content **or model or param** change — guarded by INV-cache + D-5.
- human correction scored as automatic — guarded by INV-taint + D-8.
- unhandled NaN/Inf/÷0 passing — guarded by E controls + D-7.
- any unseen-song / real-model accuracy claim — guarded by D-11.

## Scenarios

The five tabletop rows above (0-executed pass, model-only cache, under-version dataset edit,
transitive taint, two-preds-one-GT) are the known failure modes; each is a required break-test.

## Facts relied on

- Reviewed tree at `6d6ad87` = README + explore.md + spec.md only; no code/CI/fixtures/decisions.
  `[artifact-verified @ git ls-files, git show --stat 6d6ad87]`
- Spec is intent-level/minimal by design; mechanism deferred to build. `[artifact-verified @
  reviewspec-core §2; spec.md]`
- No hidden holdout; transparent fixtures + reviewer break cases are not unseen-song accuracy.
  `[user-confirmed @ AIM-2 "Holdout boundary"]`
- AIM-3 (build) is blocked on this verdict; AIM-4 is the independent second pass. `[artifact-verified
  @ heartbeat-context blocks: AIM-3]`

## Links (authoritative — do not restate)

- README: `README.md` · spec: `docs/reviewspec/readme-p0/spec.md` · explore:
  `docs/reviewspec/readme-p0/explore.md` · this review: `docs/reviewspec/readme-p0/design-review.md`

## Open questions (for AIM-3 build to resolve, AIM-4 to confirm)

- Exact non-semantic-field allowlist for the D-6 comparator (must be documented + minimal).
- Tolerance-boundary inclusive/exclusive side for D-7 (must be documented + tested on both sides).
- The tamper anchor form for D-4 (committed lock vs report-recorded hash) — either satisfies the
  invariant; build to pick and document.
