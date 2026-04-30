# Automatic Percentage Calculation - Student Term Subject Result

## 🎯 Update Applied

**What:** The `percentage` field now automatically calculates based on `score` and `max_score`

**When:** Applied immediately (v1.2.1)

**How:** Updates happen automatically on save for new and existing records

---

## ✅ What Changed

### Automatic Calculation

**Before:**
- Percentage field was calculated but could be manually overridden
- Existing records might have incorrect percentages
- No easy way to recalculate for all records

**After:**
- Percentage **always** auto-calculates on save
- Formula: `percentage = (score / max_score) × 100`
- Rounded to 2 decimal places
- Handles edge cases (0 scores, 0 max_score)

### Code Enhancement

```python
def calculate_percentage(self):
    """Calculate percentage based on score and max score"""
    # Always calculate if max_score is set
    if self.max_score and flt(self.max_score) > 0:
        self.percentage = round(flt(self.score) / flt(self.max_score) * 100, 2)
    elif flt(self.score) == 0 and flt(self.max_score) == 0:
        self.percentage = 0
    else:
        # If max_score is 0 but score is set, set percentage to 0
        self.percentage = 0
```

**Key Improvements:**
- ✅ Always calculates (even if percentage already set)
- ✅ Handles score = 0 correctly
- ✅ Handles max_score = 0 safely
- ✅ Rounds to 2 decimal places
- ✅ Uses flt() for safe float conversion

---

## 📊 Examples

### Example 1: Normal Calculation
```
score = 85
max_score = 100
percentage = (85 / 100) × 100 = 85.00%
```

### Example 2: Zero Score
```
score = 0
max_score = 100
percentage = (0 / 100) × 100 = 0.00%
```

### Example 3: Perfect Score
```
score = 100
max_score = 100
percentage = (100 / 100) × 100 = 100.00%
```

### Example 4: Fractional Scores
```
score = 47.5
max_score = 50
percentage = (47.5 / 50) × 100 = 95.00%
```

### Example 5: Edge Case - Zero Max Score
```
score = 10
max_score = 0
percentage = 0.00% (prevents division by zero)
```

---

## 🔄 Update Existing Records

You have **two options** to update percentages for existing records:

### Option 1: Automatic Function (Recommended)

```bash
# Via bench console
bench --site [your-site-name] console
```

```python
# Import the function
from education.education.doctype.student_term_subject_result.student_term_subject_result import update_all_percentages

# Run update (commits changes)
update_all_percentages()
```

**Output:**
```
======================================================================
Student Term Subject Result - Percentage Update Utility
======================================================================

Found 150 records to process...
Mode: COMMIT

✓ STSR-2025-00001 (Alice Johnson - Mathematics)
   85/100 → 0% → 85.00%
✓ STSR-2025-00002 (Bob Smith - English)
   78/100 → 0% → 78.00%
...

✓ Changes committed to database!

======================================================================
Summary:
----------------------------------------------------------------------
  Total records:      150
  Updated:            145
  Already correct:    5
  Errors:             0
======================================================================
```

### Option 2: Using Separate Script

```bash
bench --site [your-site-name] console
```

```python
# Import from utility script
from education.update_percentages import run

# Run update
run()

# Or dry run first (doesn't commit)
run(commit=False)
```

---

## 🎯 Additional Update Functions

### Update Single Record

```python
from education.update_percentages import update_single_record

# Update specific record
result = update_single_record("STSR-2025-00001")
print(result)
```

**Output:**
```python
{
    'success': True,
    'name': 'STSR-2025-00001',
    'old_percentage': 0.0,
    'new_percentage': 85.0,
    'updated': True
}
```

### Update by Student Group

```python
from education.update_percentages import update_by_student_group

# Update all records in a specific student group
result = update_by_student_group("Grade 10 A")
```

**Output:**
```
Updating percentages for Student Group: Grade 10 A

Found 25 records in this student group...

✓ Alice Johnson - Mathematics: 0% → 85.00%
✓ Alice Johnson - English: 0% → 78.00%
✓ Bob Smith - Mathematics: 0% → 92.00%
...

✓ Changes committed!

Summary: 25 updated, 0 already correct, 0 errors
```

### Dry Run (Preview Changes)

```python
from education.update_percentages import run

# Preview changes without committing
result = run(commit=False)

print(f"Would update {result['updated']} records")
```

---

## 🚀 Step-by-Step Guide

### Step 1: Backup Your Data (Recommended)

```bash
# Backup database
bench --site [your-site-name] backup
```

### Step 2: Run Update

```bash
# Open bench console
bench --site [your-site-name] console
```

```python
# Import function
from education.education.doctype.student_term_subject_result.student_term_subject_result import update_all_percentages

# Preview first (optional)
# result = update_all_percentages(commit=False)

# Run update
update_all_percentages()
```

### Step 3: Verify Results

```bash
# Check a few records
bench --site [your-site-name] console
```

```python
import frappe

# Get random sample
results = frappe.get_all(
    "Student Term Subject Result",
    fields=["name", "score", "max_score", "percentage"],
    limit=10
)

for r in results:
    calculated = round((r.score / r.max_score) * 100, 2) if r.max_score > 0 else 0
    status = "✓" if r.percentage == calculated else "✗"
    print(f"{status} {r.name}: {r.score}/{r.max_score} = {r.percentage}% (expected: {calculated}%)")
```

### Step 4: Clear Cache

```bash
bench --site [your-site-name] clear-cache
bench restart
```

---

## 🔍 Verification

### Quick Verification Script

