# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AppealResult(Document):
	def validate(self):
		"""Validate the appeal before saving"""
		self.validate_duplicate_appeal()
		
	def validate_duplicate_appeal(self):
		"""Prevent duplicate appeals for the same exam"""
		existing = frappe.db.exists("Appeal Result", {
			"appealer": self.appealer,
			"semester": self.semester,
			"subject": self.subject,
			"exam": self.exam,
			"academic_year": self.academic_year,
			"status": ["in", ["Pending", "Under Review"]],
			"name": ["!=", self.name],
			"docstatus": ["!=", 2]
		})
		
		if existing:
			frappe.throw(
				f"An appeal for {self.subject} - {self.exam} in {self.semester} is already pending. "
				"Please wait for the previous appeal to be processed."
			)
	
	def before_submit(self):
		"""Set status to under review when submitted"""
		if self.status == "Pending":
			self.status = "Under Review"
	
	def on_submit(self):
		"""Send notification when appeal is submitted"""
		self.send_appeal_notification()
	
	def send_appeal_notification(self):
		"""Send notification to administrators about new appeal"""
		try:
			# Get education managers and system managers
			recipients = frappe.get_all("Has Role", 
				filters={
					"role": ["in", ["Education Manager", "System Manager"]]
				},
				fields=["parent"],
				distinct=True
			)
			
			recipient_emails = [
				frappe.db.get_value("User", r.parent, "email") 
				for r in recipients 
				if frappe.db.get_value("User", r.parent, "enabled")
			]
			
			if recipient_emails:
				subject = f"New Grade Appeal: {self.appealer} - {self.subject}"
				message = f"""
				A new grade appeal has been submitted:
				
				Student: {self.appealer}
				Class: {getattr(self, 'class', 'N/A')}
				Subject: {self.subject}
				Exam: {self.exam}
				Semester: {self.semester}
				Current Score: {self.current_score}/{self.max_score}
				
				Appeal Reason:
				{self.appeal}
				
				Please review and take appropriate action.
				"""
				
				frappe.sendmail(
					recipients=recipient_emails,
					subject=subject,
					message=message,
					reference_doctype=self.doctype,
					reference_name=self.name
				)
		except Exception as e:
			frappe.log_error(f"Failed to send appeal notification: {str(e)}")
			# Don't fail the submission if notification fails


@frappe.whitelist()
def approve_appeal(appeal_name, admin_response=""):
	"""Approve an appeal"""
	appeal = frappe.get_doc("Appeal Result", appeal_name)
	appeal.status = "Approved"
	appeal.admin_response = admin_response
	appeal.reviewed_by = frappe.session.user
	appeal.reviewed_on = frappe.utils.now()
	appeal.save()
	
	frappe.msgprint("Appeal has been approved.")
	return appeal


@frappe.whitelist()
def reject_appeal(appeal_name, admin_response=""):
	"""Reject an appeal"""
	appeal = frappe.get_doc("Appeal Result", appeal_name)
	appeal.status = "Rejected"
	appeal.admin_response = admin_response
	appeal.reviewed_by = frappe.session.user
	appeal.reviewed_on = frappe.utils.now()
	appeal.save()
	
	frappe.msgprint("Appeal has been rejected.")
	return appeal


@frappe.whitelist()
def get_student_appeals(student_name, academic_year=None):
	"""Get all appeals for a student"""
	filters = {"appealer": student_name}
	if academic_year:
		filters["academic_year"] = academic_year
	
	appeals = frappe.get_all("Appeal Result",
		filters=filters,
		fields=["*"],
		order_by="creation desc"
	)
	
	return appeals 