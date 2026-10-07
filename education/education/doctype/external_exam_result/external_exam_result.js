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
    if (frm.doc.docstatus === 0 && frm.doc.exam_type === 'Grade 12 National Exam') {
      frm.add_custom_button(__('Fill Usual Subjects'), () => fill_subjects(frm))
    }
    const colors = { Pass: 'green', Fail: 'red', Absent: 'orange', Withheld: 'orange' }
    if (colors[frm.doc.result_status] && !frm.is_new()) {
      frm.dashboard.set_headline_alert(
        frm.doc.average_percentage
          ? __('{0}: {1}% average', [__(frm.doc.result_status), format_number(frm.doc.average_percentage, null, 2)])
          : __(frm.doc.result_status),
        colors[frm.doc.result_status]
      )
    }
  },

  total_score: average_from_totals,
  total_max_score: average_from_totals,
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

function average_from_totals(frm) {
  if ((frm.doc.subjects || []).length) return
  if (flt(frm.doc.total_max_score) > 0) {
    frm.set_value('average_percentage', (flt(frm.doc.total_score) / flt(frm.doc.total_max_score)) * 100)
  }
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
