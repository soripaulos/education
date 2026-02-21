# Student Term Results Summary Report - Usage Examples

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [Common Scenarios](#common-scenarios)
3. [Advanced Queries](#advanced-queries)
4. [Customization Examples](#customization-examples)
5. [API Usage](#api-usage)
6. [Troubleshooting Examples](#troubleshooting-examples)

---

## Basic Usage

### Example 1: View Results for a Single Class

**Scenario:** You want to see results for Grade 10 A students in Term 1 of 2024-25.

**Steps:**
1. Navigate to: **Home > Education > Reports > Student Term Results Summary**
2. Set filters:
   - **Student Group:** Grade 10 A
   - **Academic Year:** 2024-25
   - **Semester:** Term 1
3. Click **Refresh** or press `Ctrl + Enter`

**Expected Output:**
```
| Student ID | Student Name  | Student Group | Math | English | Science | Total | Average | Rank |
|------------|---------------|---------------|------|---------|---------|-------|---------|------|
| STU-001    | Alice Johnson | Grade 10 A    | 180  | 165     | 175     | 520   | 173.33  | 1    |
| STU-002    | Bob Smith     | Grade 10 A    | 170  | 170     | 160     | 500   | 166.67  | 2    |
| STU-003    | Charlie Brown | Grade 10 A    | 165  | 160     | 170     | 495   | 165.00  | 3    |
```

**Interpretation:**
- **Total:** Sum of all subject scores (Math + English + Science)
- **Average:** Total divided by 3 subjects
- **Rank:** Alice is ranked 1st with highest average of 173.33

---

### Example 2: View Results Across All Terms

**Scenario:** View all results for Grade 10 A across all terms in the academic year.

**Steps:**
1. Open report
2. Set filters:
   - **Student Group:** Grade 10 A
   - **Academic Year:** 2024-25
   - **Semester:** (Leave empty)
3. Click **Refresh**

**Expected Output:**
Now includes scores from all terms (Term 1, Term 2, Term 3) summed together for each subject.

---

### Example 3: Export to Excel

**Scenario:** Export report data for further analysis.

**Steps:**
1. Run the report with desired filters
2. Click **Menu** (three dots) in top right
3. Select **Export**
4. Choose **Excel**
5. File downloads as `Student_Term_Results_Summary.xlsx`

**Excel File Contents:**
- All columns preserved
- Formatting maintained
- Ready for pivot tables or charts

---

## Common Scenarios

### Scenario 1: Finding Top 10 Students

**Goal:** Identify the top-performing students in a class.

**Method:**
1. Run report with filters
2. Click on **Rank** column header
3. Results auto-sort by rank (ascending)
4. Top 10 students are at the top

**Alternative - Using Chart:**
The report automatically shows a bar chart with top 10 students by average.

---

### Scenario 2: Identifying Students Who Need Help

**Goal:** Find students with average below 60%.

**Method:**
1. Run the report
2. Look at the **Average** column
3. Manually identify students < 60
4. Or export to Excel and use filtering

**Advanced - Add Custom Filter:**
Modify `student_term_results_summary.py`:

```python
# In get_data() function, add at the end before return:
if filters.get("min_average"):
    data = [row for row in data if row.average >= filters.get("min_average")]
```

Then add filter in `.js` file:

```javascript
{
  fieldname: 'min_average',
  label: __('Minimum Average'),
  fieldtype: 'Float',
  default: 0
},
```

---

### Scenario 3: Comparing Multiple Classes

**Goal:** Compare performance across different student groups.

**Method:**
1. Run report for **Student Group A**
2. Note the top student's average
3. Run report for **Student Group B**
4. Compare averages

**Automated Comparison (Custom Script):**

```python
import frappe
from education.education.report.student_term_results_summary.student_term_results_summary import execute

groups = ["Grade 10 A", "Grade 10 B", "Grade 10 C"]
academic_year = "2024-25"

for group in groups:
    filters = {
        "student_group": group,
        "academic_year": academic_year
    }
    
    columns, data, msg, chart = execute(filters)
    
    if data:
        averages = [row['average'] for row in data]
        print(f"\n{group}:")
        print(f"  Class Average: {sum(averages)/len(averages):.2f}")
        print(f"  Highest: {max(averages):.2f}")
        print(f"  Lowest: {min(averages):.2f}")
```

---

### Scenario 4: Tracking Individual Student Progress

**Goal:** Track a specific student's performance.

**Method 1 - Via Report:**
1. Run report for the student's group
2. Use browser's Find feature (`Ctrl + F`)
3. Search for student name
4. View their scores

**Method 2 - Direct Query:**

```python
import frappe

student = "STU-001"
student_group = "Grade 10 A"
academic_year = "2024-25"

results = frappe.get_all(
    "Student Term Subject Result",
    filters={
        "student": student,
        "student_group": student_group,
        "academic_year": academic_year,
        "docstatus": 1
    },
    fields=["subject", "exam", "score", "max_score", "semester"]
)

for result in results:
    print(f"{result.semester} - {result.subject} - {result.exam}: {result.score}/{result.max_score}")
```

---

### Scenario 5: Generating Report Cards

**Goal:** Create printable report cards for all students.

**Method:**
1. Run report with filters
2. Click **Menu > Print**
3. Select **Print Format** (or create custom one)
4. Print or save as PDF

**Custom Print Format (HTML):**

Create in: **Customization > Print Format**

```html
<h2 style="text-align: center;">Student Report Card</h2>
<h3>{{ doc.student_name }}</h3>
<p>Student ID: {{ doc.student }}</p>
<p>Class: {{ doc.student_group }}</p>

<table class="table table-bordered">
  <thead>
    <tr>
      <th>Subject</th>
      <th>Score</th>
    </tr>
  </thead>
  <tbody>
    {% for key, value in doc.items() %}
      {% if key.startswith('subject_') and value %}
        <tr>
          <td>{{ key.replace('subject_', '').title() }}</td>
          <td>{{ value }}</td>
        </tr>
      {% endif %}
    {% endfor %}
    <tr>
      <th>Total</th>
      <th>{{ doc.total }}</th>
    </tr>
    <tr>
      <th>Average</th>
      <th>{{ doc.average }}</th>
    </tr>
    <tr>
      <th>Rank</th>
      <th>{{ doc.rank }}</th>
    </tr>
  </tbody>
</table>
```

---

## Advanced Queries

### Example 1: Students with Perfect Scores

**Goal:** Find students who scored 100% in any subject.

**Script:**

```python
import frappe

filters = {
    "student_group": "Grade 10 A",
    "academic_year": "2024-25",
    "docstatus": 1
}

# Get all results
results = frappe.get_all(
    "Student Term Subject Result",
    filters=filters,
    fields=["student", "student_name", "subject", "score", "max_score"]
)

# Group by student and subject
student_subjects = {}
for r in results:
    key = (r.student, r.subject)
    if key not in student_subjects:
        student_subjects[key] = {"total": 0, "max": 0, "name": r.student_name}
    student_subjects[key]["total"] += r.score
    student_subjects[key]["max"] += r.max_score

# Find perfect scores
perfect_scores = []
for (student, subject), data in student_subjects.items():
    if data["total"] == data["max"]:
        perfect_scores.append({
            "student": student,
            "name": data["name"],
            "subject": subject
        })

for ps in perfect_scores:
    print(f"{ps['name']} - {ps['subject']}: Perfect Score!")
```

---

### Example 2: Subject-wise Class Average

**Goal:** Calculate average score for each subject across all students.

**Script:**

```python
import frappe
from education.education.report.student_term_results_summary.student_term_results_summary import (
    execute, get_subjects_for_group
)

filters = {
    "student_group": "Grade 10 A",
    "academic_year": "2024-25"
}

# Get report data
columns, data, msg, chart = execute(filters)

# Get subjects
subjects = get_subjects_for_group(filters)

# Calculate subject averages
subject_averages = {}
for subject in subjects:
    subject_key = "subject_" + frappe.scrub(subject)
    scores = [row[subject_key] for row in data if row.get(subject_key, 0) > 0]
    if scores:
        subject_averages[subject] = sum(scores) / len(scores)

# Display
print("\nSubject-wise Class Averages:")
print("-" * 40)
for subject, avg in sorted(subject_averages.items(), key=lambda x: x[1], reverse=True):
    print(f"{subject:20s}: {avg:.2f}")
```

---

### Example 3: Students Above Class Average

**Goal:** Identify students performing above class average.

**Script:**

```python
import frappe
from education.education.report.student_term_results_summary.student_term_results_summary import execute

filters = {
    "student_group": "Grade 10 A",
    "academic_year": "2024-25"
}

columns, data, msg, chart = execute(filters)

# Calculate class average
averages = [row['average'] for row in data]
class_average = sum(averages) / len(averages)

print(f"\nClass Average: {class_average:.2f}")
print("\nStudents Above Class Average:")
print("-" * 60)

above_average = [row for row in data if row['average'] > class_average]
for row in sorted(above_average, key=lambda x: x['average'], reverse=True):
    print(f"{row['student_name']:20s}: {row['average']:.2f} (Rank: {row['rank']})")
```

---

## Customization Examples

### Example 1: Adding Grade Letter Column

**Goal:** Add A/B/C/D/F grades based on average.

**Modify:** `student_term_results_summary.py`

```python
# Add function after calculate_ranks()
def assign_letter_grades(data):
    """Assign letter grades based on average"""
    for row in data:
        avg = row.average
        if avg >= 90:
            row.letter_grade = "A+"
        elif avg >= 80:
            row.letter_grade = "A"
        elif avg >= 70:
            row.letter_grade = "B"
        elif avg >= 60:
            row.letter_grade = "C"
        elif avg >= 50:
            row.letter_grade = "D"
        else:
            row.letter_grade = "F"
    return data

# In execute() function, after calculate_ranks():
data = calculate_ranks(data)
data = assign_letter_grades(data)  # Add this line

# In get_columns(), add before rank:
{
    "fieldname": "letter_grade",
    "label": _("Grade"),
    "fieldtype": "Data",
    "width": 80
}
```

---

### Example 2: Adding Subject-wise Ranks

**Goal:** Show rank for each individual subject.

This requires significant changes. Create a new report variant or modify extensively.

**Simplified Version - Highest Score Indicator:**

```python
# In get_data(), after calculating all scores:
subjects = get_subjects_for_group(filters)

for subject in subjects:
    subject_key = "subject_" + frappe.scrub(subject)
    scores = [(row[subject_key], i) for i, row in enumerate(data) if row.get(subject_key, 0) > 0]
    if scores:
        max_score = max(scores, key=lambda x: x[0])[0]
        for score, idx in scores:
            if score == max_score:
                data[idx][subject_key + "_indicator"] = "🏆"  # Trophy emoji
```

---

### Example 3: Color-coding Performance

**Goal:** Add visual indicators for performance levels.

ERPNext reports support limited styling. Best approach: Export to Excel and apply conditional formatting.

**Excel Conditional Formatting:**
1. Export report to Excel
2. Select **Average** column
3. Go to **Home > Conditional Formatting**
4. Choose **Color Scales** or **Icon Sets**
5. Set rules:
   - Green: >= 80
   - Yellow: 60-79
   - Red: < 60

---

## API Usage

### Example 1: Getting Report Data via API

**REST API Call:**

```python
import requests
import json

url = "https://your-site.com/api/method/frappe.desk.query_report.run"

headers = {
    "Authorization": "token your_api_key:your_api_secret",
    "Content-Type": "application/json"
}

data = {
    "report_name": "Student Term Results Summary",
    "filters": {
        "student_group": "Grade 10 A",
        "academic_year": "2024-25"
    }
}

response = requests.post(url, headers=headers, data=json.dumps(data))
result = response.json()

columns = result['message']['columns']
data = result['message']['result']

print(f"Found {len(data)} students")
for row in data:
    print(f"{row['student_name']}: {row['average']:.2f}")
```

---

### Example 2: Scheduled Report Email

**Setup via Code:**

```python
import frappe

# Create Auto Email Report
auto_email = frappe.get_doc({
    "doctype": "Auto Email Report",
    "report": "Student Term Results Summary",
    "report_type": "Script Report",
    "user": "administrator@example.com",
    "enabled": 1,
    "format": "HTML",
    "frequency": "Weekly",
    "day_of_week": "Monday",
    "filters": frappe.as_json({
        "student_group": "Grade 10 A",
        "academic_year": "2024-25"
    }),
    "email_to": "principal@school.com\nteacher@school.com",
    "send_if_data": 1
})

auto_email.insert()
frappe.db.commit()

print(f"Scheduled report created: {auto_email.name}")
```

---

### Example 3: Embedding Report in Custom Page

**HTML/JavaScript:**

```html
<!-- In a custom web page or dashboard -->
<div id="report-container"></div>

<script>
frappe.call({
    method: 'frappe.desk.query_report.run',
    args: {
        report_name: 'Student Term Results Summary',
        filters: {
            student_group: 'Grade 10 A',
            academic_year: '2024-25'
        }
    },
    callback: function(r) {
        if (r.message) {
            let data = r.message.result;
            let html = '<table class="table table-bordered">';
            html += '<thead><tr><th>Student</th><th>Average</th><th>Rank</th></tr></thead>';
            html += '<tbody>';
            
            data.forEach(row => {
                html += `<tr>
                    <td>${row.student_name}</td>
                    <td>${row.average.toFixed(2)}</td>
                    <td>${row.rank}</td>
                </tr>`;
            });
            
            html += '</tbody></table>';
            document.getElementById('report-container').innerHTML = html;
        }
    }
});
</script>
```

---

## Troubleshooting Examples

### Example 1: Debug Missing Data

**Problem:** Student appears in group but not in report.

**Debug Script:**

```python
import frappe

student = "STU-001"
student_group = "Grade 10 A"
academic_year = "2024-25"

# Check if student is in group
in_group = frappe.db.exists("Student Group Student", {
    "parent": student_group,
    "student": student
})
print(f"Student in group: {in_group}")

# Check submitted results
results = frappe.get_all(
    "Student Term Subject Result",
    filters={
        "student": student,
        "student_group": student_group,
        "academic_year": academic_year,
        "docstatus": 1  # Only submitted
    },
    fields=["name", "subject", "score", "docstatus"]
)

print(f"\nFound {len(results)} submitted results:")
for r in results:
    print(f"  {r.name}: {r.subject} - {r.score} points")

if len(results) == 0:
    # Check draft results
    draft = frappe.get_all(
        "Student Term Subject Result",
        filters={
            "student": student,
            "student_group": student_group,
            "academic_year": academic_year,
            "docstatus": 0  # Draft
        },
        fields=["name"]
    )
    print(f"\nFound {len(draft)} DRAFT results (need to be submitted)")
```

---

### Example 2: Performance Profiling

**Problem:** Report is slow with large datasets.

**Profile Script:**

```python
import time
import frappe

filters = {
    "student_group": "Grade 10 A",
    "academic_year": "2024-25"
}

# Test original version
print("Testing original version...")
start = time.time()
from education.education.report.student_term_results_summary.student_term_results_summary import execute
columns, data, msg, chart = execute(filters)
end = time.time()
print(f"Time taken: {end - start:.2f} seconds")
print(f"Records: {len(data)}")

# Test SQL-optimized version
print("\nTesting SQL-optimized version...")
start = time.time()
from education.education.report.student_term_results_summary.student_term_results_summary_sql_optimized import execute as execute_sql
columns, data, msg, chart = execute_sql(filters)
end = time.time()
print(f"Time taken: {end - start:.2f} seconds")
print(f"Records: {len(data)}")
```

---

### Example 3: Data Validation

**Problem:** Verify data integrity before generating report.

**Validation Script:**

```python
import frappe

def validate_report_data(student_group, academic_year):
    """Validate data before running report"""
    
    issues = []
    
    # Check 1: Student group exists
    if not frappe.db.exists("Student Group", student_group):
        issues.append(f"Student Group '{student_group}' not found")
        return issues
    
    # Check 2: Students in group
    students = frappe.get_all("Student Group Student", 
        filters={"parent": student_group},
        pluck="student")
    
    if not students:
        issues.append(f"No students in '{student_group}'")
        return issues
    
    print(f"✓ Found {len(students)} students in group")
    
    # Check 3: Results exist
    results = frappe.get_all("Student Term Subject Result",
        filters={
            "student_group": student_group,
            "academic_year": academic_year,
            "docstatus": 1
        })
    
    if not results:
        issues.append("No submitted results found")
    else:
        print(f"✓ Found {len(results)} submitted results")
    
    # Check 4: All students have results
    students_with_results = frappe.get_all("Student Term Subject Result",
        filters={
            "student_group": student_group,
            "academic_year": academic_year,
            "docstatus": 1
        },
        pluck="student",
        distinct=True)
    
    missing = set(students) - set(students_with_results)
    if missing:
        issues.append(f"{len(missing)} students have no results: {', '.join(list(missing)[:5])}")
    else:
        print(f"✓ All students have results")
    
    return issues

# Run validation
issues = validate_report_data("Grade 10 A", "2024-25")
if issues:
    print("\n⚠ Issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n✓ All validations passed!")
```

---

## Best Practices

1. **Always submit results** before running the report (docstatus = 1)
2. **Use specific semester filters** for better performance
3. **Export to Excel** for advanced analysis and formatting
4. **Schedule regular reports** instead of running manually
5. **Validate data** before generating reports for stakeholders
6. **Use SQL-optimized version** for classes with 100+ students
7. **Clear cache** after modifying report code
8. **Test with sample data** before using in production

---

## Additional Resources

- Main Documentation: [README.md](./README.md)
- Installation Guide: [../../STUDENT_REPORT_INSTALLATION_GUIDE.md](../../STUDENT_REPORT_INSTALLATION_GUIDE.md)
- Setup Script: [setup_student_report.py](../../setup_student_report.py)
- SQL Optimized Version: [student_term_results_summary_sql_optimized.py](./student_term_results_summary_sql_optimized.py)

---

**For questions or issues, contact your system administrator.**
