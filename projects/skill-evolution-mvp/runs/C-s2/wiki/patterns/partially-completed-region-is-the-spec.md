# The already-completed region IS the specification

## Pattern
The prompt says something like *"I've completed results for the first meet"*, *"here's a sample sheet for reference"*, or the sheet simply has the first N rows of the answer column filled in. The agent reads the prompt's prose, invents a rule from it, and never reverse-engineers the completed region — often overwriting it in the process.

## Root cause
Natural-language descriptions of a mapping are almost always lossy ("fill in the results ... from column I on sheet two" doesn't say *which* row gets *which* value). The completed region is an unambiguous, machine-checkable statement of the same mapping. It is strictly more informative than the prose and it is what the grader compares against.

## Evidence: 194-19 (soft=0 in iteration 2 and iteration 4)
The agent had the answer key on screen and used none of it:
```
Sheet1 row 2: Meet=PORT MACQUARIE, Race#1, Tab=7,  I=None
Sheet1 row 3: Meet=PORT MACQUARIE, Race#1, Tab=14, I=2
Sheet1 row 4: Meet=PORT MACQUARIE, Race#1, Tab=12, I=4
Sheet1 row 8: Meet=PORT MACQUARIE, Race#1, Tab=?,  I=1
Sheet2 row 2: Track=PORT MACQUARIE, Race#1, J-M = [1, 14, 4, 12]
```
Decoding takes one minute: **J/K/L/M hold Tab numbers, and their column position is the rank.** Tab 1 -> rank 1, Tab 14 -> rank 2, Tab 4 -> rank 3, Tab 12 -> rank 4. Write the rank into Sheet1 column I on the row whose `Tab` (Sheet1 col J) matches; leave non-matching rows blank.

What the agent built instead: `lookup[(track,race)] = (top, first_non_empty(J..M))` — one scalar per race — then wrote that same constant into **every** Sheet1 row of the race, destroying the completed first meet (see destructive-overwrite-of-given-content.md).

## Evidence: 22-47 (soft=0)
Second sheet `ورقة1` held the expected output list (11 names, alphabetical, `HASSAN` three times) and `F2:F11` was pre-filled `1..10` fixing the output height at 10 rows. The agent printed both and then reasoned purely from the prose, ending with a global sort by REF that the reference sheet contradicts.

## Fix
1. Locate the completed region first: any answer-column cells that already have values, plus any sample/reference sheet.
2. Write `rule()` and run it **over the completed region only**; `assert` it reproduces every filled cell *and* leaves blank every cell that is blank there.
3. Only after that passes, extend to the empty region. Never write into the completed region.
4. If your rule can't reproduce the completed region, the prose reading is wrong — enumerate alternative mappings (positional vs value-based, per-row vs per-group) until one fits.
