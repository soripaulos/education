# Push Notification System Setup Guide

## Overview

This guide will help you set up a comprehensive push notification system for your MBS Education App. The system is built entirely within Frappe and provides:

- **Token Management**: Automatic registration and management of device push tokens
- **Flexible Targeting**: Send to all students, specific students, student groups, or custom selections
- **Rich Notifications**: Support for categories, priorities, images, and custom data
- **Delivery Tracking**: Complete logging and statistics for all notifications
- **Web Interface**: Easy-to-use web interface for managing notifications
- **API Integration**: RESTful APIs for mobile app integration

## System Components

### 1. DocTypes Created
- **Push Token**: Manages device push tokens
- **Push Notification**: Main notification management
- **Push Notification Student**: Child table for specific student targeting
- **Push Notification Student Group**: Child table for student group targeting
- **Push Notification User**: Child table for specific user targeting
- **Push Notification Log**: Delivery tracking and logging

### 2. API Endpoints
- **Token Registration**: `/api/method/education.education.api.push_notifications.register_push_token`
- **Send to Students**: `/api/method/education.education.api.push_notifications.send_notification_to_students`
- **Send to All**: `/api/method/education.education.api.push_notifications.send_notification_to_all_students`
- **Send to Groups**: `/api/method/education.education.api.push_notifications.send_notification_to_student_groups`
- **Test Notification**: `/api/method/education.education.api.push_notifications.test_notification`

### 3. Web Interface
- **Management Interface**: `/push-notifications` - Complete web interface for managing notifications

## Installation Steps

### Step 1: Install DocTypes

1. **Navigate to your Frappe site**:
   ```bash
   cd /path/to/your/frappe/site
   bench --site your-site.com install-app education
   ```

2. **Install the new DocTypes**:
   ```bash
   bench --site your-site.com migrate
   ```

3. **If migration doesn't work, manually install**:
   ```bash
   bench --site your-site.com console
   ```
   
   Then in the console:
   ```python
   # Install Push Token DocType
   frappe.reload_doctype("Push Token")
   
   # Install Push Notification DocType
   frappe.reload_doctype("Push Notification")
   
   # Install child tables
   frappe.reload_doctype("Push Notification Student")
   frappe.reload_doctype("Push Notification Student Group")
   frappe.reload_doctype("Push Notification User")
   frappe.reload_doctype("Push Notification Log")
   
   frappe.db.commit()
   ```

### Step 2: Set Permissions

1. **Go to Role Permission Manager** in your Frappe desk
2. **Set permissions for Push Token**:
   - System Manager: All permissions
   - Education Manager: All permissions
   - Student: Read and Write (own records only)

3. **Set permissions for Push Notification**:
   - System Manager: All permissions
   - Education Manager: All permissions
   - Instructor: Create, Read, Write

### Step 3: Configure Mobile App Integration

Update your mobile app to register push tokens when users log in:

```javascript
// In your mobile app's authentication flow
import { registerPushToken } from './pushNotificationService';

// After successful login
const registerToken = async () => {
  try {
    const token = await Notifications.getExpoPushTokenAsync();
    const deviceInfo = await Device.getDeviceTypeAsync();
    
    const response = await frappe.call({
      method: 'education.education.api.push_notifications.register_push_token',
      args: {
        push_token: token.data,
        device_type: Platform.OS, // 'android' or 'ios'
        app_version: Constants.manifest.version,
        device_model: Device.modelName,
        student: userStudent // if user is linked to a student
      }
    });
    
    console.log('Push token registered:', response);
  } catch (error) {
    console.error('Failed to register push token:', error);
  }
};
```

### Step 4: Test the System

1. **Test Token Registration**:
   - Login to your mobile app
   - Check if push tokens are being created in the Push Token doctype

2. **Test Notification Sending**:
   - Go to `/push-notifications` in your browser
   - Send a test notification to yourself
   - Check if you receive the notification on your mobile device

3. **Test Web Interface**:
   - Create a new notification from the web interface
   - Send to different target types (all students, specific students, groups)
   - Check delivery statistics

## Usage Guide

### Sending Notifications via Web Interface

1. **Access the Interface**:
   - Go to `https://your-site.com/push-notifications`
   - Login with appropriate permissions

2. **Send a Notification**:
   - Fill in the title and message
   - Select category and priority
   - Choose target audience
   - Optionally include parents/teachers
   - Click "Send Notification"

3. **Monitor Delivery**:
   - Check the statistics cards for delivery counts
   - View recent notifications for status updates
   - Check delivery logs for detailed information

