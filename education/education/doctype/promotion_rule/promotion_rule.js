// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Promotion Rule', {
  refresh(frm) {
    if (!frm.is_new()) {
      frm.add_custom_button(__('Suggest Not Promoted Students'), () =>
        frappe.set_route('List', 'Not Promoted Student')
      )
    }
    frm.set_intro(
      __(
        'A student is not promoted when ANY criterion below is true. Each grade is decided by one enabled rule; a rule without programs is the default for all other grades.'
      )
    )
  },
})

frappe.ui.form.on('Promotion Rule Condition', {
  failed_subjects: describe,
  subject_mark_below: describe,
})

function describe(frm, cdt, cdn) {
  const row = locals[cdt][cdn]
  const n = cint(row.failed_subjects)
  const mark = flt(row.subject_mark_below)
  frappe.model.set_value(
    cdt,
    cdn,
    'description',
    n && mark ? __('{0} or more {1} below {2}', [n, n === 1 ? __('subject') : __('subjects'), mark]) : ''
  )
}
