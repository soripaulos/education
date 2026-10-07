frappe.listview_settings['Student Exit'] = {
  add_fields: ['status', 'exit_type'],
  get_indicator(doc) {
    if (doc.docstatus === 0) return [__('Draft'), 'red', 'docstatus,=,0']
    if (doc.docstatus === 2) return [__('Cancelled'), 'grey', 'docstatus,=,2']
    if (doc.status === 'Readmitted') return [__('Readmitted'), 'green', 'status,=,Readmitted']
    if (doc.exit_type === 'Graduated') return [__('Graduated'), 'blue', 'exit_type,=,Graduated']
    return [__(doc.exit_type || 'Exited'), 'orange', 'exit_type,=,' + (doc.exit_type || '')]
  },
}
