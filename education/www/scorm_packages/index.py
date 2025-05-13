import frappe
from frappe import _

def get_context(context):
    # Get current user's student groups
    student_groups = get_student_groups(frappe.session.user)
    
    if not student_groups:
        context.packages = []
        return context
    
    # Get SCORM packages assigned to user's student groups
    packages = frappe.get_all(
        "SCORM Package",
        filters={
            "is_active": 1,
            "student_groups.student_group": ["in", student_groups]
        },
        fields=["name", "title", "description", "version"],
        distinct=True
    )
    
    # Get last attempt for each package
    for package in packages:
        last_attempt = frappe.get_all(
            "SCORM Session",
            filters={
                "package": package.name,
                "user": frappe.session.user
            },
            fields=["score_raw", "completion_status", "modified"],
            order_by="modified desc",
            limit=1
        )
        
        if last_attempt:
            package.last_attempt = {
                "score": last_attempt[0].score_raw,
                "status": last_attempt[0].completion_status,
                "date": last_attempt[0].modified
            }
    
    context.packages = packages
    return context

def get_student_groups(user):
    """Get student groups for the current user"""
    student_groups = frappe.get_all(
        "Student Group Student",
        filters={"student": user},
        fields=["parent"]
    )
    return [sg.parent for sg in student_groups] 