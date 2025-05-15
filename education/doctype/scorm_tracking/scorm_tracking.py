import frappe
from frappe.model.document import Document

class SCORMTracking(Document):
    def validate(self):
        """
        Validate the SCORM tracking data
        """
        # Ensure score is between 0 and 100
        if self.score:
            if float(self.score) < 0:
                self.score = 0
            elif float(self.score) > 100:
                self.score = 100
                
        # Ensure attempts is at least 1 for new records
        if not self.is_new():
            if self.attempts < 1:
                self.attempts = 1 