# Epistemics Specification

Anchors the evidence-discipline rules that are the reason this skill exists. These bind
ALL agents and ALL outputs. Verified against SKILL.md Epistemic Rules and the agent files.

REQ-EPIST-001: Absence is a valid finding. If a question cannot be answered from available sources, the output states "No evidence found" with what was searched and where — never fabrication, speculation, or padding from general knowledge.
Rationale: A fabricated answer is worse than an honest gap; the pipeline's value is calibrated evidence.
Verification: SKILL.md Epistemic Rules (1); `agents/synthesizer.md`, `agents/refiner.md`.

REQ-EPIST-002: Direct quotes over paraphrase. A citation includes a direct quote (`> "..." [N]`) with inline citation; paraphrase only when the original is excessively long, and still cite.
Rationale: Quotes are auditable; paraphrase can silently drift from the source.
Verification: SKILL.md Epistemic Rules (2).

REQ-EPIST-003: No uncited assertions. Every factual claim carries an inline `[N]` resolving to `sources.json`; methodology/structure statements are exempt; anything uncitable is flagged `[uncited]`.
Rationale: An uncited factual claim cannot be verified and must be visibly marked.
Verification: SKILL.md Epistemic Rules (3); `agents/packager.md` (flags residual `[uncited]`).

REQ-EPIST-004: Claims drawn from `questionable` or `avoid` sources are tagged `[uncertain]`; single-source claims are noted as such.
Rationale: Reader must see the strength of evidence behind each claim.
Verification: `agents/synthesizer.md` / `agents/refiner.md`; `spec/data.md` (credibility categories).

REQ-EPIST-005: Credibility scores are visible in the Sources section, and the critic validates them against the rubric independently of the scorer.
Rationale: An independent check guards against a mis-scored source propagating into conclusions.
Verification: `agents/critic.md`; `agents/synthesizer.md` Sources section.

REQ-EPIST-006: The packager verifies, before close, that every citation resolves, every research question is answered-with-evidence or explicitly marked unanswered, and no `[uncited]` / `[gap]` tags remain unresolved.
Rationale: The final gate on evidence discipline before the report is declared done.
Verification: `agents/packager.md` steps 1–2.
