#!/usr/bin/env python3
"""
Migration script for School Feedback doctype
Run this to update existing documents with the new categories configuration
"""

import frappe
import json

def migrate_school_feedback_data():
    """Migrate existing School Feedback documents to new structure"""
    
    # Default configuration
    default_config = {
        "Academic Issues": {
            "Curriculum": ["Content Difficulty", "Pace Too Fast", "Pace Too Slow", "Missing Topics"],
            "Teaching Methods": ["Unclear Explanations", "Lack of Examples", "No Interactive Activities", "Poor Use of Technology"],
            "Assessment": ["Unfair Grading", "Too Many Tests", "Unclear Instructions", "Late Feedback"]
        },
        "Facility Issues": {
            "Classroom": ["Poor Lighting", "Uncomfortable Seating", "Temperature Issues", "Cleanliness"],
            "Technology": ["Broken Equipment", "Internet Issues", "Software Problems", "Lack of Resources"],
            "Safety": ["Security Concerns", "Emergency Procedures", "Maintenance Issues", "Accessibility"]
        },
        "Administrative Issues": {
            "Communication": ["Poor Information Sharing", "Late Notifications", "Unclear Policies", "Language Barriers"],
            "Scheduling": ["Conflicting Times", "Too Many Classes", "Break Time Issues", "Event Planning"],
            "Documentation": ["Missing Records", "Incorrect Information", "Slow Processing", "Lost Documents"]
        },
        "Other Issues": {}
    }
    
    # Get all School Feedback documents
    feedback_docs = frappe.get_all("School Feedback", fields=["name"])
    
    print(f"Found {len(feedback_docs)} School Feedback documents to migrate...")
    
    updated_count = 0
    
    for doc_info in feedback_docs:
        try:
            doc = frappe.get_doc("School Feedback", doc_info.name)
            
            # Add default configuration if missing
            if not doc.feedback_categories_config:
                doc.feedback_categories_config = json.dumps(default_config)
                doc.save()
                updated_count += 1
                print(f"Updated {doc.name} with default configuration")
                
        except Exception as e:
            print(f"Error updating {doc_info.name}: {str(e)}")
    
    print(f"Migration completed. Updated {updated_count} documents.")

if __name__ == "__main__":
    # Run this script from Frappe bench
    migrate_school_feedback_data() 
