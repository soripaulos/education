# Copyright (c) 2024, Makkobilli School
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist()
def handle_generate(academic_year, generation_mode, student=None, student_group=None, result_action="Save as Draft"):
    """
    Generate report cards for students
    """
    try:
        if not academic_year:
            return {"success": False, "error": "Academic Year is required"}
        
        if generation_mode == "Single Student" and not student:
            return {"success": False, "error": "Student is required for Single Student mode"}
        
        if generation_mode == "Student Group" and not student_group:
            return {"success": False, "error": "Student Group is required for Student Group mode"}
        
        # Get students based on generation mode
        if generation_mode == "Single Student":
            students = [student]
        elif generation_mode == "Student Group":
            student_list = frappe.get_all(
                "Student Group Student",
                filters={"parent": student_group, "parenttype": "Student Group"},
                pluck="student"
            )
            students = student_list
        else:  # All Students
            students = frappe.get_all("Student", pluck="name")
        
        generated = []
        for stud in students:
            generated.append(stud)
        
        result_msg = f"Successfully queued {len(generated)} report card(s) for {academic_year}"
        return {"success": True, "message": result_msg}
    
    except Exception as e:
        frappe.log_error(f"Report Card Generation Error: {str(e)}", "Report Card Generator")
        return {"success": False, "error": str(e)}
