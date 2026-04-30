// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Weekly Course Schedule Tool', {
  setup(frm) {
    frm.add_fetch('student_group', 'program', 'program')
    frm.add_fetch('student_group', 'academic_year', 'academic_year')
    frm.add_fetch('student_group', 'academic_term', 'academic_term')
  },

  refresh(frm) {
    frm.disable_save()
    frm.page.set_primary_action(__('Create Weekly Schedule'), () => {
      frm.trigger('create_schedules')
    })
  },

  student_group(frm) {
    frm.doc.schedule = []
    frm.refresh_field('schedule')

    if (!frm.doc.student_group) return

    frappe.after_ajax(() => {
      if (frm.doc.program) {
        frm.trigger('load_periods')
      }
      frm.trigger('set_default_room')
    })
  },

  load_periods(frm) {
    frm
      .call('populate_periods')
      .then(() => {
        frm.refresh_field('schedule')
      })
  },

  set_default_room(frm) {
    frm.call('get_default_room').then((r) => {
      if (r && r.message) {
        frm.set_value('default_room', r.message)
      }
    })
  },

  create_schedules(frm) {
    frappe.dom.freeze(__('Creating Course Schedules...'))
    frm
      .call('create_schedules')
      .fail(() => {
        frappe.dom.unfreeze()
        frappe.msgprint(__('Failed to create Course Schedules'))
      })
      .then((r) => {
        frappe.dom.unfreeze()
        if (!r || !r.message) {
          frappe.throw(__('There were errors creating Course Schedules'))
          return
        }

        const { created, errors, rescheduled, reschedule_errors } = r.message
        let html = ''

        if (rescheduled && rescheduled.length) {
          html += `<p><strong>${__('Rescheduled (deleted)')}: ${rescheduled.length}</strong></p>`
        }
        if (reschedule_errors && reschedule_errors.length) {
          html += `<p class="text-danger">${__('Failed to delete')}: ${reschedule_errors.length}</p>`
        }

        if (created && created.length) {
          const rows = created
            .map(
              (c) => `
              <tr>
                <td><a href="/app/course-schedule/${c.name}">${c.name}</a></td>
                <td>${c.schedule_date}</td>
                <td>${c.course}</td>
                <td>Period ${c.period}</td>
              </tr>`
            )
            .join('')

          html += `
            <table class="table table-bordered">
              <caption>${__('Course Schedules Created')}: ${created.length}</caption>
              <thead>
                <tr>
                  <th>${__('Schedule')}</th>
                  <th>${__('Date')}</th>
                  <th>${__('Subject')}</th>
                  <th>${__('Period')}</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>`
        }

        if (errors && errors.length) {
          const errRows = errors
            .map(
              (e) => `
              <tr>
                <td>${e.date}</td>
                <td>${e.course}</td>
                <td>Period ${e.period}</td>
                <td>${e.message}</td>
              </tr>`
            )
            .join('')

          html += `
            <table class="table table-bordered text-danger">
              <caption>${__('Errors')}: ${errors.length}</caption>
              <thead>
                <tr>
                  <th>${__('Date')}</th>
                  <th>${__('Subject')}</th>
                  <th>${__('Period')}</th>
                  <th>${__('Error')}</th>
                </tr>
              </thead>
              <tbody>${errRows}</tbody>
            </table>`
        }

        if (!html) {
          html = `<p>${__('No schedules were created. Make sure subjects are assigned to periods.')}</p>`
        }

        frappe.msgprint({ title: __('Weekly Schedule Results'), message: html, wide: true })
      })
  },
})

frappe.ui.form.on('Weekly Schedule Entry', {
  monday(frm, cdt, cdn) {
    set_instructor_for_day(frm, cdt, cdn, 'monday')
  },
  tuesday(frm, cdt, cdn) {
    set_instructor_for_day(frm, cdt, cdn, 'tuesday')
  },
  wednesday(frm, cdt, cdn) {
    set_instructor_for_day(frm, cdt, cdn, 'wednesday')
  },
  thursday(frm, cdt, cdn) {
    set_instructor_for_day(frm, cdt, cdn, 'thursday')
  },
  friday(frm, cdt, cdn) {
    set_instructor_for_day(frm, cdt, cdn, 'friday')
  },
  saturday(frm, cdt, cdn) {
    set_instructor_for_day(frm, cdt, cdn, 'saturday')
  },
  sunday(frm, cdt, cdn) {
    set_instructor_for_day(frm, cdt, cdn, 'sunday')
  },
})

function set_instructor_for_day(frm, cdt, cdn, day) {
  const row = locals[cdt][cdn]
  const course = row[day]
  const instructor_field = day + '_instructor'

  if (!course) {
    frappe.model.set_value(cdt, cdn, instructor_field, '')
    return
  }

  frm
    .call('get_instructor_for_subject', { course: course })
    .then((r) => {
      if (r && r.message) {
        frappe.model.set_value(cdt, cdn, instructor_field, r.message)
      } else {
        frappe.model.set_value(cdt, cdn, instructor_field, '')
        frappe.show_alert({
          message: __(
            'No instructor found for {0} in Student Group {1}. Check the Instructor-Subject assignments.',
            [course, frm.doc.student_group]
          ),
          indicator: 'orange',
        })
      }
    })
}
