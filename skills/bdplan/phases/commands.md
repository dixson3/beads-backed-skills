# Commands

## /bdplan continue [<plan-id>]

1. If plan-id given: read its plan.md, resume at current phase
2. If no argument, one open plan: auto-select
3. If multiple: present choices
4. Fuzzy-match objective text if ambiguous

plan.md is self-contained for cold resume.

## /bdplan list

```bash
for dir in docs/plans/plan-*/; do
  [ -f "${dir}plan.md" ] || continue
  id=$(basename "$dir")
  status=$(grep -m1 '^\*\*Status:\*\*' "${dir}plan.md" | sed 's/.*\*\* //')
  objective=$(head -1 "${dir}plan.md" | sed 's/^# Plan: //')
  printf "  %-35s %-30s status: %s\n" "$id" "\"$objective\"" "$status"
done
```

## /bdplan status [<plan-id>]

Show plan.md header + `bd show <epic-id> --json` + bead progress.
Without plan-id: show all plans with bead counts.
