import frappe
from frappe.model.document import Document

class StudentExamResult(Document):
    def before_submit(self):
        # Validate score doesn't exceed max score
        if self.score > self.max_score:
            frappe.throw(f"Score ({self.score}) cannot exceed Max Score ({self.max_score})")
        
        # Auto-calculate percentage
        self.percentage = (self.score / self.max_score) * 100
