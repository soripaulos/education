# 🎯 QUICK REFERENCE - Average Calculation

## Formula (v1.1.1)

```
Average = Total Score / Total Subjects in Program
```

**NOT:** ~~Total Score / Subjects with Results~~

---

## Example

**Program:** Grade 10 (5 subjects)  
**Student:** Alice

| Subject | Score |
|---------|-------|
| Math | 90 |
| English | 85 |
| Science | 0 |
| History | 0 |
| Geography | 0 |

**Calculation:**
```
Total = 90 + 85 + 0 + 0 + 0 = 175
Average = 175 / 5 = 35.00
```

---

## Why?

✅ Fair comparison (same denominator for all students)  
✅ Accurate ranking (complete work ranks higher)  
✅ Standard practice (like traditional grading)  
✅ Prevents gaming (can't boost by doing only easy subjects)  

---

## Apply Update

```bash
cd /path/to/frappe-bench
bench --site [site] clear-cache
bench restart
```

---

## Result

Students with **complete results** rank **higher** than students with **partial results**, even if partial results have high scores.

**Example:**
- Student A: 2 subjects done, scores 95+90 = 185 total → 185/5 = **37.00 avg**
- Student B: 5 subjects done, scores 80+78+75+82+80 = 395 total → 395/5 = **79.00 avg**
- **Student B ranks higher** ✅

---

**Version:** 1.1.1  
**Status:** ✅ Applied  
**Details:** See `AVERAGE_CALCULATION_UPDATE.md`
