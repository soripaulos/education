// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Exit', {
  setup(frm) {
    frm.set_query('national_exam_result', () => ({
      filters: {
        student: frm.doc.student,
        exam_type: 'Grade 12 National Exam',
        docstatus: 1,
      },
    }))
    frm.set_query('student_group', () => ({
      filters: frm.doc.program ? { program: frm.doc.program } : {},
    }))
  },

  refresh(frm) {
    if (frm.doc.docstatus === 1 && frm.doc.status === 'Exited') {
      frm.dashboard.set_headline_alert(
        __('This student has left. Documents handed out later (transcripts, certificates) can still be added below.'),
        'orange'
      )
      frm.add_custom_button(__('Record Document Issued'), () => {
        frm.add_child('documents_issued', {
          issued_on: frappe.datetime.get_today(),
          issued_by: frappe.session.user,
        })
        frm.refresh_field('documents_issued')
        frm.scroll_to_field('documents_issued')
      })
    }
    if (frm.doc.status === 'Readmitted') {
      frm.dashboard.set_headline_alert(
        __('Readmitted on {0}.', [frappe.datetime.str_to_user(frm.doc.readmitted_on)]),
        'green'
      )
    }
    if (frm.doc.student) {
      frm.add_custom_button(
        __('Student'),
        () => frappe.set_route('Form', 'Student', frm.doc.student),
        __('View')
      )
    }
  },

  student(frm) {
    if (!frm.doc.student || frm.doc.docstatus !== 0) return
    frappe.call({
      method: 'education.education.doctype.student_exit.student_exit.get_exit_defaults',
      args: { student: frm.doc.student },
      callback(r) {
        const values = r.message || {}
        Object.keys(values).forEach((key) => {
          if (values[key] && !frm.doc[key]) frm.set_value(key, values[key])
        })
      },
    })
  },
})
