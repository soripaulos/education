import frappe
from frappe.utils import now

@frappe.whitelist(allow_guest=False)
def save_scorm_data(course_chapter, score, status):
    """
    Save SCORM tracking data for a user.
    This is a simplified version focusing only on score and completion status.
    
    Args:
        course_chapter: Name of the course chapter
        score: Value from cmi.core.score.raw (0-100)
        status: Value from cmi.core.lesson_status (completed, incomplete, etc)
    """
    user = frappe.session.user
    
    # Find existing session or create new
    existing = frappe.db.exists(
        "SCORM Tracking",
        {"user": user, "course_chapter": course_chapter}
    )
    
    if existing:
        # Update existing record
        doc = frappe.get_doc("SCORM Tracking", existing)
        
        # Increment attempt count when retaking
        if status == "incomplete" and doc.status in ["completed", "passed", "failed"]:
            doc.attempts += 1
        
        # Update score only if higher than previous (best attempt tracking)
        if float(score or 0) > float(doc.score or 0):
            doc.score = score
            
        # Update status - prioritize completion states
        if status in ["completed", "passed", "failed"] or not doc.status:
            doc.status = status
            
        doc.last_attempt = now()
        doc.save(ignore_permissions=True)
        
    else:
        # Create new tracking record
        doc = frappe.get_doc({
            "doctype": "SCORM Tracking",
            "user": user,
            "course_chapter": course_chapter,
            "score": score,
            "status": status,
            "attempts": 1,
            "last_attempt": now()
        })
        doc.insert(ignore_permissions=True)
    
    frappe.db.commit()
    return {
        "success": True,
        "attempts": doc.attempts,
        "score": doc.score,
        "status": doc.status
    }

@frappe.whitelist(allow_guest=False)
def get_scorm_data(course_chapter):
    """
    Get SCORM tracking data for the current user and course chapter
    """
    user = frappe.session.user
    
    data = frappe.db.get_value(
        "SCORM Tracking",
        {"user": user, "course_chapter": course_chapter},
        ["score", "status", "attempts", "last_attempt"],
        as_dict=1
    )
    
    return data if data else {
        "score": 0,
        "status": "not attempted",
        "attempts": 0,
        "last_attempt": None
    }

@frappe.whitelist(allow_guest=False)
def get_course_data(course):
    """
    Get course details including chapters with SCORM indicators
    """
    course_doc = frappe.get_doc("Course", course)
    chapters = []
    
    for idx, chapter in enumerate(course_doc.get("chapters") or []):
        chapter_data = {
            "name": chapter.name,
            "title": chapter.title,
            "is_scorm_package": chapter.is_scorm_package if hasattr(chapter, 'is_scorm_package') else 0,
            "index": idx + 1
        }
        
        # Get tracking data if it's a SCORM package
        if chapter_data["is_scorm_package"]:
            tracking = get_scorm_data(chapter.name)
            chapter_data.update({
                "score": tracking.get("score", 0),
                "status": tracking.get("status", "not attempted"),
                "attempts": tracking.get("attempts", 0)
            })
            
        chapters.append(chapter_data)
    
    return {
        "name": course_doc.name,
        "title": course_doc.course_name,
        "description": course_doc.description,
        "chapters": chapters
    }

@frappe.whitelist(allow_guest=False)
def get_scorm_chapter(chapter):
    """
    Get SCORM chapter details for launching
    """
    chapter_doc = frappe.get_doc("Course Chapter", chapter)
    
    if not chapter_doc.is_scorm_package or not chapter_doc.scorm_package:
        return {
            "error": "This chapter does not have a valid SCORM package"
        }
    
    file_url = chapter_doc.scorm_package
    
    # Extract the folder name from the URL
    if "/files/" in file_url:
        folder_name = file_url.split("/files/")[1].rsplit(".", 1)[0]
        launch_url = f"/assets/education/scorm/{folder_name}/index.html"
    else:
        launch_url = None
        
    tracking = get_scorm_data(chapter)
    
    return {
        "name": chapter_doc.name,
        "title": chapter_doc.title,
        "launch_file": launch_url,
        "status": tracking.get("status"),
        "score": tracking.get("score"),
        "attempts": tracking.get("attempts")
    } 