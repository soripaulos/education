# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BannerDismissal(Document):
    def validate(self):
        """Ensure each user can only dismiss a banner once"""
        # Check if there's already a dismissal record for this user and banner
        existing = frappe.db.exists(
            "Banner Dismissal",
            {
                "banner": self.banner,
                "user": self.user,
                "name": ["!=", self.name]  # Exclude current document
            }
        )
        
        if existing:
            frappe.throw(f"User {self.user} has already dismissed banner {self.banner}")
            
    def before_insert(self):
        """Set the dismissed timestamp if not provided"""
        if not self.dismissed_on:
            self.dismissed_on = frappe.utils.now() 