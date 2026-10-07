// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

const EXTERNAL_EXAM_SUBJECTS = {
  'Grade 6 Regional Exam': [
    'Afaan Oromo', 'Amharic', 'English', 'Mathematics', 'General Science', 'Social Studies',
  ],
  'Grade 8 Regional Exam': [
    'Afaan Oromo', 'Amharic', 'English', 'Mathematics', 'General Science', 'Social Studies', 'Citizenship',
  ],
  'Grade 12 National Exam': {
    'Natural Science': ['English', 'Mathematics', 'Scholastic Aptitude', 'Physics', 'Chemistry', 'Biology'],
    'Social Science': ['English', 'Mathematics', 'Scholastic Aptitude', 'Geography', 'History', 'Economics'],
  },
}

frappe.ui.form.on('External Exam Result', {
  refresh(frm) {
    if (frm.doc.docstatus === 0) {
      frm.add_custom_button(__('Fill Usual Subjects'), () => fill_subjects(frm))
    }
    const colors = { Pass: 'green', Fail: 'red', Absent: 'orange', Withheld: 'orange' }
    if (colors[frm.doc.result_status] && !frm.is_new()) {
      frm.dashboard.set_headline_alert(
        __('{0}: {1}% average', [__(frm.doc.result_status), format_number(frm.doc.average_percentage, null, 2)]),
        colors[frm.doc.result_status]
      )
    }
  },

  exam_type(frm) {
    if (!frm.doc.exam_type) return
    frappe.call({
      method: 'education.education.doctype.external_exam_result.external_exam_result.get_default_pass_mark',
      args: { exam_type: frm.doc.exam_type },
      callback(r) {
        if (r.message) frm.set_value('pass_mark', r.message)
      },
    })
  },
})

frappe.ui.form.on('External Exam Subject', {
  score: recalculate,
  max_score: recalculate,
  subjects_remove: recalculate,
})

function recalculate(frm) {
  let total = 0
  let total_max = 0
  ;(frm.doc.subjects || []).forEach((row) => {
    const max = flt(row.max_score) || 100
    row.percentage = (flt(row.score) / max) * 100
    total += flt(row.score)
    total_max += max
  })
  frm.set_value('total_score', total)
  frm.set_value('total_max_score', total_max)
  frm.set_value('average_percentage', total_max ? (total / total_max) * 100 : 0)
  frm.refresh_field('subjects')
}

function fill_subjects(frm) {
  let subjects = EXTERNAL_EXAM_SUBJECTS[frm.doc.exam_type]
  if (!subjects) {
    frappe.msgprint(__('Choose the exam first.'))
    return
  }
  if (!Array.isArray(subjects)) {
    subjects = subjects[frm.doc.stream || 'Natural Science']
  }
  const existing = new Set((frm.doc.subjects || []).map((r) => r.subject))
  subjects.forEach((subject) => {
    if (!existing.has(subject)) frm.add_child('subjects', { subject, max_score: 100 })
  })
  frm.refresh_field('subjects')
}
