import frappe
from frappe.utils import strip_html_tags

def course_enrollment_handler(doc, method=None):
    """Handle notification events for Course Enrollment"""
    if method == "after_insert":
        try:
            send_enrollment_notification(doc)
        except Exception as e:
            log_notification_error("course_enrollment_handler", e, doc)
    
    elif method == "on_update":
        # Other update-specific handling if needed
        pass

def assignment_handler(doc, method=None):
    """Handle notification events for Assignment"""
    if method == "on_update" and doc.has_value_changed("status"):
        try:
            send_assignment_notification(doc)
        except Exception as e:
            log_notification_error("assignment_handler", e, doc)
    
    elif method == "on_submit":
        try:
            send_assignment_notification(doc, "submitted")
        except Exception as e:
            log_notification_error("assignment_handler", e, doc)

def fee_handler(doc, method=None):
    """Handle notification events for Fee documents"""
    if method == "after_insert":
        try:
            send_fee_notification(doc, "created")
        except Exception as e:
            log_notification_error("fee_handler", e, doc)
    
    elif method == "on_update":
        if doc.has_value_changed("paid") and doc.paid:
            try:
                send_fee_notification(doc, "paid")
            except Exception as e:
                log_notification_error("fee_handler", e, doc)
        elif doc.has_value_changed("due_date"):
            try:
                send_fee_notification(doc, "due_date_changed")
            except Exception as e:
                log_notification_error("fee_handler", e, doc)

def exam_handler(doc, method=None):
    """Handle notification events for Examination"""
    if method == "after_insert" or (method == "on_update" and (
            doc.has_value_changed("schedule_date") or 
            doc.has_value_changed("exam_date") or 
            doc.has_value_changed("from_time"))):
        try:
            send_exam_notification(doc)
        except Exception as e:
            log_notification_error("exam_handler", e, doc)

def attendance_handler(doc, method=None):
    """Handle notification events for Student Attendance"""
    if method == "on_update" and doc.has_value_changed("status") and doc.status == "Absent":
        try:
            send_attendance_notification(doc)
        except Exception as e:
            log_notification_error("attendance_handler", e, doc)

# Utility functions for sending notifications
def send_enrollment_notification(doc):
    """Send notification for course enrollment"""
    student_user = frappe.db.get_value("Student", doc.student, "student_email_id")
    if not student_user:
        return
    
    from_user = frappe.session.user
    if from_user == student_user:
        return
    
    # Get course/program name
    program_name = ""
    course_name = ""
    
    if hasattr(doc, 'program') and doc.program:
        program_name = frappe.db.get_value("Program", doc.program, "program_name")
    
    if hasattr(doc, 'course') and doc.course:
        course_name = frappe.db.get_value("Course", doc.course, "course_name")
    
    # Create message
    message = ""
    if program_name and course_name:
        message = f"You have been enrolled in <b>{course_name}</b> under program <b>{program_name}</b>"
    elif program_name:
        message = f"You have been enrolled in program <b>{program_name}</b>"
    elif course_name:
        message = f"You have been enrolled in course <b>{course_name}</b>"
    else:
        message = f"You have been enrolled in a new course/program"

    # Check notification preferences
    if should_send_notification(doc.student, "course_updates"):
        create_notification(from_user, student_user, message, doc.doctype, doc.name)

def send_assignment_notification(doc, status_override=None):
    """Send notification for assignment updates"""
    student_user = frappe.db.get_value("Student", doc.student, "student_email_id")
    if not student_user:
        return
    
    from_user = frappe.session.user
    if from_user == student_user:
        return
    
    status = status_override or doc.status
    
    # Create message based on status
    message = ""
    if status == "Submitted" or status_override == "submitted":
        message = f"Your assignment <b>{doc.name}</b> has been received and is under review"
    elif status == "Completed" or status == "Graded":
        message = f"Your assignment <b>{doc.name}</b> has been graded. Please check your results."
    elif status == "Returned":
        message = f"Your assignment <b>{doc.name}</b> has been returned for revision"
    else:
        return  # Don't send for other statuses
    
    # Check notification preferences
    if should_send_notification(doc.student, "assignment_notifications"):
        create_notification(from_user, student_user, message, doc.doctype, doc.name)

