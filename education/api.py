import frappe
from frappe import _
from frappe.utils import flt, now_datetime, cstr
import json

@frappe.whitelist()
def hello_world():
    frappe.log_error("Hello World API called!", "API Test")
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
    student_list = get_student_group_students(student_group)
    for i, student in enumerate(student_list):
        result = get_result(student.student, assessment_plan)
        if result:
            student_result = {}
            for d in result.details:
                student_result.update({d.assessment_criteria: [cstr(d.score), d.grade]})
            student_result.update(
                {"total_score": [cstr(result.total_score), result.grade], "comment": result.comment}
            )
            student.update(
                {
                    "assessment_details": student_result,
                    "docstatus": result.docstatus,
                    "name": result.name,
                }
            )
        else:
            student.update({"assessment_details": None})
    return student_list

@frappe.whitelist()
def get_assessment_details(assessment_plan):
    """Return all related criteria details with the assessment plan"""
    return frappe.get_all(
        "Assessment Plan Criteria",
        filters={"parent": assessment_plan},
        fields=["assessment_criteria", "maximum_score", "docstatus"],
        order_by="idx",
    )

@frappe.whitelist()
def get_result(student, assessment_plan, docstatus=None):
    """Return assessment result for the provided student and assessment criteria"""
    filters = {
        "student": student,
        "assessment_plan": assessment_plan,
        "docstatus": ("!=", 2)
    }
    if docstatus:
        filters["docstatus"] = docstatus
    result = frappe.get_all(
        "Assessment Result",
        filters=filters,
        fields=[
            "name",
            "total_score",
            "grade",
            "comment",
            "docstatus"
        ]
    )

    if not result:
        return None
    
    result = result[0]
    result.details = frappe.get_all(
        "Assessment Result Detail",
        filters={
            "parent": result.name
        },
        fields=[
            "assessment_criteria",
            "score",
            "grade"
        ]
    )
    return result

def get_grades(grading_scale, percentage):
    """Return grading scales in order of the percentage"""
    grades = []
    for d in get_grade_scale(grading_scale):
        if percentage >= d.threshold_percentage:
            return d.grade
    return ""

def get_grade_scale(grading_scale):
    """Return grade scales of a particular grading scale in order"""
    return frappe.get_all(
        "Grading Scale Interval",
        filters={"parent": grading_scale},
        fields=["grade", "threshold_percentage", "grade_description"],
        order_by="threshold_percentage desc",
    )

@frappe.whitelist()
def mark_assessment_result(assessment_plan, scores):
    """Mark assessment result for a student"""
    try:
        student_score = json.loads(scores) if isinstance(scores, str) else scores
        assessment_details = frappe.get_doc("Assessment Plan", assessment_plan)

        # Validate assessment plan
        if not assessment_details:
            frappe.throw(_("Assessment Plan not found"))

        # Process the score
        total_score = 0
        for criteria in assessment_details.assessment_criteria:
            criteria.maximum_score = float(criteria.maximum_score)
            if criteria.assessment_criteria in student_score.get("assessment_details", {}):
                score = flt(student_score["assessment_details"][criteria.assessment_criteria][0])
                if score < 0:
                    score = 0
                elif score > criteria.maximum_score:
                    score = criteria.maximum_score
                total_score += score

        # Update total score
        student_score["total_score"] = total_score

        # Get or create assessment result
        result = get_evaluation_criteria(assessment_details, student_score, total_score)
        result.save()
        
        return result

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Assessment Result Error")
        frappe.throw(_("Error marking assessment result: {0}").format(str(e)))

@frappe.whitelist()
def submit_assessment_results(assessment_plan, student_group, scores=None):
    """Submit assessment results for all students"""
    try:
        if scores:
            # Process scores from frontend
            scores_data = json.loads(scores) if isinstance(scores, str) else scores
            assessment_results = []
            
            for student_score in scores_data:
                # Mark individual result
                result = mark_assessment_result(assessment_plan, student_score)
                if result:
                    # Submit the result
                    result.docstatus = 1
                    result.save()
                    assessment_results.append(result.name)
        else:
            # Legacy method - get results from database
            student_list = get_student_group_students(student_group)
            assessment_results = []
            
            for student in student_list:
                doc = get_result(student.student, assessment_plan, 0)
                if doc and doc.docstatus == 0:
                    assessment_result = frappe.get_doc("Assessment Result", doc.name)
                    assessment_result.docstatus = 1
                    assessment_result.save()
                    assessment_results.append(assessment_result.name)
        
        return assessment_results

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Assessment Submission Error")
        frappe.throw(_("Error submitting assessment results: {0}").format(str(e)))

