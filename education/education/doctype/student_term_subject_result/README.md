# Student Result Calculation System

This system provides automated calculation of student term and year results with ranking functionality.

## Overview

The system consists of the following components:

1. **Student Term Subject Result** - Individual assessment results
2. **Student Term Report** - Aggregated term results with ranking
3. **Student Year Report** - Aggregated year results with ranking
4. **Result Calculation Tool** - Manual trigger for calculations

## Workflow

### 1. Recording Individual Results

Use the **Student Term Subject Result** doctype to record individual assessment scores:

- Student, Academic Year, Academic Term
- Subject, Student Group, Grade/Program
- Assessment Criteria (e.g., "Midterm Exam", "Final Exam")
- Score and Maximum Score
- The system automatically calculates percentage

### 2. Term Result Calculation

When an academic term is completed, use the **Result Calculation Tool** to:

1. Calculate total scores for each subject per student
2. Calculate term average across all subjects
3. Rank students within their student group
4. Generate **Student Term Report** documents

### 3. Year Result Calculation

When an academic year is completed, use the **Result Calculation Tool** to:

1. Average all term results for each student
2. Rank students within their student group for the year
3. Generate **Student Year Report** documents

## Ranking Logic

- Students are ranked by their average scores (highest to lowest)
- If two students have the same average, they get the same rank
- The next rank is skipped (e.g., if two students tie for rank 2, the next student gets rank 4)

## API Endpoints

For mobile app integration:

### Submit Results
```
POST /api/method/education.education.education.api.create_and_submit_term_subject_result
```

### Get Student Results
```
GET /api/method/education.education.education.api.get_student_term_results
GET /api/method/education.education.education.api.get_student_term_report
GET /api/method/education.education.education.api.get_student_year_report
```

### Trigger Calculations
```
POST /api/method/education.education.education.api.trigger_term_calculation
POST /api/method/education.education.education.api.trigger_year_calculation
```

## Usage Instructions

### For Teachers/Administrators

1. **Record Assessment Results**: Create Student Term Subject Result documents for each student's assessment
2. **Complete Term**: When all assessments for a term are recorded, use the Result Calculation Tool to calculate term results
3. **Complete Year**: When all terms are completed, use the Result Calculation Tool to calculate year results

### For Mobile App

1. Use the existing `create_and_submit_term_subject_result` API endpoint
2. The mobile app can fetch calculated results using the provided API endpoints
3. Calculations can be triggered via API if needed

## Data Integrity

- All result documents are submittable to ensure data integrity
- Duplicate prevention: Cannot create multiple results for same student/subject/assessment/term
- Score validation: Score cannot exceed maximum score or be negative
- Automatic percentage calculation

## Performance Considerations

- Calculations are designed to handle large datasets efficiently
- Use background jobs for very large student populations
- Results are cached in term/year report documents for fast retrieval

## Troubleshooting

- Check Error Log for calculation failures
- Ensure all Student Term Subject Results are submitted before running calculations
- Verify Academic Year and Term setup is correct
- Check Student Group assignments are complete 