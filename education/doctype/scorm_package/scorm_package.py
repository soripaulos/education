import frappe
import os
import zipfile
import xml.etree.ElementTree as ET
from frappe.utils import get_site_path

@frappe.whitelist()
def extract_scorm_package(docname):
    """Extract SCORM package and find launch file"""
    doc = frappe.get_doc("SCORM Package", docname)
    
    # Get file path
    file_path = frappe.get_site_path("private", "files", doc.zip_file)
    
    # Create extraction directory
    extract_dir = frappe.get_site_path("public", "files", "scorm_packages", docname)
    os.makedirs(extract_dir, exist_ok=True)
    
    # Extract ZIP
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Find imsmanifest.xml
    manifest_path = os.path.join(extract_dir, "imsmanifest.xml")
    if not os.path.exists(manifest_path):
        frappe.throw("Invalid SCORM package: imsmanifest.xml not found")
    
    # Parse manifest to find launch file
    tree = ET.parse(manifest_path)
    root = tree.getroot()
    
    # Find first resource with SCORM type
    ns = {'ns': 'http://www.imsproject.org/xsd/imscp_rootv1p1p2'}
    resources = root.findall('.//ns:resource', ns)
    
    launch_file = None
    for resource in resources:
        if 'scormtype' in resource.attrib:
            launch_file = resource.attrib.get('href')
            break
    
    if not launch_file:
        frappe.throw("Invalid SCORM package: No launch file found in manifest")
    
    # Update launch file path
    doc.launch_file = launch_file
    doc.save()
    
    return {
        "status": "success",
        "launch_file": launch_file
    }

@frappe.whitelist()
def get_scorm_package_url(docname):
    """Get URL for launching SCORM package"""
    doc = frappe.get_doc("SCORM Package", docname)
    site_url = frappe.utils.get_url()
    
    return {
        "url": f"{site_url}/files/scorm_packages/{docname}/{doc.launch_file}"
    } 