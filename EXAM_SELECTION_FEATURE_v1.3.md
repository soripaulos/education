# Exam Selection Feature - v1.3

## 🎯 New Feature: Exam Filter

**Version:** 1.3  
**Date:** January 4, 2026  
**Status:** ✅ Complete and Tested  

---

## 🆕 What's New

### Exam Selection Filter

The report now includes a **new Exam(s) filter** that allows you to:

1. ✅ **Select specific exam(s)** to report on
2. ✅ **View individual exam scores** (when 1 exam selected)
3. ✅ **View summed scores** (when multiple exams selected)
4. ✅ **View all exams** (when no exam selected - default behavior)

---

## 📊 How It Works

### Scenario 1: No Exam Selected (Default)

**Behavior:** Shows **total scores from ALL exams**

**Example:**
- Student has taken: Midterm (45/50), Final (48/50), Quiz (20/20)
- Report shows: **113** (45 + 48 + 20)

**Column Header:** `Mathematics` (subject name only)

**Use Case:** Overall performance across entire term

---

### Scenario 2: Single Exam Selected

**Behavior:** Shows **individual scores for that specific exam**

**Example:**
- Filter: Select "Midterm Exam"
- Student's midterm score: 45/50
- Report shows: **45**

**Column Header:** `Mathematics (Midterm Exam)` ← Includes exam name!

**Use Case:** 
- Quick check of specific exam results
- Compare student performance on particular assessment
- Grade a specific test

---

### Scenario 3: Multiple Exams Selected

**Behavior:** Shows **summed scores from selected exams only**

**Example:**
- Filter: Select "Midterm Exam" + "Final Exam"
- Student scores: Midterm (45/50), Final (48/50)
- Report shows: **93** (45 + 48)
- Quiz score (20/20) is NOT included

**Column Header:** `Mathematics` (subject name only)

**Use Case:**
- Calculate term grades from specific assessments
- Exclude practice quizzes or bonus work
- Custom scoring combinations

---

## 🎯 Use Cases

### Use Case 1: Grade a Specific Exam

**Scenario:** Just completed midterm exams, want to see results

**Steps:**
1. Set filters:
   - Student Group: Grade 10 A
   - Academic Year: 2024-25
   - Semester: Term 1
   - **Exam(s): Midterm Exam** ← Select ONE exam
2. Run report

**Result:**
```
| Student | Name  | Math (Midterm) | English (Midterm) | Science (Midterm) | Total | Avg  | Rank |
|---------|-------|----------------|-------------------|-------------------|-------|------|------|
| STU-001 | Alice | 85             | 78                | 92                | 255   | 85.0 | 1    |
| STU-002 | Bob   | 78             | 82                | 88                | 248   | 82.7 | 2    |
```

**Note:** Column headers include exam name!

---

### Use Case 2: Calculate Term Grades

**Scenario:** Need final grades based on Midterm + Final only (exclude quizzes)

**Steps:**
1. Set filters:
   - Student Group: Grade 10 A
   - Academic Year: 2024-25
   - Semester: Term 1
   - **Exam(s): Midterm Exam, Final Exam** ← Select MULTIPLE exams
2. Run report

**Result:**
```
| Student | Name  | Math | English | Science | Total | Avg   | Rank |
|---------|-------|------|---------|---------|-------|-------|------|
| STU-001 | Alice | 180  | 165     | 185     | 530   | 176.7 | 1    |
| STU-002 | Bob   | 170  | 175     | 180     | 525   | 175.0 | 2    |
```

**Calculation:** 
- Alice Math: Midterm (85) + Final (95) = **180**
- Quizzes NOT included

---

### Use Case 3: Overall Term Performance

**Scenario:** Need complete picture including all assessments

**Steps:**
1. Set filters:
   - Student Group: Grade 10 A
   - Academic Year: 2024-25
   - Semester: Term 1
   - **Exam(s): (Leave empty)** ← No selection
2. Run report

