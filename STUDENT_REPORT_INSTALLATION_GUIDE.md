# Student Term Results Summary Report - Complete Installation Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Testing the Report](#testing-the-report)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Usage](#advanced-usage)

---

## Overview

This guide provides step-by-step instructions for installing and configuring the **Student Term Results Summary** report in your Frappe ERPNext Education module.

### What This Report Does
- Displays student results in a tabulated format
- Groups data by Student Group
- Shows dynamic columns for each subject (course)
- Calculates totals, averages, and ranks automatically
- Uses complex SQL queries for efficient data retrieval

### Report Structure
```
Row: Each student in the selected Student Group
Columns:
  - Student ID (Link to Student)
  - Student Name
  - Student Group
  - [Subject 1] - Total score across all exams
  - [Subject 2] - Total score across all exams
  - [Subject N] - Total score across all exams
  - Total - Sum of all subject scores
  - Average - Total ÷ Number of subjects
  - Rank - Based on average (1 = highest)
```

---

## Prerequisites

### System Requirements
- Frappe Framework 13+ or 14+
- ERPNext with Education Module installed
- Access to bench commands (SSH/terminal access)
- System Manager or Administrator role

### Data Requirements
Before using the report, ensure you have:
1. **Student records** created in ERPNext
2. **Student Groups** created with students added
3. **Academic Year** configured
4. **Academic Terms** (Semesters) configured
5. **Courses** (Subjects) created
6. **Assessment Criteria** (Exams) created
7. **Student Term Subject Result** records created and **submitted**

---

## Installation Steps

### Step 1: Verify Report Files

The report files should be located in:
```
education/education/report/student_term_results_summary/
├── __init__.py
├── student_term_results_summary.json
├── student_term_results_summary.js
├── student_term_results_summary.py
└── README.md
```

To verify the files exist:
```bash
cd /path/to/frappe-bench/apps/education
ls -la education/education/report/student_term_results_summary/
```

### Step 2: Navigate to Bench Directory

```bash
cd /path/to/frappe-bench
# Example: cd /home/frappe/frappe-bench
```

### Step 3: Restart Bench Services

Restart all bench services to load the new report:

```bash
bench restart
```

If you're using production mode with supervisor:
```bash
sudo supervisorctl restart all
```

Or restart specific processes:
```bash
sudo supervisorctl restart frappe-bench-web:
sudo supervisorctl restart frappe-bench-workers:
```

### Step 4: Clear Site Cache

Clear the cache for your site (replace `[site-name]` with your actual site name):

```bash
bench --site [site-name] clear-cache
```

Example:
```bash
bench --site myschool.local clear-cache
```

To clear cache for all sites:
```bash
bench clear-cache
```

### Step 5: Run Migration (Optional but Recommended)

```bash
bench --site [site-name] migrate
```

This ensures the report is registered in the database.

### Step 6: Rebuild Assets (For JavaScript Changes)

If you make any changes to the `.js` file:

```bash
bench build
```

Or for development mode:
```bash
bench build --force
```

### Step 7: Verify Installation

Check if the report is installed:

```bash
bench --site [site-name] console
```

Then in the console:
```python
import frappe
frappe.get_doc('Report', 'Student Term Results Summary')
```

If successful, you'll see the report document details.

---

## Configuration

### Setting Up Permissions

1. **Via ERPNext UI:**
   - Go to: **Home** > **Customization** > **Report**
   - Search: "Student Term Results Summary"
   - Click on the report
   - Scroll to **Roles** section
   - Ensure these roles are added:
     - Education Manager
     - Instructor
     - Academics User
     - System Manager
   - Save

2. **Via Bench Console:**
   ```bash
   bench --site [site-name] console
   ```
   
   ```python
   import frappe
   report = frappe.get_doc('Report', 'Student Term Results Summary')
   
   # Add roles if not present
   roles = ['Education Manager', 'Instructor', 'Academics User']
   for role in roles:
       if not any(r.role == role for r in report.roles):
           report.append('roles', {'role': role})
   
   report.save()
   frappe.db.commit()
   ```

### Accessing the Report

**Method 1: Via Module**
1. Login to ERPNext
2. Go to **Home** > **Education** > **Reports**
3. Find **Student Term Results Summary** under "Education Reports"
4. Click to open

**Method 2: Via Awesome Bar**
1. Press `Ctrl + K` (or `Cmd + K` on Mac)
2. Type: "Student Term Results Summary"
3. Press Enter

**Method 3: Direct URL**
```
https://your-site.com/app/query-report/Student%20Term%20Results%20Summary
```

---

## Testing the Report

### Create Sample Data (For Testing)

If you don't have data, create sample records:

#### 1. Create a Student Group
```
Home > Education > Student Group > New
- Academic Year: 2024-25
- Group Based On: Batch
- Student Group Name: Grade 10 A
- Add students to the group
```