```python
import frappe
from frappe.utils import flt

# Get all records
results = frappe.get_all(
    "Student Term Subject Result",
    fields=["name", "score", "max_score", "percentage"]
)

incorrect = []
for r in results:
    if flt(r.max_score) > 0:
        expected = round((flt(r.score) / flt(r.max_score)) * 100, 2)
        if abs(flt(r.percentage) - expected) > 0.01:
            incorrect.append({
                "name": r.name,
                "score": r.score,
                "max_score": r.max_score,
                "current": r.percentage,
                "expected": expected
            })

if incorrect:
    print(f"Found {len(incorrect)} records with incorrect percentages:")
    for rec in incorrect[:10]:
        print(f"  {rec['name']}: {rec['current']}% (should be {rec['expected']}%)")
else:
    print("✓ All percentages are correct!")
```

---

## 💡 Use Cases

### Use Case 1: Initial Setup

**Scenario:** You just installed the system and imported historical data

**Action:**
```python
from education.update_percentages import run
run()  # Updates all existing records
```

### Use Case 2: Data Cleanup

**Scenario:** Found some records with incorrect percentages

**Action:**
```python
from education.update_percentages import run
run()  # Recalculates all percentages
```

### Use Case 3: Student Group Migration

**Scenario:** Moving students between groups, need to verify data

**Action:**
```python
from education.update_percentages import update_by_student_group
update_by_student_group("Grade 10 A")
update_by_student_group("Grade 10 B")
```

### Use Case 4: Audit Before Report

**Scenario:** Need to ensure all percentages are correct before generating report cards

**Action:**
```python
from education.update_percentages import run
# Dry run to see what would change
result = run(commit=False)
print(f"{result['updated']} records need updating")

# If looks good, commit
if result['updated'] > 0:
    run(commit=True)
```

---

## 🔧 Customization

### Change Rounding Precision

Edit `student_term_subject_result.py`:

```python
# Current: 2 decimal places
self.percentage = round(flt(self.score) / flt(self.max_score) * 100, 2)

# Change to 1 decimal place
self.percentage = round(flt(self.score) / flt(self.max_score) * 100, 1)

# No decimal places (integers only)
self.percentage = round(flt(self.score) / flt(self.max_score) * 100, 0)
```

### Add Validation for Percentage Range

```python
def calculate_percentage(self):
    """Calculate percentage based on score and max score"""
    if self.max_score and flt(self.max_score) > 0:
        self.percentage = round(flt(self.score) / flt(self.max_score) * 100, 2)
        
        # Ensure percentage is within 0-100 range
        if self.percentage < 0:
            self.percentage = 0
        elif self.percentage > 100:
            frappe.msgprint("Percentage exceeds 100%. Check score and max_score.")
    else:
        self.percentage = 0
```

---

## 📊 Statistics

After running `update_all_percentages()`, you can get statistics:

```python
from education.update_percentages import run

result = run()

print(f"Total records: {result['total']}")
print(f"Updated: {result['updated']}")
print(f"Already correct: {result['skipped']}")
print(f"Errors: {result['errors']}")

# Calculate percentage of records that needed updating
if result['total'] > 0:
    update_rate = (result['updated'] / result['total']) * 100
    print(f"\n{update_rate:.1f}% of records needed updating")
```

---

## 🐛 Troubleshooting

### Issue: "Permission Denied"

**Solution:**
```bash
# Ensure you're System Manager or have appropriate permissions
bench --site [site] console
```

```python
import frappe
frappe.set_user("Administrator")
# Then run update function
```

### Issue: "No records found"

**Cause:** No Student Term Subject Result records exist

**Solution:** Create some records first, then run update

### Issue: "Some records not updating"

**Check:**
1. Are records cancelled (docstatus = 2)?
2. Do they have valid score and max_score values?
3. Check error messages in output

**Debug:**
```python
# Get problem records
import frappe
results = frappe.get_all(
    "Student Term Subject Result",
    filters={"percentage": 0, "score": [">", 0]},
    fields=["name", "score", "max_score", "percentage"]
)
print(f"Found {len(results)} potential problem records")
```

---

## ✅ Best Practices

1. **Backup First:** Always backup before mass updates
2. **Dry Run:** Test with `commit=False` first
3. **Verify Sample:** Check a few records manually after update
4. **Clear Cache:** Clear cache after bulk updates
5. **Off-Peak:** Run bulk updates during low-usage times
6. **Monitor:** Watch for errors during execution

---

## 📁 Files Modified/Created

✅ **student_term_subject_result.py**
- Enhanced `calculate_percentage()` method
- Added `update_all_percentages()` function

✅ **update_percentages.py** (New)
- Standalone utility script
- Multiple update functions
- Comprehensive error handling

📄 **PERCENTAGE_CALCULATION_UPDATE.md** (This file)
- Complete documentation

---

## 🎉 Summary

**What:** Automatic percentage calculation for Student Term Subject Result

**How:** Calculates on every save: `percentage = (score / max_score) × 100`

**Benefits:**
- ✅ Always accurate
- ✅ No manual calculation needed
- ✅ Handles edge cases safely
- ✅ Easy to update existing records
- ✅ Prevents data inconsistencies

**Action Required:**
1. Update existing records: Run `update_all_percentages()`
2. Clear cache and restart
3. New records auto-calculate from now on

---

**Version:** 1.2.1  
**Date:** January 4, 2026  
**Status:** ✅ Complete and Tested  
**Breaking Changes:** None  

**All existing and new records will now have accurate, auto-calculated percentages!** 🎊
