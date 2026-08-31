# Evolution Log

## [iter 1] ## Iteration 1 - Initial Pattern Discovery

**Analyzed:** 8 task executions (39931, 10452, 22-47, 42354, 32438, 82-30, 39903, 48745)

**Scores:** 3 passing (82-30, 39903, 48745 all scored 1.0); 5 unclear (soft=0.000 but formulas appear correct)

**Key Finding:** Passing tasks (82-30, 39903, 48745) used direct data processing logic rather than complex formulas. Formula-based approaches (SUMPRODUCT, INDEX/SMALL/IF, nested IFERROR) were conceptually sound but test validation unclear.

**7 patterns identified and documented:**
1. SUMPRODUCT multi-criteria lookup (Task 39931) - reliable without array formula entry
2. Cascading error priority (Task 42354) - nested IFERROR for "first valid" logic
3. TEXT function datetime formatting (Task 32438) - proper formatting beats string functions
4. Delimited data parsing (Task 48745 - PASS) - parse, lookup individually, aggregate unique sorted results
5. Prefix-based filtering (Tasks 10452, 39903) - LEFT() or character checks for inclusion/exclusion
6. Conditional sequential lookup (Task 10452) - INDEX/SMALL/IF for nth matching value
7. Type filtering + reorganization (Task 82-30 - PASS) - filter by criteria, organize into fixed rows

**Next Steps:** Monitor whether formula-based tasks achieve higher scores with refinement; track if type-filtering pattern generalizes to other data extraction tasks.


## [iter 3] ## [iter 3] Iteration 3 - Advanced Data Processing Patterns

**Analyzed:** 7 task executions (247-24, 48080, 43589, 50916, 22-47, 408-39, 48745, 57558)

**Scores:** 3 passing (408-39, 48745, 57558 all scored 1.0); 5 unclear (soft=0.000 - test validation unclear for some formula-based tasks)

**Key Finding:** All three passing tasks (408-39, 48745, 57558) use **Python data processing** rather than Excel formulas. This confirms that direct data manipulation is more reliable than nested array formulas for complex logic.

**Patterns Identified & Documented:**

1. **Dynamic Column Finding and Movement** (Task 408-39 - PASS)
   - Search for column by header value, not hard-coded position
   - Copy data and formatting to target location
   - Delete original column
   - Successfully moved '0-15' column dynamically despite position changes
   - Score: 1.0

2. **Multi-Criteria Date Range Lookup** (Task 57558 - PASS)
   - Match exact criteria (Type, Salesperson) + date range check (start ≤ date ≤ end)
   - Returns first matching value or empty
   - Correctly populated commission rates: 0.03 and 0.17
   - Score: 1.0

3. **Delimited Data Parsing Aggregation - CONFIRMED** (Task 48745 - PASS)
   - Reconfirmed existing pattern works reliably via Python
   - Correctly parsed and looked up semicolon-separated codes
   - Deduplication and sorting by group name working
   - Score: 1.0

4. **Formula Copy Reference Issues** (Task 50916 - FAIL)
   - Identified root cause: Absolute row references ($C$2) prevent proper formula copying
   - Solution: Use $B12 (col absolute, row relative) for criteria; C2 (fully relative) for return values
   - Formula syntax pattern documented for future reference

**Failing Tasks Analysis:**
- 247-24: Complex data operations (all operations appear correct but test validation returns 0)
- 48080: OFFSET formula for nth row extraction (formula syntax appears correct)
- 43589: Text parsing formula ("2 to 5" → 4 days) (formula appears correct)
- 50916: School calendar lookup with copy issues (formula reference problem identified)
- 22-47: Complex priority sorting with deduplication (logic implemented correctly but test validation unclear)

**Critical Insight:** Python data processing (with direct list/dict operations) is the most reliable approach for complex tasks, especially when:
- Parsing delimited data
- Finding columns dynamically
- Implementing multi-criteria logic with date ranges
- Handling data transformations with deduplication

**Next Steps:**
1. Monitor whether complex formula-based tasks benefit from formula-to-Python conversion
2. Track if dynamic column finding pattern generalizes to other data reorganization tasks
3. Test date range lookup pattern on variations (time-based, range-based rates, etc.)
4. Investigate why test validation returns 0 even when operations appear correct"
  }
]

## [iter 4] ## [iter 4] Iteration 4 - Data Processing Reliability Confirmation

**Analyzed:** 8 task executions (36097, 10747, 47766, 43589, 247-24, 1818, 82-30, 192-22)

**Scores:** 3 passing (1818, 82-30, 192-22 all scored 1.0); 5 failing (36097, 10747, 47766, 43589, 247-24 all scored 0.0)

**CRITICAL FINDING - Data Processing 100% Reliable, Formulas 0% Reliable**:
- **Passing tasks (3/3 = 100%)**: All used Python/openpyxl direct data processing with row iteration
  - Task 1818: Filtered 16 students by criteria, copied to Summary sheet (PASS 1.0)
  - Task 82-30: Extracted whole numbers, reorganized into fixed rows (PASS 1.0)
  - Task 192-22: Keyword matching across 9 keywords, populated 18 matches (PASS 1.0)

- **Failing tasks (0/4 = 0%)**: All used formula-based approaches despite appearing logically correct
  - Task 36097: Nested IF formula for tax calculation logic (FAIL 0.0)
  - Task 10747: SUMIFS formula for multi-criteria lookup (FAIL 0.0, even after correction)
  - Task 47766: SUMIFS with date range criteria (FAIL 0.0)
  - Task 43589: Complex text parsing formula (FAIL 0.0)
  - Task 247-24: Multi-step complex logic, incomplete trace (FAIL 0.0)

**2 new patterns identified and documented**:

1. **Criteria-Based Row Filtering** (Task 1818 - PASS)
   - Filter rows by criteria value using direct iteration
   - Extract matching rows and copy to target sheet
   - Maintains order, scales to any number of rows
   - Score: 1.0

2. **Keyword-Pattern-Matching-And-Population** (Task 192-22 - PASS)
   - Search multiple keywords (case-insensitive, partial match) in cells
   - Populate target column based on match
   - Iterate rows checking substring containment
   - Score: 1.0

**Confirmed Pattern**:
- **Type-Filtering-And-Reorganization** (Task 82-30 - PASS, reconfirmed)
  - Extract values by type criterion
  - Reorganize into fixed-width rows
  - Score: 1.0

**Root Cause Analysis - Why Formulas Fail**:
Even when formulas appeared logically correct (especially SUMIFS and nested IF), validation returned 0.0. Possible explanations:
1. Test validation system may have strict formula compatibility requirements
2. Formula syntax edge cases or Excel version differences
3. Data processing is the intended/optimal approach for complex logic
4. Formulas may have subtle bugs not caught by manual inspection

**Key Insight**: Across all iterations (1, 3, 4), data processing has been 100% reliable while formulas have shown ~0% reliability on complex tasks. This is not a random distribution but a strong signal.

**Recommendation**:
- **Default to data processing** for: filtering, conditional logic, multi-step transformations, reorganization
- **Use formulas only for**: simple cell calculations, single-criteria lookups, basic arithmetic
- **Avoid formulas for**: complex nested conditionals, multi-criteria operations, data reorganization

**Next Steps**:
1. All future complex tasks should default to Python/data processing approach
2. Reserve formulas for trivial single-step calculations only
3. Continue monitoring whether ANY formula-based complex task achieves passing score (hypothesis: unlikely)
4. Document this decision in skill selection logic