def get_evaluation_criteria(assessment_plan, student_score, total_score):
    """Return the Assessment Result for the student"""
    student = student_score["student"]
    assessment_result = get_assessment_result_doc(student, assessment_plan.name)
    
    if not assessment_result:
        assessment_result = frappe.new_doc("Assessment Result")
        assessment_result.student = student
        assessment_result.student_name = frappe.db.get_value("Student", student, "title")
        assessment_result.assessment_plan = assessment_plan.name
        assessment_result.program = assessment_plan.program
        assessment_result.course = assessment_plan.course
        assessment_result.academic_year = assessment_plan.academic_year
        assessment_result.academic_term = assessment_plan.academic_term
    else:
        # Clear the old assessment details
        assessment_result.details = []

    assessment_result.comment = student_score.get("comment", "")
    assessment_result.details = []
    
    # Add assessment details for each criteria
    for criteria in assessment_plan.assessment_criteria:
        result_detail = frappe.new_doc("Assessment Result Detail")
        result_detail.assessment_criteria = criteria.assessment_criteria
        result_detail.maximum_score = criteria.maximum_score
        
        # Get score for this criteria
        score = 0
        if criteria.assessment_criteria in student_score.get("assessment_details", {}):
            score = flt(student_score["assessment_details"][criteria.assessment_criteria][0])
            if score < 0:
                score = 0
            elif score > criteria.maximum_score:
                score = criteria.maximum_score
        
        result_detail.score = score
        
        # Calculate grade if grading scale exists
        if assessment_plan.grading_scale:
            score_percentage = (score / criteria.maximum_score) * 100
            result_detail.grade = get_grades(assessment_plan.grading_scale, score_percentage)
        
        assessment_result.append("details", result_detail)
    
    # Set total score and grade
    assessment_result.total_score = total_score
    
    if assessment_plan.grading_scale:
        total_percentage = (total_score / assessment_plan.maximum_assessment_score) * 100
        assessment_result.grade = get_grades(assessment_plan.grading_scale, total_percentage)
    
    return assessment_result

def get_assessment_result_doc(student, assessment_plan):
    """Return Assessment Result for student if exists"""
    assessment_result = frappe.get_all(
        "Assessment Result",
        filters={"student": student, "assessment_plan": assessment_plan, "docstatus": ("!=", 2)},
    )
    
    if assessment_result:
        return frappe.get_doc("Assessment Result", assessment_result[0])
    else:
        return None

