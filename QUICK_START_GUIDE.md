# Student Term Results Summary Report - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites Checklist
- [ ] ERPNext with Education Module installed
- [ ] Terminal/SSH access to your Frappe bench
- [ ] System Manager or Administrator role

---

## 📦 Installation (2 minutes)

### Option 1: Automatic Setup (Recommended)

```bash
# Navigate to your bench directory
cd /path/to/frappe-bench

# Run setup script
bench --site [your-site-name] execute education.setup_student_report.setup

# Example:
bench --site myschool.local execute education.setup_student_report.setup
```

### Option 2: Manual Setup

```bash
cd /path/to/frappe-bench

# Step 1: Restart bench
bench restart

# Step 2: Clear cache
bench --site [your-site-name] clear-cache

# Step 3: Migrate
bench --site [your-site-name] migrate
```

---

## ✅ Verify Installation (1 minute)

```bash
bench --site [your-site-name] execute education.setup_student_report.verify_installation
```

Or manually:
1. Login to ERPNext
2. Press `Ctrl + K` (or `Cmd + K` on Mac)
3. Type: "Student Term Results Summary"
4. Report should appear in search results

---

## 🧪 Create Test Data (2 minutes)

### Only for testing/development environments!

```bash
bench --site [your-site-name] execute education.setup_student_report.create_sample_data
```

This creates:
- Academic Year: 2024-25
- Academic Term: Term 1 2024-25
- Program: Grade 10
- 5 Courses: Mathematics, English, Science, History, Geography
- 3 Exam Types: Midterm, Final, Quiz
- Student Group: Grade 10 A - Test
- 5 Sample Students with complete results

---

## 📊 Run Your First Report (1 minute)

1. **Access Report:**
   - Go to: **Home** > **Education** > **Reports**
   - Find: **Student Term Results Summary**
   - Click to open

2. **Set Filters:**
   - **Student Group:** Grade 10 A - Test *(if you created test data)*
   - **Academic Year:** 2024-25
   - **Semester:** Term 1 2024-25 *(optional)*

3. **Run Report:**
   - Click **Refresh** or press `Ctrl + Enter`

4. **View Results:**
   - See tabulated student data
   - Check the bar chart below
   - Export if needed (Menu > Export > Excel)

---

## 📁 File Structure

```
/workspace/
│
├── QUICK_START_GUIDE.md                        ← You are here
├── STUDENT_REPORT_INSTALLATION_GUIDE.md        ← Detailed installation
├── setup_student_report.py                     ← Setup automation script
│
└── education/education/report/student_term_results_summary/
    ├── __init__.py                             ← Empty init
    ├── student_term_results_summary.json       ← Report metadata
    ├── student_term_results_summary.js         ← Filter configuration
    ├── student_term_results_summary.py         ← Main report logic
    ├── student_term_results_summary_sql_optimized.py  ← Fast version
    ├── README.md                               ← Report documentation
    └── USAGE_EXAMPLES.md                       ← Usage examples
```

---

## 🎯 Report Features

### Input (Filters)
- ✅ **Student Group** (Required) - Select class/batch
- ✅ **Academic Year** (Required) - Select year
- ✅ **Semester** (Optional) - Filter by term

### Output (Columns)
| Column | Description |
|--------|-------------|
| Student ID | Link to student record |
| Student Name | Full name of student |
| Student Group | The selected class/group |
| [Subject 1, 2, ...N] | Total score for each subject (across all exams) |
| Total | Sum of all subject scores |
| Average | Total ÷ Number of subjects |
| Rank | Position based on average (1 = highest) |

### Additional Features
- 📊 **Visual Chart:** Bar chart showing top 10 students
- 📥 **Export:** Excel, CSV, PDF formats
- 🖨️ **Print:** Printer-friendly format
- 📧 **Email:** Schedule automated reports

---

## 🔧 Common Commands

```bash
# Navigate to bench
cd /path/to/frappe-bench

# Setup report
bench --site [site] execute education.setup_student_report.setup

# Verify installation
bench --site [site] execute education.setup_student_report.verify_installation

# Create test data
bench --site [site] execute education.setup_student_report.create_sample_data

# Clear cache
bench --site [site] clear-cache

# Restart bench
bench restart

# Rebuild (after JS changes)
bench build --force

# Open console (for debugging)
bench --site [site] console
```

---

## 🐛 Troubleshooting

### Problem: Report not showing

**Solution:**
```bash
bench --site [site] clear-cache
bench restart
```

### Problem: No data in report

**Possible Causes:**
1. Results not submitted (docstatus = 0)
2. Students not added to Student Group
3. Wrong filters selected

