# Kybernion — project brief for continued work

Prepared 2026-09-19 for Android 0.3.4, Spread Grammar.
Repository: https://github.com/D-A-Rob01/Axisarium-Integration
Working branch: `codex/kybernion-034-spread-grammar`; baseline: `3dbe692` (0.3.3).
Read `changes-0.3.4.md` for verified build status. This brief describes the
inspected repository, distinguishes implementation from aspirations, and sets
boundaries for future design and interpretation work.

## Purpose

Kybernion is a personal, local-first instrument for structured symbolic inquiry.
It supports asking a question, drawing a fixed set of cards, noticing one's first
response, exporting that record, choosing an action, and later auditing whether
the reading helped. Its value is reflective and practical: clearer questions,
alternative frames, explicit uncertainty, and accountable follow-through.

The user values the existing icon and generative field, and wants greater variety
in the cognitive operations supported by spreads. Version 0.3.4 is a conservative
addition to a working app, not an architectural rewrite or an interpretation
service. Preserve The Constellation exactly. Preserve existing reading/export
behavior and user agency.

## Current architecture and source map

- `cartomancy_engine/android-app/`: Kotlin / Jetpack Compose Android application.
  Package and application ID remain `com.aletheion.cartomancy` for compatibility.
  Android minimum API 26, target/compile API 35, Java 17, Gradle wrapper, Android
  Gradle plugin 8.5.2. Android version 0.3.4 / code 7.
- `cartomancy_engine/src/cartomancy_engine/data/decks/rider-waite-smith.json`:
  78 canonical Major and Minor Arcana card records, with stable IDs and keywords.
- `.../data/spreads/*.json`: shared spread contracts containing only `id`, `name`,
  and ordered `positions` (`index`, `label`, `prompt`). Android packages this
  directory directly as assets. Python discovers the bundled JSON resources.
- `android-app/app/src/main/assets/tarot-v3/`: 78 complete SVG card illustrations
  and an artwork index with card IDs, paths, and SHA-256 hashes. Preserve LF
  bytes; image checksums are intentional integrity constraints.
- `ContractRepository.kt`: reads the bundled deck and formations; the Android
  selection list explicitly includes Three Card, Constellation, and the five
  Spread Grammar additions. Three other compact spreads remain Python-accessible.
- `DrawEngine.kt`: samples cards without replacement and sets optional reversals.
  Drawn cards retain their position label and prompt. Card draws are separate
  from the decorative generative field.
- `ContractModels.kt`: Parcelable card and reading records. `ReadingSessionViewModel.kt`
  retains the active reading through `SavedStateHandle`. Changing configuration
  must not silently redraw. The explicit refresh control begins a new reading.
- `CartomancyApp.kt`: question/setup, generative field, formation/protocol selection,
  draw action, adaptive card overview, full-screen detail view, first impression,
  and export controls. `Theme.kt` and resource vectors provide presentation.
- `ArtifactRenderer.kt`: Markdown and JSON representations of the same Android
  reading. `Export.kt` writes export files into app cache and shares them through
  a FileProvider and Android share intent, granting temporary URI read access.
- Python `reading.py`, `models.py`, `markdown.py`, `cli.py`, `review.py`: a separate
  CLI reading/review implementation using the shared deck and spreads. Its
  package version remains 0.1.0; that is not the Android app version. Do not claim
  that its schema and Android's richer export format are identical.
- `.github/workflows/kybernion-android.yml`: verifies artwork, startup contracts,
  deck/artwork IDs, unit tests, debug and release builds; an explicitly requested
  release run builds and retains a signed APK using repository secrets.

This source snapshot is not the user's phone, vault, or complete development
machine. It excludes private readings, credentials, keystores, local configuration,
build caches, and unrelated Axisarium systems. Shared source and assets are
sufficient for mobile development when the documented SDK/JDK dependencies are
installed. Signing credentials stay in their existing protected workflow.

## Workflow, persistence, and export contract

The practical sequence is ask → draw → notice → export → act → follow up → audit.
Capture the inquiry and context before drawing, choose a formation and protocol,
then commit one immutable draw. The first impression is distinct from later
interpretation. Preserve card identity, orientation, order, position text,
question, confidence, and context when editing notes or exporting.

Android artifacts include `schema_version: 1.0`, `architecture: kybernion`,
`draw_status: immutable`, deck/spread/mode and their conceptual aliases
(`symbolic_corpus`, `receptive_formation`, `interpretation_protocol`), plus
epistemic and audit identifiers, review metadata, and six claim types.
The Markdown worksheet includes first impression, reference notes, later
interpretation, action chosen, a 72-hour experiment, follow-up, and outcome/audit.
Most of those later fields are worksheet scaffolding, not a completed in-app
review database or automated outcome evaluator. The user exports and retains
the file; cache files are not a durable reading library.

Keep JSON fields, YAML names, compatibility identifiers, sharing behavior, and
the stored reading model stable. Changes to formats or persistence require an
explicit migration plan and regression evidence. Never silently replace a draw
or substitute artwork when a contract is missing.

## UX and visual language

The app should feel like a compact navigational instrument: dark surfaces,
luminous cyan/violet, controlled glow, clear typography, and a purposeful field
of nodes and connections. The icon's aperture/compass character is valued.
Preserve its existing resources. Avoid turning the interface into a catalog of
ornate occult motifs or filling the capture flow with philosophical exposition.

The generative Kybernetic Field responds deterministically to inquiry, formation,
protocol, reversals, and its generation count. Tapping it changes the field
composition; it does not supply divinatory evidence or alter a committed draw.
The field is a focus and interaction cue, not a measurement of energy or destiny.

