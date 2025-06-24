# Simple Push Notification Setup ✅

## Overview

This is a **very simple** push notification system using just DocTypes directly. No web interface, no complex tracking, no delivery logs - just the basics that work!

## What You Get

- ✅ **Basic DocType Interface** - Use standard Frappe forms to send notifications
- ✅ **Title, Message, Category** - Essential notification fields
- ✅ **Target Selection** - All students, specific students, or student groups  
- ✅ **Simple Sending** - Submit the DocType document to send
- ✅ **Basic Status** - Draft/Sent/Failed status only
- ✅ **Auto Token Registration** - Mobile app handles token registration automatically

## Files Created (All in correct path)

### DocTypes in `education/education/education/doctype/`:

1. **push_token/** - Stores device push tokens
   - `push_token.json` - DocType definition
   - `push_token.py` - Controller (existing)
   - `__init__.py`

2. **push_notification/** - Main notification DocType
   - `push_notification.json` - DocType definition  
   - `push_notification.py` - Controller with send logic
   - `__init__.py`

3. **push_notification_student/** - Child table for student selection
   - `push_notification_student.json` - Child table definition
   - `__init__.py`

4. **push_notification_student_group/** - Child table for student group selection
   - `push_notification_student_group.json` - Child table definition
   - `__init__.py`

### Mobile App Integration

- **Updated `pushNotificationService.js`** - Simplified service that just registers tokens

## How to Use

### Step 1: Install DocTypes

1. Make sure all files are in the correct path: `education/education/education/doctype/`
2. Run migration on your Frappe site:
   ```bash
   bench --site your-site.com migrate
   ```

### Step 2: Mobile App Auto-Registration

The mobile app automatically registers push tokens when users log in. No manual setup needed.

### Step 3: Send Notifications (Super Simple!)

1. **Go to Push Notification** in your Frappe desk
2. **Click "New"**
3. **Fill in the form**:
   - **Title**: Your notification title (required)
   - **Message**: Your notification message (required)
   - **Category**: Choose from dropdown (academic, announcements, urgent, fees, attendance, general, event, exam)
   - **Target Type**: Choose who to send to:
     - `all_students` - Send to everyone
     - `specific_students` - Select individual students
     - `student_groups` - Select student groups
   - **Target Students/Groups**: Select if you chose specific targeting
4. **Click "Submit"** - This automatically sends the notification!

### Step 4: Check Status

- **Draft** - Not sent yet
- **Sent** - Successfully sent (with timestamp)
- **Failed** - Failed to send (check Error Log)

## Simple API Usage (Optional)

If you want to send programmatically from code:

```python
# Create and send notification
doc = frappe.get_doc({
    "doctype": "Push Notification",
    "title": "Test Notification",
    "message": "This is a test message",
    "category": "general",
    "target_type": "all_students"
})
doc.insert()
doc.submit()  # This automatically sends the notification
```

## Available Categories

- `academic` - Academic announcements
- `announcements` - General announcements  
- `urgent` - Urgent notifications
- `fees` - Fee-related notifications
- `attendance` - Attendance notifications
- `general` - General notifications (default)
- `event` - Event notifications
- `exam` - Exam notifications

## Target Types

- `all_students` - Send to all students with registered tokens
- `specific_students` - Send to selected students only
- `student_groups` - Send to students in selected groups

## That's It! 🎉

No complex setup, no web interfaces, no delivery tracking databases. Just:

1. Create a Push Notification document
2. Fill in title, message, category, and target
3. Submit the document
4. Notification is sent automatically!

The system uses your existing Student and Student Group records for targeting, and the mobile app handles all the token registration automatically.

**Perfect for simple, reliable push notifications without the complexity!** 