### Sending Notifications via API

#### Send to All Students
```python
import frappe

frappe.call(
    method='education.education.api.push_notifications.send_notification_to_all_students',
    args={
        'title': 'Important Announcement',
        'message': 'School will be closed tomorrow due to weather conditions.',
        'category': 'announcements',
        'priority': 'high',
        'include_parents': True
    }
)
```

#### Send to Specific Students
```python
frappe.call(
    method='education.education.api.push_notifications.send_notification_to_students',
    args={
        'title': 'Assignment Reminder',
        'message': 'Your math assignment is due tomorrow.',
        'students': ['STU-001', 'STU-002', 'STU-003'],
        'category': 'academic',
        'priority': 'normal'
    }
)
```

#### Send to Student Groups
```python
frappe.call(
    method='education.education.api.push_notifications.send_notification_to_student_groups',
    args={
        'title': 'Class Cancelled',
        'message': 'Today\'s physics class is cancelled.',
        'student_groups': ['Grade-10-A', 'Grade-10-B'],
        'category': 'academic',
        'priority': 'high',
        'include_parents': True
    }
)
```

### Categories and Priorities

#### Categories
- **academic**: Academic-related notifications
- **announcements**: General announcements
- **urgent**: Urgent notifications
- **fees**: Fee-related notifications
- **attendance**: Attendance-related notifications
- **general**: General notifications
- **event**: Event notifications
- **exam**: Exam-related notifications

#### Priorities
- **low**: Low priority (no special handling)
- **normal**: Normal priority (default)
- **high**: High priority (emphasized in UI)
- **urgent**: Urgent priority (immediate delivery)

## Advanced Features

### Custom Data and Actions

You can include custom data and action URLs in notifications:

```python
frappe.call(
    method='education.education.api.push_notifications.send_notification_to_students',
    args={
        'title': 'New Grade Available',
        'message': 'Your math test grade is now available.',
        'students': ['STU-001'],
        'category': 'academic',
        'action_url': '/grades/view/GRADE-001',
        'data': {
            'grade_id': 'GRADE-001',
            'subject': 'Mathematics',
            'score': 85
        }
    }
)
```

### Scheduled Notifications

You can schedule notifications for future delivery:

```python
# Create a notification document with scheduled_time
doc = frappe.get_doc({
    "doctype": "Push Notification",
    "title": "Exam Reminder",
    "message": "Your exam is tomorrow at 9 AM",
    "category": "exam",
    "priority": "high",
    "target_type": "all_students",
    "scheduled_time": "2024-01-20 08:00:00"
})
doc.insert()
doc.submit()  # This will schedule the notification
```

### Delivery Tracking

Monitor notification delivery through:

1. **Statistics Dashboard**: Real-time delivery statistics
2. **Push Notification Log**: Detailed per-device delivery logs
3. **Notification History**: Complete history of sent notifications

## Troubleshooting

### Common Issues

1. **Notifications Not Received**:
   - Check if push tokens are registered correctly
   - Verify device permissions for notifications
   - Check if the app is in background/foreground

2. **API Errors**:
   - Ensure proper authentication
   - Check if required parameters are provided
   - Verify user permissions

3. **Web Interface Not Loading**:
   - Check if the www folder is accessible
   - Verify user has appropriate permissions
   - Check browser console for JavaScript errors

### Debug Mode

Enable debug logging by adding this to your site config:

```json
{
  "developer_mode": 1,
  "log_level": "DEBUG"
}
```

### Support

For issues and support:
1. Check the Error Log in Frappe desk
2. Review the Push Notification Log doctype for delivery issues
3. Check browser console for web interface issues

## Security Considerations

1. **Token Security**: Push tokens are stored securely and linked to user accounts
2. **Permission Control**: Only authorized users can send notifications
3. **Data Privacy**: Personal data is handled according to privacy policies
4. **Rate Limiting**: Consider implementing rate limiting for API endpoints

## Performance Optimization

1. **Batch Processing**: Notifications are sent in batches of 100
2. **Background Processing**: Large notification sends are queued
3. **Token Cleanup**: Inactive tokens are automatically deactivated
4. **Caching**: Statistics are cached for better performance

## Conclusion

Your push notification system is now ready! The system provides:

- ✅ Complete token management
- ✅ Flexible targeting options
- ✅ Rich notification features
- ✅ Delivery tracking and statistics
- ✅ Easy-to-use web interface
- ✅ RESTful API integration
- ✅ Mobile app compatibility

You can now send targeted push notifications to your students, parents, and teachers through both the web interface and API endpoints. 