// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student', {
  refresh: function (frm) {
    frm.set_query('user', function (doc) {
      return {
        filters: {
          ignore_user_type: 1,
        },
      }
    })

    if (!frm.is_new()) {
      frm.add_custom_button(__('Accounting Ledger'), function () {
        frappe.set_route('query-report', 'General Ledger', {
          party_type: 'Customer',
          party: frm.doc.customer,
        })
      })
      show_exit_status(frm)
    }

    frappe.db
      .get_single_value('Education Settings', 'user_creation_skip')
      .then((r) => {
        if (cint(r) !== 1) {
          frm.set_df_property('student_email_id', 'reqd', 1)
        }
      })

    // keep age display in sync on load
    frm.doc.age = get_age_from_dob(frm.doc.date_of_birth)
    frm.refresh_field('age')
  },

  date_of_birth: function (frm) {
    // virtual field: compute for display only (not stored)
    frm.doc.age = get_age_from_dob(frm.doc.date_of_birth)
    frm.refresh_field('age')
  },
})

function show_exit_status(frm) {
  // Leaving is recorded on a Student Exit; the exit fields on this form are
  // filled from it. Show where the student stands and how to change it.
  frappe.db
    .get_list('Student Exit', {
      filters: { student: frm.doc.name, docstatus: 1, status: 'Exited' },
      fields: ['name', 'exit_type', 'exit_date'],
      order_by: 'exit_date desc',
      limit: 1,
    })
    .then((rows) => {
      if (rows && rows.length) {
        const exit = rows[0]
        frm.dashboard.set_headline_alert(
          __('Left the school on {0} ({1}). See {2}.', [
            frappe.datetime.str_to_user(exit.exit_date),
            __(exit.exit_type),
            `<a href="/app/student-exit/${encodeURIComponent(exit.name)}">${exit.name}</a>`,
          ]),
          'orange'
        )
        frm.add_custom_button(__('Open Exit Record'), () =>
          frappe.set_route('Form', 'Student Exit', exit.name)
        )
      } else if (frm.doc.enabled) {
        frm.add_custom_button(__('Record Exit'), () =>
          frappe.new_doc('Student Exit', { student: frm.doc.name })
        )
      } else {
        frm.dashboard.set_headline_alert(
          __('This student is disabled but has no exit record. Record one so the reason for leaving is kept.'),
          'yellow'
        )
        frm.add_custom_button(__('Record Exit'), () =>
          frappe.new_doc('Student Exit', { student: frm.doc.name })
        )
      }
    })
}

function get_age_from_dob(dob) {
  if (!dob) return null

  const dobDate = frappe.datetime.str_to_obj(dob)
  const todayDate = frappe.datetime.str_to_obj(frappe.datetime.get_today())
  if (!dobDate || !todayDate) return null

  const msPerDay = 24 * 60 * 60 * 1000
  const ageInYears = (todayDate.getTime() - dobDate.getTime()) / msPerDay / 365.25
  if (ageInYears < 0) return 0.0
  return Math.round(ageInYears * 10) / 10
}

frappe.ui.form.on('Student Guardian', {
  guardians_add: function (frm) {
    frm.fields_dict['guardians'].grid.get_field('guardian').get_query =
      function (doc) {
        let guardian_list = []
        if (!doc.__islocal) guardian_list.push(doc.guardian)
        $.each(doc.guardians, function (idx, val) {
          if (val.guardian) guardian_list.push(val.guardian)
        })
        return { filters: [['Guardian', 'name', 'not in', guardian_list]] }
      }
  },
})