#### 2. Create Student Term Subject Results
```
Home > Education > Student Term Subject Result > New

Record 1:
- Student: [Select Student]
- Academic Year: 2024-25
- Semester: Term 1
- Subject: Mathematics
- Student Group: Grade 10 A
- Grade: Grade 10
- Exam: Midterm Exam
- Score: 85
- Maximum Score: 100
- Submit the document

Record 2:
- Student: [Same Student]
- Subject: English
- Exam: Midterm Exam
- Score: 78
- Maximum Score: 100
- Submit the document

[Create similar records for multiple students and subjects]
```

### Running the Report

1. Open the report: **Student Term Results Summary**
2. Set filters:
   - **Student Group**: Grade 10 A
   - **Academic Year**: 2024-25
   - **Semester**: Term 1 (optional)
3. Click **Refresh** or press `Ctrl + Enter`

### Expected Output

You should see a table with:
```
| Student ID | Student Name | Student Group | Mathematics | English | Total | Average | Rank |
|------------|--------------|---------------|-------------|---------|-------|---------|------|
| STU-001    | John Doe     | Grade 10 A    | 85.00       | 78.00   | 163.00| 81.50   | 1    |
| STU-002    | Jane Smith   | Grade 10 A    | 92.00       | 88.00   | 180.00| 90.00   | 1    |
```

And a bar chart showing top 10 students by average.

---

## Troubleshooting

### Issue 1: Report Not Appearing in List

**Symptoms:** Report doesn't show up in Education > Reports

**Solutions:**
```bash
# Clear cache
bench --site [site-name] clear-cache

# Restart bench
bench restart

# Rebuild if needed
bench build

# Check if report exists in database
bench --site [site-name] console
```
```python
frappe.db.exists('Report', 'Student Term Results Summary')
```

### Issue 2: "Report Not Found" Error

**Symptoms:** Error message when trying to open report

**Solutions:**
```bash
# Reinstall the report
bench --site [site-name] console
```
```python
import frappe
from frappe.modules.import_file import import_file_by_path

# Import the report JSON
path = 'apps/education/education/education/report/student_term_results_summary/student_term_results_summary.json'
import_file_by_path(path)
frappe.db.commit()
```

### Issue 3: Permission Denied

**Symptoms:** "Insufficient Permission for Report"

**Solutions:**
1. Add role permissions (see Configuration section)
2. Or grant report access via Role Permission Manager:
   ```
   Home > Users and Permissions > Role Permission Manager
   - Document Type: Report
   - Role: [Your Role]
   - Add permission
   ```

### Issue 4: No Data Showing

**Symptoms:** Report loads but shows empty table

**Possible Causes & Solutions:**

1. **No submitted results:**
   - Check: Go to Student Term Subject Result list
   - Solution: Submit your result documents (Green "Submit" button)
   - Verify: Only submitted documents (docstatus = 1) appear in report

2. **Students not in Student Group:**
   - Check: Open the Student Group and verify students are added
   - Solution: Add students to the group's "Students" table

3. **Filter mismatch:**
   - Check: Verify filters match your data
   - Solution: Try different Student Group or Academic Year

4. **Database check:**
   ```bash
   bench --site [site-name] console
   ```
   ```python
   import frappe
   
   # Check if results exist
   results = frappe.db.get_all('Student Term Subject Result', 
       filters={'docstatus': 1}, 
       limit=5)
   print(results)
   
   # Check specific student group
   results = frappe.db.get_all('Student Term Subject Result',
       filters={'student_group': 'Grade 10 A', 'docstatus': 1},
       fields=['student', 'subject', 'score'])
   print(results)
   ```

### Issue 5: Report is Slow

**Symptoms:** Report takes long time to load

**Solutions:**

1. **Add Database Indexes:**
   ```bash
   bench --site [site-name] console
   ```
   ```python
   import frappe
   
   # Add indexes for frequently queried fields
   frappe.db.sql("""
       CREATE INDEX IF NOT EXISTS idx_student_group 
       ON `tabStudent Term Subject Result`(student_group, academic_year, docstatus)
   """)
   
   frappe.db.sql("""
       CREATE INDEX IF NOT EXISTS idx_student 
       ON `tabStudent Term Subject Result`(student, subject, docstatus)
   """)
   
   frappe.db.commit()
   ```

2. **Limit data range:** Add semester filter to reduce dataset

3. **Use the SQL-optimized version** (see Advanced Usage)

### Issue 6: JavaScript Errors in Console

**Symptoms:** Browser console shows errors

**Solutions:**
```bash
# Rebuild JavaScript assets
bench build --force

# Clear browser cache
# Press Ctrl + Shift + Delete (or Cmd + Shift + Delete on Mac)
# Select "Cached images and files"
# Clear

# Reload page with hard refresh
# Press Ctrl + Shift + R (or Cmd + Shift + R on Mac)
```

---

## Advanced Usage

### Customizing the Report

