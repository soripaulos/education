import frappe
from frappe import _
from frappe.utils import flt, now_datetime

@frappe.whitelist()
def hello_world():
    frappe.log_error("Hello World API called!") # Add log to confirm execution
    return "Hello from API!"

@frappe.whitelist()
def log_assessment_entry(student, assessment_plan, assessment_criteria, score, comments=""):
    """Logs a single assessment score entry for a student and criterion."""
    try:
        # Fetch necessary details (handles potential errors if plan/student not found)
        plan = frappe.get_doc("Assessment Plan", assessment_plan)
        student_doc = frappe.get_doc("Student", student)
        
        # Find the maximum score for this specific criterion within the plan
        max_score = 0
        for criteria_detail in plan.assessment_criteria:
            if criteria_detail.assessment_criteria == assessment_criteria:
                max_score = criteria_detail.maximum_score
                break
        
        if max_score == 0:
            # Optional: Decide how to handle if criterion not found in plan
            # frappe.throw(_("Assessment Criterion '{0}' not found in Plan '{1}'").format(assessment_criteria, assessment_plan))
            pass # Or allow logging even if max_score isn't defined in plan?

        # Basic validation server-side
        score = flt(score)
        if score < 0:
            score = 0
        # We might trust client-side for max_score validation, or re-validate here
        # if max_score > 0 and score > max_score:
        #     score = max_score 
            
        # Create new log entry
        log_entry = frappe.new_doc("Assessment Log Entry")
        log_entry.student = student
        log_entry.student_name = student_doc.student_name # Fetch student name
        log_entry.assessment_plan = assessment_plan
        log_entry.course = plan.course # Fetch from plan
        log_entry.academic_year = plan.academic_year # Fetch from plan
        log_entry.academic_term = plan.academic_term # Fetch from plan
        log_entry.assessment_criteria = assessment_criteria
        log_entry.maximum_score = max_score
        log_entry.score = score
        log_entry.entry_datetime = now_datetime() # Set timestamp
        log_entry.comments = comments
        # Amended From is likely not relevant here unless editing previous logs
        
        log_entry.insert(ignore_permissions=True) # Use insert for new documents
        # Do not submit log entries automatically, they are just logs
        
        # Return success indicator or the name of the created log
        return {"status": "success", "log_entry_name": log_entry.name, "logged_score": score}

    except frappe.DoesNotExistError as e:
        frappe.log_error(frappe.get_traceback(), "Assessment Log Entry Error")
        frappe.throw(_("Could not find related document: {0}").format(e))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Assessment Log Entry Error")
        frappe.throw(_("An error occurred while logging the assessment entry: {0}").format(e))

