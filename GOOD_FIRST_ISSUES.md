# Good first issues

Small, testable tasks for first-time contributors. No network access needed.

1. Add an `--include-resolved` section for incidents closed this shift.
   Scope: accept a resolved_incidents list, render it after open
   incidents, add tests.

2. Add a `--date` override that replaces the date in the input file.
   Scope: add the flag, apply it before rendering, add a CLI test.

3. Support multiple teams in one file, rendering one note per team.
   Scope: accept a list of handovers, render each with a separator,
   add tests.

4. Add a word count and incident count summary line at the top of the note.
   Scope: compute both counts, render them in Markdown and plain text,
   add tests.
