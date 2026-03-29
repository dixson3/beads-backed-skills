# Phase 4: INTAKE

On operator approval:

## 4.1 — Set status `approved`

## 4.2 — Pour molecule

```bash
cp -f "${SKILL_DIR}/formulas/plan-execute.formula.toml" .beads/formulas/
RESULT=$(bd mol pour plan-execute --var objective="${objective}" --var plan_dir="${plan_dir}" --json)
rm -f .beads/formulas/plan-execute.formula.toml

EPIC=$(echo "$RESULT" | uv run python -c "import sys,json; print(json.load(sys.stdin)['new_epic_id'])")
START_GATE=$(echo "$RESULT" | uv run python -c "import sys,json; print(json.load(sys.stdin)['id_mapping']['plan.start-gate'])")
```

## 4.3 — Create beads from plan.md

For each epic/issue:

```bash
EPIC_BEAD=$(bd create "Epic: ${epic_name}" \
  --description="${epic_description}" -t epic -p 2 \
  --parent ${EPIC} --deps "${START_GATE}" \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")

ISSUE_BEAD=$(bd create "${issue_description}" \
  --description="${issue_detail}" -t task -p 2 \
  --parent ${EPIC_BEAD} --deps "${dependency_beads}" \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

## 4.4 — Attach upstream metadata

```bash
bd update ${ISSUE_BEAD} --metadata '{"upstream":"#142","disposition":"include"}' -q
```

## 4.5 — Create capability gates (if any)

```bash
CAP_GATE=$(bd create "Gate: ${gate_name}" \
  --description="Condition: ${condition}\nTest: ${test_cmd}\nInstructions: ${instructions}" \
  -t gate --parent ${EPIC} \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")

bd update ${blocked_issue} --deps "${CAP_GATE}" -q
```

## 4.6 — Create reconcile gate and step

Only when upstream issues incorporated (any non-exclude disposition):

```bash
RECONCILE_GATE=$(bd create "Gate: Reconcile upstream" \
  --description="Blocks reconciliation until execution complete." \
  -t gate --parent ${EPIC} \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")

RECONCILE_STEP=$(bd create "Reconcile: update upstream issues" \
  --description="Update upstream issues per plan dispositions." \
  -t task -p 1 --parent ${EPIC} --deps "${RECONCILE_GATE}" \
  --metadata "{\"agent\":\"agents/reconciler.md\",\"context\":[\"plan.md\"]}" \
  --json | uv run python -c "import sys,json; print(json.load(sys.stdin)['id'])")
```

## 4.7 — Burn investigation wisp

```bash
bd mol burn ${INVESTIGATION_WISP_ID} 2>/dev/null || true
```

## 4.8 — Handoff

Print plan ID, epic ID, start gate ID. Instruct operator to run `/bdplan execute <plan-id>` in a new session. Start gate can only be released in a new session.
