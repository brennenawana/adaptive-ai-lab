# Nested Error Handling for Priority-Based Fallback

## Problem
Need to return first non-error value from multiple columns in priority order. Example: Column A preferred, but if it has #N/A, use Column B; if B also has #N/A, use Column C; if all are #N/A, return blank.

## Root Cause
Simple IF() cannot test for #N/A errors. ISERROR() exists but requires complex nesting. Need clean, nested approach.

## Solution
Nest IFERROR functions in priority order:
```excel
=IFERROR(A{row}, IFERROR(B{row}, IFERROR(C{row}, "")))
```

### How it works:
- IFERROR(A{row}, ...) returns A if A is not an error, otherwise evaluates second argument
- Second argument is another IFERROR checking B
- Third argument is another IFERROR checking C
- Innermost default is empty string ""

## Flow for Each Row:
1. Try column A → if success, return A value
2. If A is error → try column B → if success, return B value
3. If B is error → try column C → if success, return C value
4. If C is error → return empty string

## Example
Task 42354: Priority-based lookup
- Row 2: A=Completed, B=#N/A, C=#N/A → Returns "Completed"
- Row 3: A=#N/A, B=2022-03-15, C=#N/A → Returns "2022-03-15"
- Row 4: A=#N/A, B=#N/A, C=ENR → Returns "ENR"
- Row 8: A=#N/A, B=#N/A, C=#N/A → Returns "" (blank)

## Scalability
For 4 columns: `=IFERROR(A{row}, IFERROR(B{row}, IFERROR(C{row}, IFERROR(D{row}, ""))))`
For 5 columns: Add another IFERROR layer

## Key Points
- Works with any error: #N/A, #DIV/0!, #REF!, etc.
- Default fallback can be "", 0, "N/A", or any value
- Clean and readable even with many levels
- Excel 2007+ support