@frappe.whitelist()
def get_assessment_students(assessment_plan, student_group):
    # --- New Logic --- 
    # 1. Get list of students in the group
    student_list_details = get_student_group_students(student_group)
    students_in_group = [s.student for s in student_list_details]
    student_name_map = {s.student: s.student_name for s in student_list_details}

    if not students_in_group:
        return []

    # 2. Get all criteria for the assessment plan
    plan_criteria = frappe.get_all("Assessment Plan Criteria", 
                                     filters={"parent": assessment_plan}, 
                                     fields=["assessment_criteria", "maximum_score"],
                                     order_by="idx")
    if not plan_criteria:
        return [] # Or return student list with empty details?
    
    criteria_names = [c.assessment_criteria for c in plan_criteria]
    criteria_max_score_map = {c.assessment_criteria: c.maximum_score for c in plan_criteria}

    # 3. Fetch the latest log entry for each student+criterion combination
    # Use a subquery to rank entries by datetime desc and pick the latest (rank=1)
    latest_logs = frappe.db.sql("""
        SELECT 
            student, assessment_criteria, score, comments, entry_datetime, name
        FROM (
            SELECT 
                student, assessment_criteria, score, comments, entry_datetime, name,
                ROW_NUMBER() OVER(PARTITION BY student, assessment_criteria ORDER BY entry_datetime DESC) as rn
            FROM 
                `tabAssessment Log Entry`
            WHERE 
                assessment_plan = %(assessment_plan)s
                AND student IN %(students_in_group)s
                AND assessment_criteria IN %(criteria_names)s
        ) ranked_logs
        WHERE rn = 1
    """, {
        "assessment_plan": assessment_plan,
        "students_in_group": tuple(students_in_group),
        "criteria_names": tuple(criteria_names)
    }, as_dict=1)

    # 4. Structure the data for the frontend
    student_data_map = {}
    for log in latest_logs:
        student = log.student
        criterion = log.assessment_criteria
        if student not in student_data_map:
            student_data_map[student] = {
                "student": student,
                "student_name": student_name_map.get(student, "Unknown"), # Get name from map
                "assessment_details": {}
                # Add other base student info if needed
            }
        # Store score and comment for the specific criterion
        student_data_map[student]["assessment_details"][criterion] = {
            "score": log.score,
            "comments": log.comments,
            "entry_datetime": log.entry_datetime, # Keep track of when it was logged
            "log_name": log.name # Store the name of the log entry itself
        }

    # 5. Assemble the final list, ensuring all students and criteria are present
    result_list = []
    plan = frappe.get_doc("Assessment Plan", assessment_plan) # Needed for grading scale
    for student_id in students_in_group:
        student_info = student_data_map.get(student_id, {
            "student": student_id,
            "student_name": student_name_map.get(student_id, "Unknown"),
            "assessment_details": {}
        })
        
        current_scores = {}
        total_score = 0
        
        # Populate details for each criterion defined in the plan
        for criterion_def in plan_criteria:
            criterion_name = criterion_def.assessment_criteria
            max_score = criterion_max_score_map.get(criterion_name, 0)
            log_detail = student_info["assessment_details"].get(criterion_name)
            
            score = log_detail["score"] if log_detail else 0 # Default to 0 if no log yet
            grade = "" 
            if max_score > 0:
                 percentage = (flt(score) / max_score) * 100
                 grade = get_grade(plan.grading_scale, percentage) if plan.grading_scale else ""
            
            current_scores[criterion_name] = [score, grade] # Structure expected by old template [value, grade]
            total_score += flt(score)
            
            # Add comment if available from log
            if log_detail and log_detail.get("comments"):
                 current_scores["comment"] = log_detail.get("comments") # This overrides per-criterion comments, maybe adjust? Let's assume one comment field for now.
        
        # Calculate overall grade (similar to Assessment Result)
        overall_grade = ""
        if plan.maximum_assessment_score and plan.maximum_assessment_score > 0:
             overall_percentage = (flt(total_score) / plan.maximum_assessment_score) * 100
             overall_grade = get_grade(plan.grading_scale, overall_percentage) if plan.grading_scale else ""

        # Update the student info structure to match (roughly) the old format for template compatibility
        student_info["assessment_details"] = current_scores
        student_info["assessment_details"]["total_score"] = [total_score, overall_grade]
        # Add comment here if it wasn't added per criterion
        if "comment" not in student_info["assessment_details"]:
             # Get latest comment across all criteria for this student? Or leave blank?
             student_info["assessment_details"]["comment"] = student_info["assessment_details"].get("comment", "") # Use fetched comment if exists

        # Note: 'docstatus' and 'name' from the old get_result are no longer directly applicable 
        # as we are dealing with multiple log entries, not one main document.
        # We can set docstatus to 0 to indicate it's editable in the tool.
        student_info["docstatus"] = 0 
        # 'name' could potentially be the name of the *latest* log entry for linking, but might be confusing.
        # Let's omit 'name' for the main student object for now.

        result_list.append(student_info)

    return result_list

# --- Keep get_student_group_students, get_assessment_details, get_result (maybe unused now?), get_grade --- 
# --- Remove or comment out mark_assessment_result and submit_assessment_results if no longer used --- 
# @frappe.whitelist()
# def mark_assessment_result(assessment_plan, scores):
#     # ... old code ...

# @frappe.whitelist()
# def submit_assessment_results(assessment_plan, student_group):
#     # ... old code ... 