#### 1. Modify Column Width

Edit `student_term_results_summary.py`, find `get_columns()` function:

```python
{
    "fieldname": "student_name",
    "label": _("Student Name"),
    "fieldtype": "Data",
    "width": 250  # Change this value
}
```

#### 2. Change Ranking Logic

To rank by total instead of average, edit `calculate_ranks()` function:

```python
def calculate_ranks(data):
    # Change 'average' to 'total'
    sorted_data = sorted(data, key=lambda x: x.total, reverse=True)
    # ... rest remains same
```

#### 3. Add Percentage Column

Add to `get_columns()`:

```python
{
    "fieldname": "percentage",
    "label": _("Percentage"),
    "fieldtype": "Percent",
    "width": 100,
    "precision": 2
}
```

And in `get_data()`, calculate percentage:

```python
# After calculating average
if subject_count > 0:
    total_max = subject_count * 100  # Assuming each subject max is 100
    row.percentage = (grand_total / total_max) * 100
```

#### 4. Add Grade Column

Based on average, assign letter grades:

```python
def get_grade(average):
    if average >= 90:
        return 'A+'
    elif average >= 80:
        return 'A'
    elif average >= 70:
        return 'B'
    elif average >= 60:
        return 'C'
    else:
        return 'F'

# In get_data(), after calculating average:
row.grade = get_grade(row.average)
```

And add column:

```python
{
    "fieldname": "grade",
    "label": _("Grade"),
    "fieldtype": "Data",
    "width": 80
}
```

### Export and Scheduling

#### Export to Excel
1. Open the report
2. Click **Menu** (3 dots) > **Export**
3. Select **Excel**

#### Schedule Report Email

```python
# Create a scheduled report
bench --site [site-name] console

import frappe

# Create Auto Email Report
doc = frappe.get_doc({
    'doctype': 'Auto Email Report',
    'report': 'Student Term Results Summary',
    'report_type': 'Script Report',
    'user': 'administrator@example.com',
    'enabled': 1,
    'frequency': 'Weekly',
    'day_of_week': 'Monday',
    'filters': {
        'student_group': 'Grade 10 A',
        'academic_year': '2024-25'
    },
    'recipients': [
        {'email_address': 'principal@school.com'}
    ]
})
doc.insert()
frappe.db.commit()
```

### API Access

Access the report data programmatically:

```python
import frappe
from frappe.desk.query_report import run

# Run the report
result = run('Student Term Results Summary', filters={
    'student_group': 'Grade 10 A',
    'academic_year': '2024-25'
})

columns = result['columns']
data = result['result']

# Process data
for row in data:
    print(f"{row['student_name']}: {row['average']}")
```

### Creating a Custom Dashboard Widget

Add report to dashboard:

1. Go to **Home** > **Education** > **Education Dashboard**
2. Click **Add Chart**
3. Select **Report** as source
4. Choose **Student Term Results Summary**
5. Configure filters
6. Save

---

## File Structure Reference

```
education/education/report/student_term_results_summary/
│
├── __init__.py                              # Empty init file
│
├── student_term_results_summary.json        # Report metadata
│   ├── Report name and module
│   ├── Report type (Script Report)
│   ├── Reference DocType
│   └── Roles/permissions
│
├── student_term_results_summary.js          # Frontend filters and UI
│   ├── Filter definitions
│   ├── Filter dependencies
│   └── UI callbacks
│
├── student_term_results_summary.py          # Backend logic (Python)
│   ├── execute() - Main entry point
│   ├── get_data() - Data retrieval
│   ├── get_columns() - Column definitions
│   ├── get_subjects_for_group() - Subject list
│   ├── calculate_ranks() - Ranking logic
│   └── get_chart() - Chart generation
│
└── README.md                                # Documentation
```

---

## Quick Reference Commands

```bash
# Installation
bench restart
bench --site [site] clear-cache
bench --site [site] migrate

# Development
bench build --force
bench --site [site] console

# Debugging
bench --site [site] mariadb
SELECT * FROM `tabStudent Term Subject Result` LIMIT 10;

# Logs
bench watch
tail -f ~/frappe-bench/logs/[site].error.log
```

---

## Support and Resources

- **Frappe Documentation:** https://frappeframework.com/docs
- **ERPNext Documentation:** https://docs.erpnext.com
- **Education Module:** https://docs.erpnext.com/docs/user/manual/en/education
- **Frappe Forum:** https://discuss.frappe.io

---

## Summary Checklist

- [ ] Report files created in correct directory
- [ ] Bench restarted
- [ ] Cache cleared
- [ ] Migration run
- [ ] Permissions configured
- [ ] Sample data created
- [ ] Report accessible from Education module
- [ ] Filters working correctly
- [ ] Data displaying properly
- [ ] Export functions tested

---

**Installation Complete! 🎉**

You can now use the Student Term Results Summary report to generate comprehensive student performance reports.