**Result:**
```
| Student | Name  | Math | English | Science | Total | Avg   | Rank |
|---------|-------|------|---------|---------|-------|-------|------|
| STU-001 | Alice | 205  | 185     | 210     | 600   | 200.0 | 1    |
| STU-002 | Bob   | 195  | 195     | 205     | 595   | 198.3 | 2    |
```

**Calculation:** Includes ALL exams (Midterm + Final + Quizzes + everything)

---

## 📋 Report Message

The report now displays a message at the top indicating what's being shown:

### Message Examples:

**No exam selected:**
> Showing total scores from **all exams** for the selected filters.

**One exam selected:**
> Showing individual scores for exam: **Midterm Exam**

**Multiple exams selected:**
> Showing summed scores for exams: **Midterm Exam, Final Exam, Quiz 1**

---

## 🎨 Column Headers

### Single Exam Selected

Columns include the exam name in parentheses:

```
| Student | Math (Midterm) | English (Midterm) | Science (Midterm) |
```

**Benefit:** Clear which exam you're viewing

### Multiple or No Exams

Standard column headers:

```
| Student | Math | English | Science |
```

---

## 💡 Filter UI

### New Filter: Exam(s)

**Type:** MultiSelectList

**Features:**
- ✅ Searchable dropdown
- ✅ Select multiple exams
- ✅ Clear selection easily
- ✅ Shows all available Assessment Criteria

**Location:** Fourth filter (after Student Group, Academic Year, Semester)

**Example Options:**
- Midterm Exam
- Final Exam  
- Quiz 1
- Quiz 2
- Assignment 1
- Project
- Practical Test

---

## 🔄 Comparison Table

| Exam Selection | Behavior | Column Header | Use Case |
|----------------|----------|---------------|----------|
| **None** | Sum ALL exams | Math | Overall term performance |
| **1 exam** | Show THAT exam only | Math (Midterm) | Grade specific assessment |
| **2+ exams** | Sum SELECTED exams | Math | Custom combination |

---

## 📊 Examples

### Example 1: Student with Partial Data

**Student:** Alice  
**Available Results:**
- Midterm Exam: Math 85, English 78
- Final Exam: Math 95, English 87
- Quiz 1: Math 20

**Report Outputs:**

#### No Exam Selected (All):
```
Math: 200 (85+95+20)
English: 165 (78+87)
```

#### Only "Midterm Exam":
```
Math (Midterm): 85
English (Midterm): 78
```

#### "Midterm Exam" + "Final Exam":
```
Math: 180 (85+95)
English: 165 (78+87)
```

---

### Example 2: Class Comparison

**Scenario:** Compare midterm vs final performance

**Step 1:** Run with "Midterm Exam" only
- See midterm scores
- Note top performers

**Step 2:** Run with "Final Exam" only  
- See final scores
- Compare with midterm

**Step 3:** Run with both selected
- See combined scores
- Calculate improvement

---

## 🚀 How to Use

### Step 1: Access Report

```
Home > Education > Reports > Student Term Results Summary
```

### Step 2: Set Basic Filters

1. **Student Group:** Grade 10 A
2. **Academic Year:** 2024-25
3. **Semester:** Term 1 (optional)

### Step 3: Select Exam(s)

**Option A: Leave empty** (default)
- Shows all exams summed

**Option B: Select 1 exam**
- Click "Exam(s)" filter
- Search/select ONE exam
- Example: "Midterm Exam"

**Option C: Select multiple**
- Click "Exam(s)" filter
- Select multiple exams
- Example: "Midterm Exam", "Final Exam"

### Step 4: Run Report

Click **Refresh** or press `Ctrl + Enter`

---

## 🔍 Verification

### Check Report Message

Look at the message displayed above the report:

✅ **Correct:**
- "Showing individual scores for exam: Midterm Exam"
- "Showing summed scores for exams: Midterm Exam, Final Exam"
- "Showing total scores from all exams..."

### Check Column Headers

✅ **Single exam:** Headers should include exam name
- `Math (Midterm Exam)`

✅ **Multiple/None:** Standard headers
- `Math`

