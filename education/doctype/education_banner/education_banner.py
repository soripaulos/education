# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, get_datetime


class EducationBanner(Document):
    def validate(self):
        """Validate banner dates and settings"""
        # Ensure start date is before or equal to end date
        if getdate(self.start_date) > getdate(self.end_date):
            frappe.throw("End Date cannot be before Start Date")
        
        # Ensure icon is valid if specified
        if self.icon and len(self.icon.strip()) > 0:
            # Common Feather icons for validation
            valid_icons = [
                "info", "alert-circle", "alert-triangle", "check-circle", "x-circle",
                "bell", "calendar", "book", "clock", "edit", "file", "home",
                "mail", "message-circle", "user", "users", "settings"
            ]
            
            icon = self.icon.strip().lower()
            if '-' not in icon and icon not in valid_icons:
                frappe.msgprint(
                    f"The icon '{self.icon}' may not be a valid Feather icon. Please check."
                )
        
        # Set default values if needed
        if not self.banner_type:
            self.banner_type = "info"
        
        if not self.icon:
            # Set default icon based on banner type
            if self.banner_type == "info":
                self.icon = "info"
            elif self.banner_type == "success":
                self.icon = "check-circle"
            elif self.banner_type == "warning":
                self.icon = "alert-triangle"
            elif self.banner_type == "error":
                self.icon = "alert-circle"
        
        # Auto dismiss should be a non-negative integer
        if self.auto_dismiss and self.auto_dismiss < 0:
            self.auto_dismiss = 0
            
    def on_update(self):
        """Clear banner cache when updated"""
        frappe.cache().delete_key("active_education_banners")
            
    def on_trash(self):
        """Clear banner cache when deleted"""
        frappe.cache().delete_key("active_education_banners") 