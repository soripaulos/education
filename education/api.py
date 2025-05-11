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
def mark_assessment_result(assessment_plan, student_data_json):
    """
    Marks or updates an assessment result for a single student.
    Saves the result as a Draft (docstatus=0).
    """
    try:
        if not isinstance(student_data_json, str):
            # This case should ideally not happen if called from frontend as designed
            frappe.throw(_("student_data_json must be a JSON string."))

        student_score_data = json.loads(student_data_json)

        assessment_plan_doc = frappe.get_doc("Assessment Plan", assessment_plan)
        if not assessment_plan_doc:
            frappe.throw(_("Assessment Plan {0} not found").format(assessment_plan))

        # Validate student_score_data structure
        if not student_score_data.get("student") or not isinstance(student_score_data.get("assessment_details"), dict):
            frappe.throw(_("Invalid student data structure received."))

        # Backend calculation/validation of scores
        be_total_score = 0
        processed_assessment_details = {}

        for criteria_def in assessment_plan_doc.assessment_criteria:
            criteria_name = criteria_def.assessment_criteria
            max_score_for_criteria = flt(criteria_def.maximum_score)
            score_val = 0
            grade_val = "" # Will be calculated by get_evaluation_criteria

            if criteria_name in student_score_data.get("assessment_details", {}):
                try:
                    score_input = student_score_data["assessment_details"][criteria_name][0]
                    score_val = flt(score_input)
                except (IndexError, TypeError, ValueError):
                    score_val = 0 
                
                if score_val < 0:
                    score_val = 0
                elif score_val > max_score_for_criteria:
                    score_val = max_score_for_criteria
            
            processed_assessment_details[criteria_name] = [score_val, grade_val]
            be_total_score += score_val
        
        # Update student_score_data with backend-validated scores and total
        student_score_data["assessment_details"] = processed_assessment_details
        student_score_data["total_score"] = be_total_score
        # Comment is expected to be directly in student_score_data.get("comment", "")

        assessment_result_doc = get_evaluation_criteria(assessment_plan_doc, student_score_data, be_total_score)
        
        assessment_result_doc.docstatus = 0 # Save as Draft
        assessment_result_doc.save(ignore_permissions=True)
        
        # To ensure the frontend gets up-to-date grades and other calculated fields,
        # we reload the document after save, as get_evaluation_criteria might not run all hooks of .save()
        # However, simply returning assessment_result_doc should be fine if it has all fields updated by get_evaluation_criteria.
        # For safety, can do: return frappe.get_doc("Assessment Result", assessment_result_doc.name)
        return assessment_result_doc

    except json.JSONDecodeError:
        frappe.log_error(frappe.get_traceback(), "Mark Assessment JSON Decode Error")
        frappe.throw(_("Invalid JSON data received for student assessment."))
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Mark Assessment Result Error")
        frappe.throw(_("Error processing student assessment: {0}").format(str(e)))

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
        # Clear the old assessment details before repopulating
        assessment_result.set("details", [])

    assessment_result.comment = student_score.get("comment", "")
    # assessment_result.details = [] # Already cleared above with .set("details", [])
    
    # Add assessment details for each criteria
    for criteria_def in assessment_plan.assessment_criteria:
        criteria_name = criteria_def.assessment_criteria
        max_score_for_criteria = flt(criteria_def.maximum_score)

        result_detail = frappe.new_doc("Assessment Result Detail")
        result_detail.assessment_criteria = criteria_name
        result_detail.maximum_score = max_score_for_criteria
        
        current_score_val = 0
        # Scores are now pre-processed and validated in student_score["assessment_details"]
        if criteria_name in student_score.get("assessment_details", {}):
            try:
                current_score_val = flt(student_score["assessment_details"][criteria_name][0])
            except (IndexError, TypeError, ValueError): # Should not happen if pre-processed
                current_score_val = 0
        
        result_detail.score = current_score_val
        
        if assessment_plan.grading_scale and max_score_for_criteria > 0:
            score_percentage = (current_score_val / max_score_for_criteria) * 100
            result_detail.grade = get_grades(assessment_plan.grading_scale, score_percentage)
        else:
            result_detail.grade = "" # Or some default like 'N/A'
        
        assessment_result.append("details", result_detail)
    
    assessment_result.total_score = total_score
    
    if assessment_plan.grading_scale and flt(assessment_plan.maximum_assessment_score) > 0:
        total_percentage = (flt(total_score) / flt(assessment_plan.maximum_assessment_score)) * 100
        assessment_result.grade = get_grades(assessment_plan.grading_scale, total_percentage)
    else:
        assessment_result.grade = "" # Or some default
    
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
def submit_assessment_results(assessment_plan, student_group, all_students_data_json=None):
    """
    Submits assessment results for all students based on provided data or existing drafts.
    If all_students_data_json is provided, it processes and submits that data.
    Otherwise, it attempts to submit existing draft (docstatus=0) Assessment Result documents.
    """
    submitted_count = 0
    failed_count = 0
    errors = []

    if all_students_data_json:
        try:
            all_students_data = json.loads(all_students_data_json)
            if not isinstance(all_students_data, list):
                frappe.throw(_("Processed student data must be a list."))

            for student_data in all_students_data:
                try:
                    # Use mark_assessment_result to create/update draft
                    # student_data should already be a dict here, no need to re-stringify
                    draft_result_doc = mark_assessment_result(assessment_plan, student_data_json=json.dumps(student_data))
                    
                    if draft_result_doc and draft_result_doc.name:
                        # Now submit the draft
                        submitted_doc = frappe.get_doc("Assessment Result", draft_result_doc.name)
                        if submitted_doc.docstatus == 0:
                            submitted_doc.submit() # Use a .submit() method if available, or set docstatus and save
                            # submitted_doc.docstatus = 1
                            # submitted_doc.save(ignore_permissions=True) # Ensure save after status change
                            submitted_count += 1
                        elif submitted_doc.docstatus == 1:
                            # Already submitted, count it as success for this batch operation
                            submitted_count += 1
                        else:
                            # Was cancelled or other status, log as error for this batch
                            failed_count += 1
                            errors.append(f"Student {student_data.get('student')}: Document {submitted_doc.name} has status {submitted_doc.docstatus} and was not submitted.")
                    else:
                        failed_count += 1
                        errors.append(f"Student {student_data.get('student')}: Failed to save draft.")
                except Exception as e:
                    failed_count += 1
                    student_id_for_error = student_data.get('student', 'Unknown Student')
                    errors.append(f"Student {student_id_for_error}: Error during processing - {str(e)}")
                    frappe.log_error(frappe.get_traceback(), f"Submit Assessment Error for Student {student_id_for_error}")
            
            if failed_count > 0:
                return {"status": "partial_success", "submitted_count": submitted_count, "failed_count": failed_count, "errors": errors}
            return {"status": "success", "submitted_count": submitted_count}

        except json.JSONDecodeError:
            frappe.log_error(frappe.get_traceback(), "Submit Assessment JSON Decode Error")
            return {"status": "error", "error": "Invalid JSON data received for all students."}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Submit Assessment General Error")
            return {"status": "error", "error": str(e)}

    else:
        # Fallback to legacy: submit existing drafts if no data is passed (less ideal now)
        student_list = get_student_group_students(student_group)
        assessment_results_names = []
        for student in student_list:
            try:
                draft_docs = frappe.get_all("Assessment Result",
                                            filters={"student": student.student, 
                                                     "assessment_plan": assessment_plan, 
                                                     "docstatus": 0},
                                            fields=["name"])
                for doc_meta in draft_docs:
                    doc_to_submit = frappe.get_doc("Assessment Result", doc_meta.name)
                    doc_to_submit.submit() # Use .submit() if available
                    # doc_to_submit.docstatus = 1
                    # doc_to_submit.save(ignore_permissions=True)
                    assessment_results_names.append(doc_to_submit.name)
                    submitted_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"Student {student.student}: Error submitting existing draft - {str(e)}")
                frappe.log_error(frappe.get_traceback(), f"Submit Existing Draft Error for Student {student.student}")
        
        if failed_count > 0:
            return {"status": "partial_success", "submitted_count": submitted_count, "failed_count": failed_count, "submitted_names": assessment_results_names, "errors": errors}
        return {"status": "success", "submitted_count": submitted_count, "submitted_names": assessment_results_names}

def get_student_group_students(student_group, include_inactive=0):
    """Return student list for the student group"""
    inactive_condition = "" if include_inactive else "and sd.active = 1"
    return frappe.db.sql(
        """select sd.student, sd.student_name, sd.idx,
    sd.active, sd.group_roll_number
    from `tabStudent Group Student` as sd
    where sd.parent = %s {0} order by sd.group_roll_number asc, sd.idx""".format(
            inactive_condition
        ),
        student_group,
        as_dict=1,
    )

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