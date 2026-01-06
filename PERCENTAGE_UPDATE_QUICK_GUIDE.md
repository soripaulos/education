# 🚀 Quick Guide - Update Percentages

## What Was Done

✅ **Percentage field now auto-calculates** on every save
- Formula: `percentage = (score / max_score) × 100`
- Rounded to 2 decimal places
- Handles edge cases (0 scores, 0 max_score)

---

## 🔄 Update Existing Records (Required)

### Step 1: Backup (Recommended)

```bash
bench --site [your-site-name] backup
```

### Step 2: Open Console

```bash
bench --site [your-site-name] console
```

### Step 3: Run Update

```python
from education.education.doctype.student_term_subject_result.student_term_subject_result import update_all_percentages

# Update all records
update_all_percentages()
```

**Expected Output:**
```
======================================================================
Updating Percentages for Student Term Subject Results
======================================================================

Found 150 records to process...

✓ Updated STSR-2025-00001: 0% → 85.00%
✓ Updated STSR-2025-00002: 0% → 78.00%
...

✓ Changes committed to database

======================================================================
Summary:
  Total records: 150
  Updated: 145
  Already correct: 5
  Errors: 0
======================================================================
```

### Step 4: Clear Cache

```bash
# Exit console (Ctrl+D)
bench --site [your-site-name] clear-cache
bench restart
```

**Done!** ✅

---

## 🎯 What Happens Now

### For New Records

**Automatic:**
1. User enters score and max_score
2. Saves record
3. **Percentage auto-calculates** ✅
4. No manual input needed

**Example:**
```
Score: 85
Max Score: 100
Percentage: 85.00% (auto-calculated)
```

### For Existing Records

**After running update script:**
- All percentages recalculated
- Based on current score and max_score values
- Accurate and consistent

---

## 📊 Examples

| Score | Max Score | Percentage |
|-------|-----------|------------|
| 85 | 100 | 85.00% |
| 47.5 | 50 | 95.00% |
| 0 | 100 | 0.00% |
| 100 | 100 | 100.00% |
| 10 | 0 | 0.00% (safe) |

---

## 🔍 Verify Update

```bash
bench --site [your-site-name] console
```

```python
import frappe

# Check sample records
results = frappe.get_all(
    "Student Term Subject Result",
    fields=["name", "score", "max_score", "percentage"],
    limit=5
)

for r in results:
    expected = round((r.score / r.max_score) * 100, 2) if r.max_score > 0 else 0
    match = "✓" if r.percentage == expected else "✗"
    print(f"{match} {r.name}: {r.score}/{r.max_score} = {r.percentage}%")
```

**Expected:**
```
✓ STSR-2025-00001: 85/100 = 85.0%
✓ STSR-2025-00002: 78/100 = 78.0%
✓ STSR-2025-00003: 92/100 = 92.0%
✓ STSR-2025-00004: 47.5/50 = 95.0%
✓ STSR-2025-00005: 100/100 = 100.0%
```

---

## 💡 Optional: Update by Student Group

If you only want to update specific student group:

```python
from education.update_percentages import update_by_student_group

# Update specific group only
update_by_student_group("Grade 10 A")
```

---

## 🐛 Troubleshooting

### No changes happening?

**Check:**
1. Run as Administrator or System Manager
2. Records have valid score and max_score
3. Run with `commit=True` (default)

### Want to preview first?

```python
# Dry run (doesn't save changes)
from education.update_percentages import run
result = run(commit=False)
print(f"Would update {result['updated']} records")
```

---

## ✅ Summary

**What to do:**
1. ✅ Backup database
2. ✅ Run `update_all_percentages()`
3. ✅ Clear cache & restart
4. ✅ Verify a few records

**Time needed:** 2-5 minutes

**Impact:**
- All existing records updated
- New records auto-calculate
- Consistent, accurate data

---

**Version:** 1.2.1  
**Status:** ✅ Ready to Apply  

**Full docs:** See `PERCENTAGE_CALCULATION_UPDATE.md` for complete details.
