# Result Calculation Tool

Calculates **Student Term Reports** (from Student Term Subject Results) and
**Student Year Reports** (from Student Term Reports), with a validation
preview, configurable policies for every data problem, background execution
with live progress, and a persistent audit log.

## Workflow

1. Open **Result Calculation Tool**, pick the calculation type, academic
   year, semester (for term results) and optionally a student group.
2. Click **Preview Only** (or just **Preview & Calculate**). The tool
   analyzes the data *without writing anything* and shows:
   - how many students / groups / results are involved
   - draft records that would be ignored, included, or block the run
   - students missing subjects that their group-mates have
   - students missing whole terms (joined mid-year, left, expelled)
   - inactive students who still have results
   - active students with no results at all
   - students with results who aren't on the group roster
   - courses excluded from averages
   - existing reports that would be updated / replaced / skipped
3. Confirm. The calculation runs (in the background by default) with a
   progress bar, and every action is recorded in a **Result Calculation
   Log** (one row per student: Success / Warning / Skipped / Error).
4. Recent runs are listed at the bottom of the tool; each links to its log.

One student's bad data never aborts the batch: each student is calculated
inside a savepoint, failures are rolled back and logged, and the run
continues.

## Customization options

| Option | Choices | Notes |
| --- | --- | --- |
| Draft Data Handling | Ignore / Include / Block | Applies to subject results (term calc) or term reports (year calc) |
| Missing Subject Handling | Calculate with available / Skip student / Block | "Missing" is measured against the subjects other students in the same group have |
| Missing Term Handling | Average available terms / Treat missing as zero / Exclude student / Block | Year calc only. Partial students are flagged `Partial Year` on the report with remarks listing the missing terms |
| Year Average Method | Average of term averages / Average of course year percentages | Term-based weighs each term equally; course-based weighs by max scores |
| Only Active Students | on/off | Skips students marked inactive on the Student Group roster |
| Existing Submitted Reports | Replace (cancel + delete + recreate) / Skip | Draft reports are always updated in place |
| Course exclusions | Course-level flag + per-run list | See below |
| Terms to Include | explicit list or auto-detect | Which terms constitute the year |
| Run in Background | on/off | Background runs use the long queue with progress events |

## Excluding courses from averages (e.g. Art in Kindergarten)

Two mechanisms, combinable:

- **Course master flag** — check *Exclude from Result Average* on the
  Course. It is excluded from every calculation (can be overridden per run
  by unchecking *Respect Course-Level Exclusion Flags*).
- **Per-run list** — add courses under *Also Exclude These Courses* to
  exclude them for that run only.

Excluded courses **still appear on the report cards** with their scores and
percentages — they simply don't count towards the term/year average. The
`Excluded from Average` flag is stored on each Course Term Summary /
Course Year Summary row so downstream consumers (report card prints,
frontend) can label them.

Subjects whose total maximum score is 0 (data-entry errors) are shown but
automatically left out of the average, with a warning in the log.

## Students joining or leaving mid-year

- The **preview** lists every student who is missing one or more terms,
  per group, before anything is calculated.
- The **Missing Term Handling** policy decides what happens to them.
- Their Student Year Report records `Terms Expected`, `Terms Included`,
  `Partial Year`, the policy applied, and remarks naming the missing terms.
- Marking a student *inactive* on the Student Group roster (plus *Only
  Active Students*) keeps them out of new calculations entirely while
  their historical reports remain intact.

## Programmatic API

```python
from education.education.doctype.result_calculation_tool.result_calculation_tool import (
	preview_calculation, start_calculation,
)

preview_calculation({"calculation_type": "Term Results", "academic_year": "2018 E.C.", "semester": "Semester 1"})

start_calculation({
	"calculation_type": "Year Results",
	"academic_year": "2018 E.C.",
	"missing_term_policy": "Exclude Students with Missing Terms",
	"result_action": "Save and Submit",
})  # returns {"log_name": ..., "queued": True}
```

The legacy entry points (`education.education.api.calculate_results`,
`calculate_term_results`, `calculate_year_results`) still work and now run
through this engine, so they get the logging and error isolation too.

## Doctypes

- **Result Calculation Tool** (Single) — the UI.
- **Result Calculation Log** + **Result Calculation Log Entry** — one log
  per run; parameters snapshot, counters, timing, and per-student entries.
- **Result Calculation Course** / **Result Calculation Term** — child
  tables backing the multi-select fields.
