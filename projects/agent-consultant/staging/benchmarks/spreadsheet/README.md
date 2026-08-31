# Spreadsheet Benchmark — a real run of the loop, with receipts

This folder is a case study. It is the full record of one real experiment: the
skill-evolution loop this repository implements, run on a public spreadsheet
benchmark, with the rules frozen before the data and every dollar on a ledger.
Read it to see what the method produces — and to check our claims against the
raw numbers.

**The result in one line:** evolved skills raised a cheap model's score on 100
held-out spreadsheet tasks from 36% to 76% (frontier-guided) and 63%
(self-evolved), p < 0.001, while cutting inference cost per solved task about 3×.

| File | What it is |
|---|---|
| `REPORT.md` | The experiment report: design, execution record, results, limits |
| `CONTRACT.md` | The actual pre-registration, frozen before the data — rules, budgets, stop codes, and the two amendments made during the run |
| `skills/` | The winning evolved skill, exactly as the loop wrote and accepted it |
| `results/VERDICT.json` | Machine-readable outcomes and statistics |
| `results/spend.json` | Spend per run, reconciled from append-only ledgers |
| `results/test_looks.jsonl` | The test-look ledger: 7 looks planned, 7 spent, none extra |
| `adapter/`, `fetch_data.py` | Wire the engine to this benchmark and download its data — these land together with the engine port |

**About the benchmark's data:** the tasks and the checker belong to
SpreadsheetBench (Ma et al., NeurIPS 2024; "Verified-400" subset on Hugging
Face by KAKA22). That project publishes no license file, so we point at their
work instead of copying it — `fetch_data.py` downloads the data and the checker
from the original sources at pinned versions, and nothing of theirs is stored
in this repository.

**Method credit:** the loop and its role prompts come from WikiSkill
(arXiv:2608.27454; prompts CC BY 4.0). Full credits are in `REPORT.md` §9.
