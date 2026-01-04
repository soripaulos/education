# 🚀 Quick Guide - Exam Selection Feature

## ✅ New Feature Added (v1.3)

**What:** Exam filter added to report

**Benefits:**
- ✅ Select specific exam(s) to report on
- ✅ View individual exam scores
- ✅ View summed scores from multiple exams

---

## 🎯 How to Use

### Step 1: Apply Update

```bash
cd /path/to/frappe-bench
bench --site [your-site-name] clear-cache
bench restart
```

### Step 2: Run Report

```
Home > Education > Reports > Student Term Results Summary
```

### Step 3: Select Filters

**Required:**
1. Student Group: Grade 10 A
2. Academic Year: 2024-25

**Optional:**
3. Semester: Term 1
4. **Exam(s): (NEW!)** ← Select exam(s)

### Step 4: Choose Exam Mode

**Option A: No exam selected**
- Shows ALL exams summed together
- Default behavior

**Option B: Select 1 exam**
- Shows individual exam scores
- Column headers include exam name
- Example: `Math (Midterm Exam)`

**Option C: Select multiple exams**
- Shows summed scores from selected exams only
- Excludes other exams

---

## 📊 Examples

### Example 1: Grade Midterm Exam

**Goal:** See midterm results only

**Filters:**
- Exam(s): **Midterm Exam** ← Select ONE

**Result:**
```
| Student | Math (Midterm) | English (Midterm) | Total | Avg  | Rank |
|---------|----------------|-------------------|-------|------|------|
| Alice   | 85             | 78                | 163   | 81.5 | 1    |
| Bob     | 78             | 82                | 160   | 80.0 | 2    |
```

---

### Example 2: Calculate Term Grade

**Goal:** Combine Midterm + Final (exclude quizzes)

**Filters:**
- Exam(s): **Midterm Exam, Final Exam** ← Select MULTIPLE

**Result:**
```
| Student | Math | English | Total | Avg   | Rank |
|---------|------|---------|-------|-------|------|
| Alice   | 180  | 165     | 345   | 172.5 | 1    |
| Bob     | 170  | 175     | 345   | 172.5 | 1    |
```

**Calculation:** Midterm + Final scores only

---

### Example 3: Overall Performance

**Goal:** See all assessments

**Filters:**
- Exam(s): **(Leave empty)** ← No selection

**Result:**
```
| Student | Math | English | Total | Avg  | Rank |
|---------|------|---------|-------|------|------|
| Alice   | 205  | 185     | 390   | 195  | 1    |
| Bob     | 195  | 195     | 390   | 195  | 1    |
```

**Calculation:** ALL exams (Midterm + Final + Quizzes + etc.)

---

## 💡 Quick Tips

### Tip 1: Check Report Message

Look at the top of the report for confirmation:
- "Showing individual scores for exam: **Midterm Exam**"
- "Showing summed scores for exams: **Midterm Exam, Final Exam**"
- "Showing total scores from **all exams**..."

### Tip 2: Column Headers

**Single exam:** Headers show exam name
- `Math (Midterm Exam)` ✅

**Multiple/None:** Standard headers
- `Math` ✅

### Tip 3: Compare Exams

To compare performance:
1. Run with "Midterm" only
2. Export/save results
3. Run with "Final" only
4. Compare side by side

---

## 🎯 Use Cases

| Scenario | Exam Selection | Use |
|----------|----------------|-----|
| Grade specific test | 1 exam | Quick grading |
| Calculate term grade | Multiple | Custom combinations |
| Overall performance | None | Complete picture |
| Compare assessments | Run multiple times | Track improvement |

---

## 🔍 Verification

After setting filters, verify:

✅ Report message matches selection  
✅ Column headers correct  
✅ Data matches expected exams  
✅ Totals calculated correctly  

---

## 📋 Quick Comparison

### Before (v1.2):
- No exam filter
- Always showed all exams summed
- No way to view individual exams

### After (v1.3):
- ✅ Exam filter added
- ✅ Choose which exams to include
- ✅ View individual or summed scores
- ✅ Flexible reporting

---

## ✅ Summary

**3 Modes:**

1. **No selection** → All exams
2. **1 exam** → That exam only (shows exam name)
3. **2+ exams** → Selected exams summed

**Benefits:**
- More control over reporting
- Grade specific assessments
- Calculate custom combinations
- Compare different exams

---

**Version:** 1.3  
**Time to apply:** 30 seconds  
**Action:** Clear cache & restart  

**See full docs:** `EXAM_SELECTION_FEATURE_v1.3.md`

🎊 **Enjoy flexible exam filtering!** 🎊
