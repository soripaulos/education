import frappe
import os
import zipfile
from frappe.model.document import Document
from frappe.utils import get_files_path
from pathlib import Path

class CourseChapter(Document):
    def validate(self):
        """Validate SCORM package if provided"""
        if self.is_scorm_package and self.scorm_package:
            if not self.scorm_package.endswith(('.zip')):
                frappe.throw('SCORM package must be a ZIP file')
            
            # Validate required parent document
            if not self.course:
                frappe.throw('Course is required for SCORM chapters')
    
    def after_insert(self):
        """Extract SCORM package after insert if it's a SCORM chapter"""
        if self.is_scorm_package and self.scorm_package:
            self.extract_scorm_package()
    
    def on_update(self):
        """Extract SCORM package on update if package has changed"""
        if self.is_scorm_package and self.scorm_package:
            # Check if file has changed or is new
            if self.has_value_changed('scorm_package'):
                self.extract_scorm_package()
    
    def extract_scorm_package(self):
        """Extract SCORM package to the correct location for web access"""
        try:
            if not self.scorm_package:
                return
            
            # Handle file paths
            full_path = get_files_path() + "/" + self.scorm_package.split("/files/")[1]
            
            if not os.path.exists(full_path):
                frappe.msgprint("SCORM package file not found")
                return
            
            # Extract package name without extension
            file_name = os.path.basename(self.scorm_package)
            folder_name = os.path.splitext(file_name)[0]
            
            # Create extraction folder
            site_path = frappe.utils.get_site_path()
            extract_path = os.path.join(site_path, "public", "education", "scorm", folder_name)
            
            # Create directory if it doesn't exist
            os.makedirs(extract_path, exist_ok=True)
            
            # Extract ZIP file
            with zipfile.ZipFile(full_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            frappe.msgprint(f"SCORM package extracted successfully to {extract_path}")
            
        except Exception as e:
            frappe.log_error(f"SCORM Package Extraction Error: {str(e)}", "SCORM Extraction")
            frappe.throw(f"Error extracting SCORM package: {str(e)}") 