# Student Term Results Summary Report

## Overview
This report generates a comprehensive tabulated view of student results from the `Student Term Subject Result` doctype. It displays:
- Student names (filtered by Student Group)
- Student Group in the first column
- Dynamic columns for each subject showing total exam scores
- Total column (sum of all subject scores)
- Average column (total divided by number of subjects)
- Rank column (based on averages compared to other students)

## Features
- ✅ Complex SQL query-based data extraction
- ✅ Dynamic column generation based on subjects in student group
- ✅ Automatic total and average calculation
- ✅ Rank calculation with handling of ties
- ✅ Filters: Student Group, Academic Year, Semester (optional)
- ✅ Visual chart showing top 10 student averages
- ✅ Only includes submitted (docstatus = 1) results

## Installation Steps

### Step 1: Install the Report Files
The report files have been created in:
```
education/education/report/student_term_results_summary/
├── __init__.py
├── student_term_results_summary.json
├── student_term_results_summary.js
├── student_term_results_summary.py
└── README.md
```

### Step 2: Restart Frappe Bench
After adding the report files, restart your bench to load the new report:

```bash
cd /path/to/your/frappe-bench
bench restart
```

### Step 3: Clear Cache
Clear the cache to ensure ERPNext recognizes the new report:

```bash
bench --site [your-site-name] clear-cache
```

Or from within ERPNext:
1. Go to: **Home > Settings > Clear Cache**
2. Click **Clear Cache**

### Step 4: Migrate (if needed)
If the report doesn't appear, run migration:

```bash
bench --site [your-site-name] migrate
```

### Step 5: Set Permissions
1. Go to: **Home > Reports > Student Term Results Summary**
2. Click on the report name
3. Ensure roles are assigned:
   - Education Manager
   - Instructor
   - Academics User

### Step 6: Access the Report
1. Go to: **Home > Education > Reports**
2. Find **Student Term Results Summary**
3. Or search "Student Term Results Summary" in the awesome bar

## Usage

### Filters
1. **Student Group** (Required): Select the student group to view results for
2. **Academic Year** (Required): Select the academic year
3. **Semester** (Optional): Filter by specific semester/academic term

### Report Columns
1. **Student ID**: Link to student record
2. **Student Name**: Name of the student
3. **Student Group**: The selected student group
4. **Subject Columns** (Dynamic): One column per subject showing total scores across all exams
5. **Total**: Sum of all subject scores for that student
6. **Average**: Average score (Total ÷ Number of subjects)
7. **Rank**: Student's rank based on average (1 = highest)

### Export Options
- Export to Excel
- Export to CSV
- Export to PDF
- Print

## Data Requirements

### Prerequisites
1. **Student Term Subject Result** records must be submitted (docstatus = 1)
2. Students must be added to the Student Group
3. Results must have:
   - Student
   - Student Group
   - Academic Year
   - Semester
   - Subject (Course)
   - Exam (Assessment Criteria)
   - Score

### Sample Data Flow
```
Student Term Subject Result
├── Student: STU-001
├── Student Group: Grade 10 A
├── Academic Year: 2024-25
├── Semester: Term 1
├── Subject: Mathematics
├── Exam: Midterm
├── Score: 85
└── Max Score: 100
```

The report will:
1. Group all exams for each subject per student
2. Sum the scores for each subject
3. Calculate total and average across all subjects
4. Rank students by average

## Customization

### Modify Ranking Logic
To change how ranks are calculated, edit the `calculate_ranks()` function in `student_term_results_summary.py`:

```python
def calculate_ranks(data):
    # Current: Ranks by average (descending)
    # Modify sorting key to change ranking criteria
    sorted_data = sorted(data, key=lambda x: x.average, reverse=True)
    # ... rest of function
```

### Change Chart Display
To modify the chart (e.g., show more/fewer students), edit the `get_chart()` function:

```python
def get_chart(data):
    # Change [:10] to [:20] to show top 20 students
    labels = [row.student_name for row in data[:10]]
    # ... rest of function
```

### Add More Filters
To add additional filters, edit `student_term_results_summary.js`:

```javascript
frappe.query_reports['Student Term Results Summary'] = {
  filters: [
    // ... existing filters
    {
      fieldname: 'grade',
      label: __('Grade'),
      fieldtype: 'Link',
      options: 'Program',
    },
  ],
}
```

Then update the `get_data()` function in the Python file to handle the new filter.

## Troubleshooting

### Report Not Showing
1. Clear cache: `bench --site [site] clear-cache`
2. Restart bench: `bench restart`
3. Check if report exists: `bench --site [site] console`
   ```python
   frappe.get_doc('Report', 'Student Term Results Summary')
   ```

### No Data Displayed
1. Verify Student Term Subject Result records exist and are submitted
2. Check if students are in the selected Student Group
3. Ensure filters match existing data
4. Check if results have the correct student_group field value

### Permission Issues
1. Go to: **Report > Student Term Results Summary**
2. Add required roles in the Roles table
3. Save and refresh

### Performance Issues
If the report is slow with large datasets:
1. Add database indexes on frequently queried fields
2. Use the SQL-optimized version (see below)
3. Limit the date range with additional filters

## Advanced: SQL-Optimized Version

For better performance with large datasets, you can use the SQL-optimized version which uses fewer database queries. Create a file `student_term_results_summary_sql.py` with direct SQL queries.

## Support
For issues or feature requests, please contact your system administrator or refer to the Frappe ERPNext documentation.

## License
Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
For license information, please see license.txt
