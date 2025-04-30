# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe import bold


class StudentNotificationsMixin:
    """Mixin class for managing student notifications for education doctype events"""

    def notify_student_enrollment(self):
        """Send notification when a student is enrolled in a course or program"""
        if not hasattr(self, 'student') or not self.student:
            return
            
        student_user = frappe.db.get_value("Student", self.student, "student_email_id")
        if not student_user:
            return
            
        from_user = frappe.session.user
        if from_user == student_user:
            return
            
        # Get course/program name
        program_name = ""
        course_name = ""
        
        if hasattr(self, 'program') and self.program:
            program_name = frappe.db.get_value("Program", self.program, "program_name")
        
        if hasattr(self, 'course') and self.course:
            course_name = frappe.db.get_value("Course", self.course, "course_name")
        
        # Create message
        message = ""
        if program_name and course_name:
            message = f"You have been enrolled in {bold(course_name)} under program {bold(program_name)}"
        elif program_name:
            message = f"You have been enrolled in program {bold(program_name)}"
        elif course_name:
            message = f"You have been enrolled in course {bold(course_name)}"
        else:
            message = f"You have been enrolled in a new course/program"
        
        # Create notification
        notification = frappe.new_doc("Student Notification")
        notification.from_user = from_user
        notification.to_user = student_user
        notification.message = message
        notification.reference_document_type = self.doctype
        notification.reference_document_name = self.name
        notification.insert(ignore_permissions=True)

    def notify_assignment_submission(self):
        """Send notification when a student submits an assignment or when grades are updated"""
        if not hasattr(self, 'student') or not self.student:
            return
            
        student_user = frappe.db.get_value("Student", self.student, "student_email_id")
        if not student_user:
            return
            
        from_user = frappe.session.user
        if from_user == student_user:
            return
            
        status_field = 'status' if hasattr(self, 'status') else 'workflow_state'
        status = getattr(self, status_field, None)
        
        if not status or not self.has_value_changed(status_field):
            return
            
        # Create message based on status
        message = ""
        if status == "Submitted":
            message = f"Your assignment {bold(self.name)} has been received and is under review"
        elif status == "Completed" or status == "Graded":
            message = f"Your assignment {bold(self.name)} has been graded. Please check your results."
        elif status == "Returned":
            message = f"Your assignment {bold(self.name)} has been returned for revision"
        else:
            return  # Don't send for other statuses
        
        # Create notification
        notification = frappe.new_doc("Student Notification")
        notification.from_user = from_user
        notification.to_user = student_user
        notification.message = message
        notification.reference_document_type = self.doctype
        notification.reference_document_name = self.name
        notification.insert(ignore_permissions=True)

    def notify_fee_update(self):
        """Send notification for fee updates, payments due, etc."""
        if not hasattr(self, 'student') or not self.student:
            return
            
        student_user = frappe.db.get_value("Student", self.student, "student_email_id")
        if not student_user:
            return
            
        from_user = frappe.session.user
        if from_user == student_user:
            return
            
        # Create message based on fee status
        message = ""
        amount = getattr(self, 'grand_total', getattr(self, 'amount', 0))
        
        if hasattr(self, 'due_date') and self.due_date:
            due_date = frappe.utils.format_date(self.due_date)
            message = f"Fee payment of {bold(amount)} is due on {bold(due_date)}"
        elif hasattr(self, 'paid') and self.paid:
            message = f"Fee payment of {bold(amount)} has been received"
        else:
            message = f"A new fee of {bold(amount)} has been added to your account"
        
        # Create notification
        notification = frappe.new_doc("Student Notification")
        notification.from_user = from_user
        notification.to_user = student_user
        notification.message = message
        notification.reference_document_type = self.doctype
        notification.reference_document_name = self.name
        notification.insert(ignore_permissions=True)
    
    def notify_exam_schedule(self):
        """Send notification about exam schedules"""
        # This could be a group notification to all students in a course
        if not hasattr(self, 'course') or not self.course:
            return
            
        from_user = frappe.session.user
        
        # Get all students enrolled in the course
        students = frappe.get_all(
            "Course Enrollment", 
            filters={"course": self.course, "active": 1}, 
            fields=["student"]
        )
        
        if not students:
            return
            
        # Get course name for the message
        course_name = frappe.db.get_value("Course", self.course, "course_name")
        
        # Prepare date information
        exam_date = ""
        if hasattr(self, 'schedule_date') and self.schedule_date:
            exam_date = frappe.utils.format_date(self.schedule_date)
        elif hasattr(self, 'exam_date') and self.exam_date:
            exam_date = frappe.utils.format_date(self.exam_date)
        
        time_info = ""
        if hasattr(self, 'from_time') and self.from_time:
            from_time = frappe.utils.format_time(self.from_time)
            time_info = f" at {from_time}"
        
        # Create message
        if exam_date:
            message = f"Examination for {bold(course_name)} is scheduled on {bold(exam_date)}{time_info}"
        else:
            message = f"Examination for {bold(course_name)} has been scheduled"
        
        # Send notifications to all students
        for student_data in students:
            student_user = frappe.db.get_value("Student", student_data.student, "student_email_id")
            if student_user and student_user != from_user:
                notification = frappe.new_doc("Student Notification")
                notification.from_user = from_user
                notification.to_user = student_user
                notification.message = message
                notification.reference_document_type = self.doctype
                notification.reference_document_name = self.name
                notification.insert(ignore_permissions=True)

    def notify_attendance_update(self):
        """Send notification when student is marked absent"""
        if not hasattr(self, 'student') or not self.student:
            return
            
        student_user = frappe.db.get_value("Student", self.student, "student_email_id")
        if not student_user:
            return
            
        from_user = frappe.session.user
        if from_user == student_user:
            return
        
        # Only send notification for absence
        status = getattr(self, 'status', None)
        if not status or status != 'Absent' or not self.has_value_changed('status'):
            return
        
        # Get course/date info
        course_name = ""
        if hasattr(self, 'course') and self.course:
            course_name = frappe.db.get_value("Course", self.course, "course_name")
        
        date_info = ""
        if hasattr(self, 'date') and self.date:
            date_info = f" on {frappe.utils.format_date(self.date)}"
        
        # Create message
        if course_name:
            message = f"You were marked absent for {bold(course_name)}{date_info}"
        else:
            message = f"You were marked absent{date_info}"
        
        # Create notification
        notification = frappe.new_doc("Student Notification")
        notification.from_user = from_user
        notification.to_user = student_user
        notification.message = message
        notification.reference_document_type = self.doctype
        notification.reference_document_name = self.name
        notification.insert(ignore_permissions=True) 