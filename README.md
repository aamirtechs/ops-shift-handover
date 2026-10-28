# ops-shift-handover

Assemble a shift handover note for support and ops teams from a JSON file.
One command turns the outgoing shift's notes into a readable handover the
incoming shift can act on, with the worst incidents first.

## What it does

- Takes a JSON file with date, shift, team, outgoing and incoming leads,
  plus summary bullets, open incidents, pending tasks, and watch items.
- Renders a Markdown handover note, or plain text with `--format txt`.
- Sorts open incidents by severity: critical, high, medium, low, then
  anything else.
- Validates the input with `--check` and prints a blank template with
  `--template`.

## Usage

```sh
python3 ops_shift_handover.py examples/handover.json
python3 ops_shift_handover.py handover.json --format txt
python3 ops_shift_handover.py handover.json --out handover.md
python3 ops_shift_handover.py handover.json --check
python3 ops_shift_handover.py --template > handover.json
```

## Real example

Running it on `examples/handover.json` gives:

```
# Shift handover: Support, Night shift, 2026-10-28

Outgoing: Ayesha  |  Incoming: Bilal

## Summary
- Queue cleared to zero at handover.
- One billing incident stayed open, see below.

## Open incidents
- **INC-1001** [high] Billing page timeout (investigating)
  - Next step: Check payment gateway logs at 09:00.

## Pending tasks
- [ ] Reply to ticket 4521 about refund timing.

## Watch items
- Traffic spike expected at 10:00 during the sale.
```

## Tests

```sh
python3 -m unittest discover -s tests -v
```

13 tests pass, covering validation (missing fields, bad lists, incomplete
incidents), rendering (severity order, sections, all-clear note, plain
text output), and the CLI (human output, `--check`, `--template`,
`--format txt`).

## Why it can spread

Every support and ops team writes handover notes, and most of them are
free-form messages that bury the urgent item at the bottom. A tiny tool
that enforces the same shape every shift, puts critical incidents first,
and validates the input before the shift ends is an easy habit to adopt,
and an easy one for a team lead to share.
