# Student Report Card System - Setup Guide

## Overview

The Student Report Card system is a comprehensive solution for generating professional report cards based on student academic performance data. It integrates with the existing Education module and provides features like QR code verification, PDF generation, bulk processing, and public web viewing.

## Features

- **Automated Data Population**: Fetches data from Student Term Reports and Student Year Reports
- **Professional Design**: Responsive HTML template with modern styling
- **QR Code Integration**: Generates QR codes for report verification
- **Public Web Access**: Secure public URLs for report viewing
- **PDF Generation**: Downloadable PDF reports
- **Bulk Generation**: Process multiple students at once
- **Mobile API**: RESTful endpoints for mobile app integration
- **Security**: Published/unpublished states with access controls

## Installation

### 1. Install Dependencies

The system requires the following Python packages:

```bash
# Install qrcode library
pip install qrcode[pil]
```

### 2. Create DocType

The Student Report Card DocType should be automatically created when you install the app. If not, you can manually create it using the Frappe Desk.

### 3. Set Permissions

Configure the following role permissions:

- **System Manager**: Full access (create, read, write, delete, submit)
- **Academics User**: Full access (create, read, write, delete, submit)
- **Student**: Read-only access to their own reports
- **Guest**: Read access to published reports only

### 4. Configure School Logo

1. Upload your school logo to `/files/school_logo.png`
2. The system will automatically use this logo in report cards
3. Recommended size: 200x200 pixels, PNG format

## Usage

### Creating Individual Report Cards

1. Navigate to **Education > Student Report Card > New**
2. Select the student, academic year, and student group
3. Choose report type (Term Report, Year Report, or Full Report)
4. Save the document - data will be auto-populated
5. Submit the document to make it available publicly

### Bulk Generation

1. Go to **Student Report Card** list
2. Click **Bulk Generate Report Cards** button
3. Select Academic Year and Student Group
4. Choose whether to regenerate existing reports
5. Click **Generate** - the system will process all students

### Viewing Report Cards

#### Public Web Access
- Reports are accessible at: `https://app.makkobillischool.com/report-card/{REPORT_ID}`
- QR codes automatically redirect to this URL
- Responsive design works on all devices

#### PDF Download
- Click "Download PDF" button on the web page
- Or generate PDF from the DocType form
- PDFs are stored in Frappe Files

## API Endpoints

The system provides RESTful API endpoints for mobile app integration:

### Public Endpoints (No Authentication Required)

```
GET /api/method/education.education.api.report_card.get_report_card_by_id
Parameters: report_id

GET /api/method/education.education.api.report_card.get_school_info
```

### Authenticated Endpoints

```
GET /api/method/education.education.api.report_card.get_student_report_cards
Parameters: student, academic_year, limit

POST /api/method/education.education.api.report_card.generate_report_card_pdf
Parameters: report_id

GET /api/method/education.education.api.report_card.get_student_list
Parameters: student_group, academic_year

GET /api/method/education.education.api.report_card.get_academic_years

GET /api/method/education.education.api.report_card.get_student_groups
Parameters: academic_year

POST /api/method/education.education.api.report_card.bulk_generate_report_cards_api
Parameters: academic_year, student_group, regenerate
```

## Data Requirements

For the system to work properly, ensure you have:

1. **Students** with basic information (name, gender, date of birth)
2. **Academic Years** properly configured
3. **Student Groups** with students enrolled
4. **Academic Terms** for the academic year
5. **Courses** set up for subjects
6. **Student Term Reports** submitted for students
7. **Student Year Reports** submitted for students

## Customization

### Modifying Report Design

Edit the HTML template in the `generate_html_content()` method in `student_report_card.py`:

```python
def generate_html_content(self):
    # Modify the HTML template here
    html_content = f"""
    <!-- Your custom HTML here -->
    """
```

### Adding Custom Fields

1. Go to **Customize Form** for Student Report Card
2. Add your custom fields
3. Update the `populate_student_details()` method to populate new fields

### Changing QR Code Domain

Update the base URL in the `generate_qr_code()` method:

```python
def generate_qr_code(self):
    base_url = "https://your-domain.com"  # Change this
    self.qr_code_url = f"{base_url}/report-card/{self.report_id}"
```

## Troubleshooting

### Common Issues

1. **QR Code Not Generating**
   - Ensure `qrcode` library is installed
   - Check error logs in Frappe

2. **No Data in Report Card**
   - Verify Student Term Reports and Year Reports exist
   - Check if reports are submitted (docstatus = 1)

3. **Public URL Not Working**
   - Ensure report is submitted and published
   - Check web page permissions

4. **PDF Generation Fails**
   - Check if wkhtmltopdf is installed
   - Verify file permissions

### Error Logs

Check Frappe error logs for detailed error information:
- Go to **System > Error Log**
- Filter by "Student Report Card"

## Security Considerations

1. **Public Access**: Only published and submitted reports are accessible publicly
2. **Report IDs**: Random 5-character IDs prevent guessing
3. **Guest Access**: Limited to read-only for published reports
4. **API Security**: Authenticated endpoints require valid session/token

## Performance Optimization

1. **Bulk Generation**: Process in batches for large student groups
2. **Caching**: HTML content is cached in the document
3. **PDF Storage**: PDFs are generated once and stored
4. **Database Indexing**: Report ID field is indexed for fast lookups

## Backup and Migration

1. **Data Backup**: Include Student Report Card in regular backups
2. **File Backup**: Backup PDF files and school logo
3. **Migration**: Export/import report cards between sites

## Support

For technical support or customization requests:
1. Check the error logs first
2. Verify data requirements are met
3. Test with a single report card before bulk generation
4. Contact system administrator for advanced customizations

## Version History

- **v1.0**: Initial release with basic report card generation
- **v1.1**: Added QR code functionality and public web access
- **v1.2**: Added bulk generation and API endpoints
- **v1.3**: Added PDF generation and mobile responsiveness 