Cards retain their complete 3:5 artwork, with adaptive overview and swipeable
detail views. Reversal rotates artwork while labels stay readable. Maintain
portrait/landscape readability, meaningful control labels, and useful touch
targets. Use progressive disclosure: let the user ask and draw efficiently,
then inspect details. Keep formation selection manual in 0.3.4.

## Symbolic and divinatory epistemology

Tarot is a structured symbolic prompt system. It can support association,
perspective-taking, narrative exploration, and hypothesis generation; the app
does not establish supernatural causation or objectively reveal hidden facts.
The software implements randomized card selection and recordkeeping, not
validated forecasting or psychological measurement.

Always distinguish:

1. Observation: the actual question, card, orientation, position, and later event.
2. Symbolic association: conventional or personally chosen relationships of meaning.
3. Intuition: the user's felt response, explicitly subjective.
4. Interpretation: a proposed account connecting symbols and circumstances.
5. Prediction: a tentative claim about future events, with conditions and a time window.
6. Action recommendation: a possible response evaluated against evidence and agency.

Do not collapse these layers into a single authoritative verdict. A meaningful
association does not prove a prediction. A useful reading does not establish
that a card caused an event. Confidence is a self-report, not a probability.
External language-model interpretations must remain identifiable as interpretations
and must not rewrite the source draw, invent context, or speak for other minds.

## Audit model

Before action, record what the reading suggests and what would count against the
interpretation. Choose a modest, reversible experiment when useful. Later record
what actually happened, what action was taken or avoided, what helped, what was
projection, and whether action became clearer. Preserve the original record
while adding follow-up. Avoid hindsight edits that make a vague prediction look
precise after the event.

Usefulness, projection risk, confidence, and review status are distinct fields.
No automated accuracy score, statistical validation, or recurrence analytics is
implemented by this release. Counterexamples and unhelpful readings belong in
the audit just as much as resonant ones.

## Spread Grammar

Each new formation is seven cards. The exact position order is part of its contract.

- **The Fork** — branching decisions: Current vector; Path A affordance; Path A
  cost; Path B affordance; Path B cost; Irreversible factor; Steering criterion.
  Name both options before drawing; cards do not choose on the user's behalf.
- **The Aperture** — investigation: Surface appearance; Assumption; Missing
  information; Distortion; Alternate frame; What becomes visible; Next inquiry.
  Unknowns require observation or questions, not invented factual answers.
- **The Crucible** — transformation: Material entering; Heat/pressure; What
  resists; What is being shed; What survives; New property; Tempering action.
  Do not romanticize suffering, require loss, or assume resistance is pathology.
- **The Interface** — self and another person/system/institution: Self-state;
  Other/system state; Contact surface; Misreading/noise; Mutual affordance;
  Boundary; Viable exchange. Other/system state is a testable working model,
  not access to another person's private thoughts or consent.
- **The Vector** — conditional short-range forecast: Initial condition; Momentum;
  Accelerant; Drag; Perturbation; Steering surface; Probable trajectory. Specify
  the time window. The final label is not a claim of measured probability.
- **The Constellation** — unchanged systemic formation: Present Star;
  Gravitational Pull; Threshold; Hidden Light; Relation; Course Correction;
  Emerging Pattern. Use for a broad configuration rather than forcing every
  question through it.

The complete prompts and use boundaries are in `spread-grammar.md` and the JSON
contracts. Three Card remains a compact Current Pattern / Complication / Next
Move default. Future recommendation features are optional proposals, not part
of 0.3.4. More spreads should add distinct inquiry operations, not just volume.

## Speculative psycho-spiritual frameworks

The project can host discussion of archetypes, ritual attention, synchronicity,
meaning-making, parts of self, embodied response, and cybernetic feedback as
interpretive lenses. These are optional conceptual frames for exploration, not
scientifically established mechanisms implemented by the code and not beliefs
to attribute to the user without their own statement.

Keep metaphor, subjective experience, historical tradition, and empirical claim
explicitly distinct. Invite multiple readings and disconfirming evidence. Do
not affirm that the cards establish surveillance, persecution, special powers,
destiny, spiritual rank, diagnostic facts, or compulsory action. The user's
agency, consent, privacy, and contact with ordinary evidence remain central.
The app is not therapy, diagnosis, or a substitute for qualified advice in
high-stakes decisions. This boundary should inform interpretation without
burdening every normal interaction with repetitive warnings.

## Non-goals and constraints

No cloud reading sync, embedded AI interpretation, direct vault writes, wearable
client, social feed, monetization, predictive accuracy claims, or major navigation
redesign is added here. No authentication, backup-policy, dependency-platform,
schema, or RNG redesign is bundled into this spread expansion. Review any future
security or persistence changes as their own work; do not infer protections that
the checked-out manifest and code do not implement.

Work only in the relevant mobile/engine scope. The broader repository contains
unrelated automation and personal configuration. Do not ask for or upload signing
secrets, account tokens, entire home directories, private vaults, or reading history
to continue mobile development. Uploaded files are a dated snapshot, not a live
GitHub connection; check branch/commit provenance before proposing a patch.

## Working instructions for a collaborator

Read this brief, the change record, spread guide, then the relevant source files.
Prefer small, reviewable patches. State what is implemented versus proposed,
and identify which tests were actually run. Keep draw, annotation, export,
interpretation, and audit separate. Do not label an APK signed or a device update
successful without direct evidence. Build tests do not substitute for real-device
acceptance, orientation checks, or a completed share-sheet export.

The existing project is the starting point. Preserve its icon, luminous design,
78-card mapping, Constellation, and reading/export spine while improving the
specific operation requested. If a source file is missing, name it instead of
inventing its contents. Cite file paths when discussing implementation.
