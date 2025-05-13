import frappe

def get_context(context):
    # Get package name from URL
    package_name = frappe.form_dict.package
    
    if not package_name:
        frappe.throw("Package name is required")
    
    # Get SCORM package
    try:
        doc = frappe.get_doc("SCORM Package", package_name)
    except frappe.DoesNotExistError:
        frappe.throw("SCORM package not found")
    
    # Get launch URL
    launch_url = frappe.get_site_url() + f"/files/scorm_packages/{doc.name}/{doc.launch_file}"
    
    context.update({
        "doc": doc,
        "launch_url": launch_url
    })
    
    return context 