### Verify Data

Manual calculation:
1. Check a student's actual result records
2. Sum the scores for selected exams
3. Compare with report output

---

## 📁 Files Modified

### JavaScript:
✅ `student_term_results_summary.js`
- Added "exam" filter (MultiSelectList)
- Removed onload message

### Python (Main):
✅ `student_term_results_summary.py`
- Added exam filter parsing
- Modified `get_data()` to filter by exams
- Modified `get_columns()` to show exam name
- Added `get_report_message()` function

### Python (SQL Optimized):
✅ `student_term_results_summary_sql_optimized.py`
- Same improvements as main version
- Optimized SQL queries maintained

---

## ⚙️ Technical Details

### Filter Parsing

```python
selected_exams = filters.get("exam")
if selected_exams and isinstance(selected_exams, str):
    import json
    try:
        selected_exams = json.loads(selected_exams)
    except:
        selected_exams = [e.strip() for e in selected_exams.split(",") if e.strip()]
```

### Database Query

**Without exam filter:**
```sql
SELECT * FROM `tabStudent Term Subject Result`
WHERE student_group = 'Grade 10 A'
  AND academic_year = '2024-25'
```

**With exam filter:**
```sql
SELECT * FROM `tabStudent Term Subject Result`
WHERE student_group = 'Grade 10 A'
  AND academic_year = '2024-25'
  AND exam IN ('Midterm Exam', 'Final Exam')
```

### Column Labels

```python
if is_single_exam:
    subject_label = f"{subject} ({selected_exams[0]})"
else:
    subject_label = subject
```

---

## ✅ Benefits

| Benefit | Description |
|---------|-------------|
| **Flexibility** | Choose which exams to include |
| **Clarity** | Clear indication of what's being reported |
| **Accuracy** | Only selected exams are included |
| **Comparison** | Easy to compare different exam combinations |
| **Grading** | Grade specific assessments quickly |

---

## 🎓 Best Practices

### Practice 1: Grade Individual Assessments

After each major exam:
1. Select that exam only
2. Run report
3. Identify issues early
4. Provide targeted feedback

### Practice 2: Calculate Term Grades

At end of term:
1. Select only graded exams
2. Exclude practice/ungraded work
3. Generate final grades
4. Export for report cards

### Practice 3: Compare Performance

Track improvement:
1. Run with "Midterm" only → Save
2. Run with "Final" only → Save  
3. Compare results
4. Identify students who improved/declined

### Practice 4: Custom Weightings

For weighted grades:
1. Use report to get scores
2. Export to Excel
3. Apply weightings in spreadsheet
4. Example: Midterm 40% + Final 60%

---

## 🐛 Troubleshooting

### Issue: Exam filter not showing options

**Solution:**
- Ensure Assessment Criteria records exist
- Check if you have permission to view them
- Clear cache: `bench --site [site] clear-cache`

### Issue: Report shows 0 even though results exist

**Check:**
- Selected exam matches exam in result records (exact name)
- Results are for the correct student group
- Results are not cancelled (docstatus ≠ 2)

### Issue: Column headers not showing exam name

**Expected:** Only shows exam name when **exactly 1** exam selected

**Check:** Verify only one exam is selected in filter

---

## 📚 Summary

✅ **New Exam(s) filter added**
- Select specific exam(s) to report on
- MultiSelectList for easy selection

✅ **Three modes of operation:**
1. No selection → All exams summed
2. 1 exam → Individual exam scores (with exam name in header)
3. Multiple exams → Selected exams summed

✅ **Clear messaging:**
- Report message shows what's being displayed
- Column headers indicate exam (when single)

✅ **Flexible reporting:**
- Grade individual assessments
- Calculate custom combinations
- Compare different exam sets

---

**Version:** 1.3  
**Status:** ✅ Complete and Ready to Use  
**Breaking Changes:** None  
**Action Required:** Clear cache and restart bench  

---

**The report is now more flexible and powerful with exam-specific filtering!** 🎊
