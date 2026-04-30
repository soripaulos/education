#!/usr/bin/env python3
"""
Utility script to update percentage field in all Student Term Subject Result records

This script calculates and updates the percentage field for all existing records
based on score and max_score values.

Usage:
    Method 1: Via bench console (recommended)
    ----------------------------------------
    bench --site [site-name] console
    >>> from education.education.doctype.student_term_subject_result.student_term_subject_result import update_all_percentages
    >>> update_all_percentages()
    
    Method 2: Via execute command
    -----------------------------
    bench --site [site-name] execute education.update_percentages.run
    
    Method 3: Direct execution (for testing)
    ----------------------------------------
    cd /path/to/frappe-bench
    bench --site [site-name] console
    >>> exec(open('apps/education/education/update_percentages.py').read())
"""

import frappe
from frappe.utils import flt


def run(commit=True, verbose=True):
	"""
	Main function to update all percentages
	
	Args:
		commit (bool): If True, commits changes to database. If False, dry run.
		verbose (bool): If True, prints detailed output
	
	Returns:
		dict: Summary of updates
	"""
	if verbose:
		print("\n" + "="*70)
		print("Student Term Subject Result - Percentage Update Utility")
		print("="*70 + "\n")
	
	# Get all records
	results = frappe.get_all(
		"Student Term Subject Result",
		fields=["name", "score", "max_score", "percentage", "docstatus", "student_name", "subject"],
		order_by="modified desc"
	)
	
	if not results:
		if verbose:
			print("No records found in the database.")
		return {"total": 0, "updated": 0, "skipped": 0, "errors": 0}
	
	if verbose:
		print(f"Found {len(results)} records to process...")
		print(f"Mode: {'COMMIT' if commit else 'DRY RUN (no changes will be saved)'}\n")
	
	updated_count = 0
	skipped_count = 0
	error_count = 0
	updates = []
	
	for result in results:
		try:
			score = flt(result.score)
			max_score = flt(result.max_score)
			old_percentage = flt(result.percentage)
			
			# Calculate new percentage
			if max_score > 0:
				new_percentage = round((score / max_score) * 100, 2)
			else:
				new_percentage = 0
			
			# Check if update is needed (with tolerance for floating point)
			if abs(old_percentage - new_percentage) > 0.01:
				# Direct SQL update to bypass validation
				if commit:
					frappe.db.sql("""
						UPDATE `tabStudent Term Subject Result`
						SET percentage = %s, modified = NOW()
						WHERE name = %s
					""", (new_percentage, result.name))
				
				updated_count += 1
				
				update_info = {
					"name": result.name,
					"student": result.student_name or "Unknown",
					"subject": result.subject or "Unknown",
					"old_percentage": old_percentage,
					"new_percentage": new_percentage,
					"score": score,
					"max_score": max_score
				}
				updates.append(update_info)
				
				if verbose:
					status = "✓" if commit else "○"
					print(f"{status} {result.name} ({result.student_name} - {result.subject})")
					print(f"   {score}/{max_score} → {old_percentage}% → {new_percentage}%")
			else:
				skipped_count += 1
		
		except Exception as e:
			error_count += 1
			if verbose:
				print(f"✗ Error updating {result.name}: {str(e)}")
	
	if commit:
		frappe.db.commit()
		if verbose:
			print(f"\n✓ Changes committed to database!")
	else:
		if verbose:
			print(f"\n⚠ DRY RUN: No changes were committed")
			print(f"  Run with commit=True to apply changes")
	
	if verbose:
		print("\n" + "="*70)
		print("Summary:")
		print("-"*70)
		print(f"  Total records:      {len(results)}")
		print(f"  Updated:            {updated_count}")
		print(f"  Already correct:    {skipped_count}")
		print(f"  Errors:             {error_count}")
		print("="*70 + "\n")
		
		if updated_count > 0 and not commit:
			print("To apply these changes, run:")
			print("  update_all_percentages(commit=True)")
			print()
	
	return {
		"total": len(results),
		"updated": updated_count,
		"skipped": skipped_count,
		"errors": error_count,
		"updates": updates if not commit else []
	}


def update_single_record(record_name, commit=True):
	"""
	Update percentage for a single record
	
	Args:
		record_name (str): Name of the Student Term Subject Result record
		commit (bool): If True, commits changes
	
	Returns:
		dict: Update result
	"""
	try:
		result = frappe.get_doc("Student Term Subject Result", record_name)
		
		old_percentage = flt(result.percentage)
		
		# Calculate new percentage
		if flt(result.max_score) > 0:
			new_percentage = round(flt(result.score) / flt(result.max_score) * 100, 2)
		else:
			new_percentage = 0
		
		result.percentage = new_percentage
		
		if commit:
			# Use SQL update to avoid re-triggering validation
			frappe.db.sql("""
				UPDATE `tabStudent Term Subject Result`
				SET percentage = %s, modified = NOW()
				WHERE name = %s
			""", (new_percentage, record_name))
			frappe.db.commit()
		
		return {
			"success": True,
			"name": record_name,
			"old_percentage": old_percentage,
			"new_percentage": new_percentage,
			"updated": old_percentage != new_percentage
		}
	
	except Exception as e:
		return {
			"success": False,
			"name": record_name,
			"error": str(e)
		}


def update_by_student_group(student_group, commit=True, verbose=True):
	"""
	Update percentages for all records in a specific student group
	
	Args:
		student_group (str): Name of the student group
		commit (bool): If True, commits changes
		verbose (bool): If True, prints output
	
	Returns:
		dict: Summary of updates
	"""
	if verbose:
		print(f"\nUpdating percentages for Student Group: {student_group}\n")
	
	results = frappe.get_all(
		"Student Term Subject Result",
		filters={"student_group": student_group},
		fields=["name", "score", "max_score", "percentage", "student_name", "subject"],
		order_by="student_name, subject"
	)
	
	if not results:
		if verbose:
			print(f"No records found for student group: {student_group}")
		return {"total": 0, "updated": 0, "skipped": 0, "errors": 0}
	
	if verbose:
		print(f"Found {len(results)} records in this student group...\n")
	
	updated_count = 0
	skipped_count = 0
	error_count = 0
	
	for result in results:
		try:
			score = flt(result.score)
			max_score = flt(result.max_score)
			old_percentage = flt(result.percentage)
			
			if max_score > 0:
				new_percentage = round((score / max_score) * 100, 2)
			else:
				new_percentage = 0
			
			if abs(old_percentage - new_percentage) > 0.01:
				if commit:
					frappe.db.sql("""
						UPDATE `tabStudent Term Subject Result`
						SET percentage = %s, modified = NOW()
						WHERE name = %s
					""", (new_percentage, result.name))
				
				updated_count += 1
				
				if verbose:
					print(f"✓ {result.student_name} - {result.subject}: {old_percentage}% → {new_percentage}%")
			else:
				skipped_count += 1
		
		except Exception as e:
			error_count += 1
			if verbose:
				print(f"✗ Error updating {result.name}: {str(e)}")
	
	if commit:
		frappe.db.commit()
		if verbose:
			print(f"\n✓ Changes committed!")
	
	if verbose:
		print(f"\nSummary: {updated_count} updated, {skipped_count} already correct, {error_count} errors\n")
	
	return {
		"total": len(results),
		"updated": updated_count,
		"skipped": skipped_count,
		"errors": error_count
	}


# Convenience alias
update_all_percentages = run


if __name__ == "__main__":
	print(__doc__)
	print("\nTo run this script, use one of the methods described above.")