def send_fee_notification(doc, event_type):
    """Send notification for fee updates"""
    student_user = frappe.db.get_value("Student", doc.student, "student_email_id")
    if not student_user:
        return
    
    from_user = frappe.session.user
    if from_user == student_user:
        return
    
    # Create message based on fee status
    message = ""
    amount = getattr(doc, 'grand_total', getattr(doc, 'amount', 0))
    
    if event_type == "created":
        message = f"A new fee of <b>{amount}</b> has been added to your account"
    elif event_type == "paid":
        message = f"Fee payment of <b>{amount}</b> has been received"
    elif event_type == "due_date_changed" and hasattr(doc, 'due_date') and doc.due_date:
        due_date = frappe.utils.format_date(doc.due_date)
        message = f"Fee payment of <b>{amount}</b> is due on <b>{due_date}</b>"
    else:
        return
    
    # Check notification preferences
    if should_send_notification(doc.student, "fee_reminders"):
        create_notification(from_user, student_user, message, doc.doctype, doc.name)

def send_exam_notification(doc):
    """Send notification about exam schedules"""
    if not hasattr(doc, 'course') or not doc.course:
        return
    
    from_user = frappe.session.user
    
    # Get all students enrolled in the course
    students = frappe.get_all(
        "Course Enrollment", 
        filters={"course": doc.course, "active": 1}, 
        fields=["student"]
    )
    
    if not students:
        return
    
    # Get course name for the message
    course_name = frappe.db.get_value("Course", doc.course, "course_name")
    
    # Prepare date information
    exam_date = ""
    if hasattr(doc, 'schedule_date') and doc.schedule_date:
        exam_date = frappe.utils.format_date(doc.schedule_date)
    elif hasattr(doc, 'exam_date') and doc.exam_date:
        exam_date = frappe.utils.format_date(doc.exam_date)
    
    time_info = ""
    if hasattr(doc, 'from_time') and doc.from_time:
        from_time = frappe.utils.format_time(doc.from_time)
        time_info = f" at <b>{from_time}</b>"
    
    # Create message
    if exam_date:
        message = f"Examination for <b>{course_name}</b> is scheduled on <b>{exam_date}</b>{time_info}"
    else:
        message = f"Examination for <b>{course_name}</b> has been scheduled"
    
    # Send notifications to all students
    for student_data in students:
        student_user = frappe.db.get_value("Student", student_data.student, "student_email_id")
        if student_user and student_user != from_user:
            # Check notification preferences
            if should_send_notification(student_data.student, "exam_notifications"):
                create_notification(from_user, student_user, message, doc.doctype, doc.name)

def send_attendance_notification(doc):
    """Send notification when student is marked absent"""
    student_user = frappe.db.get_value("Student", doc.student, "student_email_id")
    if not student_user:
        return
    
    from_user = frappe.session.user
    if from_user == student_user:
        return
    
    # Get course/date info
    course_name = ""
    if hasattr(doc, 'course') and doc.course:
        course_name = frappe.db.get_value("Course", doc.course, "course_name")
    
    date_info = ""
    if hasattr(doc, 'date') and doc.date:
        date_info = f" on <b>{frappe.utils.format_date(doc.date)}</b>"
    
    # Create message
    if course_name:
        message = f"You were marked absent for <b>{course_name}</b>{date_info}"
    else:
        message = f"You were marked absent{date_info}"
    
    # Check notification preferences
    if should_send_notification(doc.student, "attendance_notifications"):
        create_notification(from_user, student_user, message, doc.doctype, doc.name)

def create_notification(from_user, to_user, message, doctype, docname):
    """Create a notification with error handling"""
    try:
        notification = frappe.new_doc("Student Notification")
        notification.from_user = from_user
        notification.to_user = to_user
        notification.message = message
        notification.reference_document_type = doctype
        notification.reference_document_name = docname
        notification.insert(ignore_permissions=True)
        
        # Log success for debugging
        frappe.logger().debug(f"Notification created for {to_user}: {strip_html_tags(message)}")
        
        return True
    except Exception as e:
        log_notification_error("create_notification", e, {
            "from_user": from_user,
            "to_user": to_user,
            "doctype": doctype,
            "docname": docname
        })
        return False

def should_send_notification(student, notification_type):
    """Check if notification should be sent based on student preferences"""
    # Get student notification preferences
    prefs = frappe.db.get_value(
        "Student Notification Preferences",
        student,
        [notification_type, "push_notifications", "email_notifications"],
        as_dict=True
    )
    
    # If no preferences found, default to sending notifications
    if not prefs:
        return True
    
    # Check specific notification type preference
    return prefs.get(notification_type, True)

def log_notification_error(function_name, exception, doc_info):
    """Log notification errors with context"""
    doctype = doc_info.doctype if hasattr(doc_info, "doctype") else doc_info.get("doctype", "Unknown")
    docname = doc_info.name if hasattr(doc_info, "name") else doc_info.get("docname", "Unknown")
    
    error_msg = f"Error in {function_name}: {str(exception)} for {doctype} {docname}"
    frappe.log_error(error_msg, "Student Notification Error") 