@frappe.whitelist()
def create_or_update_assessment_log(student, assessment_plan, assessment_criteria, score, comments=""):
    """Creates a new Assessment Log Entry or updates the latest one if it exists."""
    try:
        # Validate score
        score = flt(score)
        if score < 0:
            score = 0
        # Optional: Add max score validation if needed later

        # Check if an entry exists for this specific combination logged today (or maybe ever? let's update latest)
        latest_entry_name = frappe.db.get_value("Assessment Log Entry", {
            "student": student,
            "assessment_plan": assessment_plan,
            "assessment_criteria": assessment_criteria
        }, "name", order_by="entry_datetime desc")

        if latest_entry_name:
            # Update existing entry
            log_entry = frappe.get_doc("Assessment Log Entry", latest_entry_name)
            log_entry.score = score
            log_entry.comments = comments
            log_entry.entry_datetime = now_datetime() # Update timestamp
            log_entry.save(ignore_permissions=True)
            frappe.db.commit() # Ensure save is committed immediately
            return {"status": "updated", "log_entry_name": log_entry.name, "logged_score": score}
        else:
            # Create new entry
            plan = frappe.get_doc("Assessment Plan", assessment_plan)
            student_doc = frappe.get_doc("Student", student)
            
            max_score = 0
            for criteria_detail in plan.assessment_criteria:
                if criteria_detail.assessment_criteria == assessment_criteria:
                    max_score = criteria_detail.maximum_score
                    break

            log_entry = frappe.new_doc("Assessment Log Entry")
            log_entry.student = student
            log_entry.student_name = student_doc.student_name
            log_entry.assessment_plan = assessment_plan
            log_entry.course = plan.course
            log_entry.academic_year = plan.academic_year
            log_entry.academic_term = plan.academic_term
            log_entry.assessment_criteria = assessment_criteria
            log_entry.maximum_score = max_score
            log_entry.score = score
            log_entry.entry_datetime = now_datetime()
            log_entry.comments = comments
            
            log_entry.insert(ignore_permissions=True)
            frappe.db.commit() # Ensure save is committed immediately
            return {"status": "created", "log_entry_name": log_entry.name, "logged_score": score}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create/Update Assessment Log Error")
        # Return error status to frontend
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_latest_assessment_logs(assessment_plan, student_group):
    """Fetches the latest score and comments for each student/criterion log entry."""
    try:
        students_details = get_student_group_students(student_group)
        students_in_group = [s.student for s in students_details]
        if not students_in_group:
            return {}

        plan_criteria = get_assessment_details(assessment_plan)
        criteria_names = [c.assessment_criteria for c in plan_criteria]
        if not criteria_names:
            return {}

        latest_logs = frappe.db.sql("""
            SELECT 
                student, assessment_criteria, score, comments
            FROM (
                SELECT 
                    student, assessment_criteria, score, comments,
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

        # Structure the data as { student_id: { criteria_name: {score: x, comments: y} } }
        structured_logs = {}
        for log in latest_logs:
            student = log.student
            criterion = log.assessment_criteria
            if student not in structured_logs:
                structured_logs[student] = {}
            structured_logs[student][criterion] = {
                "score": log.score,
                "comments": log.comments
            }
        
        return structured_logs

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Latest Assessment Logs Error")
        return {}

@frappe.whitelist()
def get_student_assessment_log_entries():
    """Fetches the latest assessment log entries for the logged-in student, grouped by term and plan."""
    student_id = frappe.session.user
    
    # Verify student exists
    if not frappe.db.exists("Student", student_id):
        return {} # Or raise an error?

    # Fetch the latest log entry for each unique combination of student, plan, and criteria
    # Using ROW_NUMBER() is efficient for this
    latest_logs_raw = frappe.db.sql("""
        SELECT 
            academic_term, assessment_plan, course, assessment_criteria, 
            maximum_score, score, comments, entry_datetime
        FROM (
            SELECT 
                ale.academic_term, ale.assessment_plan, ale.course, ale.assessment_criteria, 
                ale.maximum_score, ale.score, ale.comments, ale.entry_datetime,
                ROW_NUMBER() OVER(PARTITION BY ale.student, ale.assessment_plan, ale.assessment_criteria 
                                  ORDER BY ale.entry_datetime DESC) as rn
            FROM 
                `tabAssessment Log Entry` ale
            WHERE 
                ale.student = %(student)s
        ) ranked_logs
        WHERE rn = 1
        ORDER BY
            academic_term DESC, assessment_plan ASC, assessment_criteria ASC
    """, {"student": student_id}, as_dict=1)

    # Group the results by term, then by plan
    grouped_results = {}
    for log in latest_logs_raw:
        term = log.academic_term
        plan = log.assessment_plan
        
        if term not in grouped_results:
            grouped_results[term] = {}
        
        if plan not in grouped_results[term]:
            # Fetch assessment plan details once per plan
            plan_doc = frappe.get_doc("Assessment Plan", plan)
            grouped_results[term][plan] = {
                "course": log.course or plan_doc.course, # Use log's course, fallback to plan's
                "grading_scale": plan_doc.grading_scale,
                "entries": []
            }
        
        # Calculate grade if possible
        grade = ""
        if log.maximum_score and log.maximum_score > 0 and grouped_results[term][plan]["grading_scale"]:
            try:
                percentage = (flt(log.score) / flt(log.maximum_score)) * 100
                # Assuming get_grades function exists from previous API structure
                grade = get_grades(grouped_results[term][plan]["grading_scale"], percentage) 
            except Exception as e:
                 frappe.log_error(f"Error calculating grade for log entry: {e}", "Assessment Log Grade Calc")

        log["grade"] = grade # Add grade to the log dictionary
        grouped_results[term][plan]["entries"].append(log)
        
    return grouped_results

def update_website_context(context):
    """Update the website context for the Education app."""
    try:
        # Add student portal navigation to the context
        context.education_portal_links = [
            {"title": "Home", "route": "/me"},
            {"title": "Admissions", "route": "/admissions"},
            {"title": "Assessment Logs", "route": "/assessment-log"},
        ]
        
        # If user is a student, highlight the current page in navigation
        current_path = frappe.local.request.path if hasattr(frappe, 'local') and hasattr(frappe.local, 'request') else ""
        for link in context.education_portal_links:
            if current_path == link.get('route'):
                link['active'] = True
    except Exception as e:
        frappe.log_error(f"Error in update_website_context: {str(e)}", "Website Context")
        # Don't re-raise the error to prevent page breaking
                
    return context