**Check:**
```bash
bench --site [site] console
```
```python
import frappe

# Check if results exist
frappe.get_all('Student Term Subject Result', 
    filters={'docstatus': 1}, 
    limit=5)
```

### Problem: Permission denied

**Solution:**
```python
# In bench console
import frappe
report = frappe.get_doc('Report', 'Student Term Results Summary')
report.append('roles', {'role': 'Education Manager'})
report.save()
frappe.db.commit()
```

### Problem: Report is slow

**Solution:** Use SQL-optimized version
```python
# Edit student_term_results_summary.py
# Change import at line 1:
from education.education.report.student_term_results_summary.student_term_results_summary_sql_optimized import execute
```

---

## 📚 Documentation Links

| Document | Description |
|----------|-------------|
| [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md) | This file - Fast setup |
| [STUDENT_REPORT_INSTALLATION_GUIDE.md](./STUDENT_REPORT_INSTALLATION_GUIDE.md) | Complete installation guide |
| [README.md](./education/education/report/student_term_results_summary/README.md) | Report documentation |
| [USAGE_EXAMPLES.md](./education/education/report/student_term_results_summary/USAGE_EXAMPLES.md) | Usage examples and code samples |

---

## 🎓 Example Usage

### Scenario 1: End of Term Report

**Goal:** Generate report cards for Grade 10 A students

**Steps:**
1. Ensure all results are submitted
2. Open report
3. Filter: Student Group = "Grade 10 A", Academic Year = "2024-25", Semester = "Term 1"
4. Export to Excel
5. Print or email to parents

### Scenario 2: Identify Top Performers

**Goal:** Find top 5 students for awards

**Steps:**
1. Run report for the student group
2. Check "Rank" column
3. Students with Rank 1, 2, 3, 4, 5 are top performers
4. View chart for visual representation

### Scenario 3: Track Class Progress

**Goal:** Compare term 1 vs term 2 performance

**Steps:**
1. Run report with Semester = "Term 1"
2. Note class average
3. Run report with Semester = "Term 2"
4. Compare averages

---

## 💡 Pro Tips

1. **Submit Results First:** Only submitted results (green button) appear in report
2. **Use Semester Filter:** Improves performance with large datasets
3. **Export for Analysis:** Use Excel for charts, pivot tables, and conditional formatting
4. **Schedule Reports:** Set up Auto Email Report for weekly/monthly updates
5. **Customize Columns:** Edit Python file to add/remove columns
6. **Add Database Indexes:** For faster queries on large datasets
7. **Use SQL Version:** Switch to SQL-optimized version for 100+ students

---

## 🚨 Important Notes

### Data Requirements
For the report to work, you MUST have:
- ✅ Students created in ERPNext
- ✅ Student Groups with students added
- ✅ Academic Year configured
- ✅ Academic Terms configured
- ✅ Courses (Subjects) created
- ✅ Assessment Criteria (Exams) created
- ✅ **Student Term Subject Result records SUBMITTED** ← Most important!

### Submission Status
The report ONLY shows results where `docstatus = 1` (submitted).

**To submit a result:**
1. Open Student Term Subject Result
2. Fill all required fields
3. Click **Save**
4. Click **Submit** (green button)
5. Result now appears in report

---

## 📧 Support

For issues or questions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Review [STUDENT_REPORT_INSTALLATION_GUIDE.md](./STUDENT_REPORT_INSTALLATION_GUIDE.md)
3. Check [USAGE_EXAMPLES.md](./education/education/report/student_term_results_summary/USAGE_EXAMPLES.md)
4. Contact your system administrator
5. Post on Frappe Forum: https://discuss.frappe.io

---

## ✅ Quick Checklist

- [ ] Report files in correct location
- [ ] Bench restarted
- [ ] Cache cleared
- [ ] Permissions configured
- [ ] Test data created (optional)
- [ ] First report run successfully
- [ ] Export tested
- [ ] Documentation reviewed

---

## 🎉 You're All Set!

The Student Term Results Summary Report is now ready to use.

**Next Steps:**
1. Create real student data (if not already done)
2. Submit results for current term
3. Run report and verify output
4. Share with teachers/administrators
5. Set up scheduled email reports (optional)

**Need Help?**
- Detailed Guide: [STUDENT_REPORT_INSTALLATION_GUIDE.md](./STUDENT_REPORT_INSTALLATION_GUIDE.md)
- Examples: [USAGE_EXAMPLES.md](./education/education/report/student_term_results_summary/USAGE_EXAMPLES.md)
- Frappe Docs: https://frappeframework.com/docs
- ERPNext Docs: https://docs.erpnext.com

---

**Happy Reporting! 📊**
