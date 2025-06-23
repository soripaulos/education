# Simple Student Report Card Setup Guide

This is a simplified version of the Student Report Card system designed to work without any external dependencies on Frappe Cloud.

## What's Included

### 1. Student Report Card DocType
- **Location**: `education/education/doctype/student_report_card/`
- **Purpose**: Stores individual student report cards with basic academic performance data
- **Features**:
  - Automatic report ID generation
  - Student details integration
  - Term and year performance tracking
  - HTML report generation
  - Public/private publishing
  - Professional report design

### 2. Course Year Summary Child Table
- **Location**: `education/education/doctype/course_year_summary/`
- **Purpose**: Child table for storing year-level course performance data
- **Fields**: Course, Total Year Score, Max Score, Average Percentage, Terms Count

### 3. API Endpoints
- **Location**: `education/education/api/report_card.py`
- **Purpose**: RESTful API for mobile app integration
- **Endpoints**:
  - `get_student_report_cards()` - List report cards
  - `get_report_card_by_id()` - Get specific report card
  - `generate_report_card_pdf()` - Generate PDF version
  - `get_student_list()` - Get students for selection
  - `get_academic_years()` - Get academic years
  - `get_student_groups()` - Get student groups
  - `bulk_generate_report_cards_api()` - Bulk generation

### 4. Public Report Viewer
- **Location**: `education/education/www/report-card/`
- **Purpose**: Public web page for viewing published report cards
- **URL**: `https://yoursite.com/report-card/{report_id}`

## Installation Steps

### 1. Migrate the DocTypes
```bash
# Run this in your Frappe Cloud console or locally
bench migrate
```

### 2. Set Permissions
Go to **Setup > Permissions** and configure:

**Student Report Card:**
- **System Manager**: Full access
- **Academics User**: Create, Read, Write, Submit, Delete
- **Student**: Read only (for their own reports)

### 3. Test the System
1. Go to **Education > Student Report Card**
2. Create a new report card
3. Select a student, academic year, and student group
4. Save - the system will auto-populate data
5. Submit to publish

## Key Features

### Automatic Data Population
- Student details from Student master
- Academic performance from Student Term Report and Student Year Report
- Automatic calculation of averages and ranks

### Professional Report Design
- Modern, responsive HTML design
- School branding integration
- Print-friendly layout
- Mobile-responsive design

### Security & Verification
- Unique report IDs
- Published/private states
- Verification URLs
- Role-based access control

### Mobile API Integration
- RESTful API endpoints
- JSON responses
- Token authentication support
- Bulk operations

## Usage

### Creating Individual Report Cards
1. Navigate to **Education > Student Report Card**
2. Click **New**
3. Select **Student**, **Academic Year**, and **Student Group**
4. Save - data will auto-populate
5. Review the generated HTML content
6. Submit to publish

### Bulk Generation
Use the API endpoint or create a custom script:
```python
# Example bulk generation
from education.education.doctype.student_report_card.student_report_card import bulk_generate_report_cards

result = bulk_generate_report_cards(
    academic_year="2024-25",
    student_group="Grade 10-A",
    regenerate=False
)
```

### Public Viewing
Published report cards can be viewed at:
```
https://yoursite.com/report-card/{report_id}
```

## Mobile App Integration

### API Authentication
```javascript
// Example API call
const response = await fetch('/api/method/education.education.api.report_card.get_report_card_by_id', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'token your_api_key:your_api_secret'
    },
    body: JSON.stringify({
        report_id: 'ABC123'
    })
});
```

### Response Format
```json
{
    "status": "success",
    "data": {
        "report_id": "ABC123",
        "student_name": "John Doe",
        "term_1_average": 85.5,
        "term_2_average": 88.2,
        "year_average": 86.8,
        "html_content": "...",
        // ... other fields
    }
}
```

## Customization

### Branding
- Update company information in **Setup > Company**
- Add school logo to `/files/school_logo.png`
- Modify HTML template in the `generate_html_content()` method

### Styling
- Edit CSS in the `generate_html_content()` method
- Customize colors, fonts, and layout
- Add custom sections or fields

### Additional Fields
- Add custom fields to the DocType
- Update the `populate_student_details()` method
- Modify the HTML template to display new fields

## Troubleshooting

### Common Issues
1. **No data showing**: Ensure Student Term Report and Student Year Report exist and are submitted
2. **Permission errors**: Check role permissions for Student Report Card
3. **API errors**: Verify API key/secret authentication
4. **HTML not generating**: Check for errors in the validation method

### Debug Mode
Enable developer mode to see detailed error messages:
```python
# In site_config.json
{
    "developer_mode": 1,
    "log_level": "DEBUG"
}
```

## Next Steps

Once this basic system is working, you can:
1. Add child tables back for detailed subject performance
2. Implement QR code generation (when dependencies are available)
3. Add PDF generation features
4. Create custom print formats
5. Add email notifications
6. Implement batch processing tools

## Support

This simplified system is designed to work reliably on Frappe Cloud without external dependencies. It provides the core functionality needed for student report card generation and management.

For issues or enhancements, check the Frappe documentation or community forums. 