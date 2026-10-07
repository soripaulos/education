// Copyright (c) 2016, Frappe and contributors
// For license information, please see license.txt

const PET_STATUS_COLORS = {
  Ready: 'green',
  Review: 'orange',
  Blocked: 'red',
  'Already Enrolled': 'blue',
  'Not Returning': 'grey',
  Graduating: 'purple',
}

frappe.ui.form.on('Program Enrollment Tool', {
  setup(frm) {
    frm.set_query('academic_year', () => ({ order_by: 'year_start_date desc' }))
    frm.set_query('new_academic_year', () => ({ order_by: 'year_start_date desc' }))
  },

  onload(frm) {
    const defaults = (frm.doc.__onload || {}).defaults || {}
    if (!frm.doc.new_academic_year && defaults.new_academic_year) {
      frm.set_value('new_academic_year', defaults.new_academic_year)
    }
    if (!frm.doc.academic_year && defaults.academic_year) {
      frm.set_value('academic_year', defaults.academic_year)
    }
  },

  refresh(frm) {
    frm.disable_save()
    ;['get_students', 'enroll_students', 'sync_groups'].forEach((f) =>
      frm.fields_dict[f].$input.addClass('btn-primary')
    )
    render_groups_help(frm)
    render_last_run(frm)
    render_summary(frm)
    add_bulk_buttons(frm)

    if (!frm._pet_realtime) {
      frm._pet_realtime = true
      frappe.realtime.on('program_enrollment_tool', (data) => {
        frappe.show_progress(data.title || __('Working'), data.progress[0], data.progress[1])
      })
      frappe.realtime.on('program_enrollment_tool_done', (log) => {
        frappe.hide_progress()
        frm.doc.last_run_log = JSON.stringify(log)
        render_last_run(frm)
        frappe.msgprint({
          title: __('Finished'),
          message: describe_log(log) + '<p>' + __('Click Load Students to see the updated rows.') + '</p>',
          indicator: (log.failed || []).length ? 'orange' : 'green',
        })
      })
    }
  },

  new_academic_year(frm) {
    if (frm.doc.new_academic_year && !frm.doc.enrollment_date) {
      frappe.db
        .get_value('Academic Year', frm.doc.new_academic_year, 'year_start_date')
        .then((r) => r.message && frm.set_value('enrollment_date', r.message.year_start_date))
    }
  },

  get_students(frm) {
    frm.clear_table('students')
    frm.refresh_field('students')
    frm._pet_summary = null
    frm.call({
      method: 'get_students',
      doc: frm.doc,
      freeze: true,
      freeze_message: __('Checking applications, enrollments and sections...'),
      callback(r) {
        if (!r.message) return
        frm._pet_summary = r.message.summary
        frm.set_value('students', r.message.rows)
        render_summary(frm)
      },
    })
  },

  enroll_students(frm) {
    const rows = frm.doc.students || []
    const enroll = rows.filter((r) => r.action === 'Enroll')
    const exits = rows.filter((r) => r.action === 'Record Exit')
    const review = enroll.filter((r) => r.status === 'Review').length
    const blocked = enroll.filter((r) => r.status === 'Blocked').length
    if (!enroll.length && !exits.length) {
      frappe.msgprint(__('No rows are set to Enroll or Record Exit.'))
      return
    }
    let message = `<p>${__('Enroll {0} student(s) into {1}.', [enroll.length, frm.doc.new_academic_year])}</p>`
    if (exits.length) {
      message += `<p>${__('Record {0} exit(s): these students are marked as having left and their records are disabled.', [exits.length])}</p>`
    }
    if (review) message += `<p>${__('{0} of the enrollments are Review rows you chose to enroll.', [review])}</p>`
    if (blocked) message += `<p class="text-danger">${__('{0} Blocked row(s) will be skipped.', [blocked])}</p>`
    message += `<p class="text-muted">${__('No logins are created. Use the Student User Creation Tool afterwards.')}</p>`
    frappe.confirm(message, () => {
      frm.call({
        method: 'enroll_students',
        doc: frm.doc,
        freeze: true,
        callback(r) {
          if (r.message) {
            frappe.show_alert({
              message: __('{0} row(s) queued. Progress will appear here.', [r.message.queued]),
              indicator: 'blue',
            })
          }
        },
      })
    })
  },

  sync_groups(frm) {
    frappe.confirm(
      __(
        'Every section named on a {0} enrollment will be moved to {0} and its members replaced by the students enrolled into it. ' +
          'Each student\'s {1} section is first saved on their {1} enrollment, so last year\'s reports stay correct. Continue?',
        [frm.doc.new_academic_year, frm.doc.academic_year]
      ),
      () => {
        frm.call({
          method: 'sync_groups',
          doc: frm.doc,
          freeze: true,
          callback() {
            frappe.show_alert({ message: __('Section rollover started.'), indicator: 'blue' })
          },
        })
      }
    )
  },
})

function add_bulk_buttons(frm) {
  const set_action = (predicate, action) => {
    let changed = 0
    ;(frm.doc.students || []).forEach((row) => {
      if (predicate(row) && row.action !== action) {
        row.action = action
        changed++
      }
    })
    frm.refresh_field('students')
    render_summary(frm)
    frappe.show_alert(__('{0} row(s) set to {1}', [changed, __(action)]))
  }
  const group = __('Set Actions')
  frm.add_custom_button(__('Enroll all Ready'), () => set_action((r) => r.status === 'Ready', 'Enroll'), group)
  frm.add_custom_button(
    __('Enroll all Review rows'),
    () =>
      frappe.confirm(__('Enroll every Review row? Check their issues first.'), () =>
        set_action((r) => r.status === 'Review', 'Enroll')
      ),
    group
  )
  frm.add_custom_button(
    __('Record Exit for Graduating'),
    () => set_action((r) => r.status === 'Graduating', 'Record Exit'),
    group
  )
  frm.add_custom_button(
    __('Record Exit for Not Returning'),
    () =>
      frappe.confirm(
        __('Mark every Not Returning row as having left? Only do this once registration for the new year has closed.'),
        () => set_action((r) => r.status === 'Not Returning', 'Record Exit')
      ),
    group
  )
  frm.add_custom_button(__('Skip All'), () => set_action(() => true, 'Skip'), group)
  frm.add_custom_button(
    __('Enrollment Diagnostics'),
    () =>
      frappe.set_route('query-report', 'Enrollment Diagnostics', {
        academic_year: frm.doc.new_academic_year,
        previous_academic_year: frm.doc.academic_year,
      }),
    __('Reports')
  )
  frm.add_custom_button(
    __('Enrollment Statistics'),
    () =>
      frappe.set_route('query-report', 'Enrollment Statistics', {
        academic_year: frm.doc.new_academic_year,
        previous_academic_year: frm.doc.academic_year,
      }),
    __('Reports')
  )
  frm.add_custom_button(
    __('Student User Creation Tool'),
    () => frappe.set_route('Form', 'Student User Creation Tool'),
    __('Reports')
  )
}

function render_summary(frm) {
  const wrapper = frm.get_field('summary').$wrapper
  const rows = frm.doc.students || []
  if (!rows.length) {
    wrapper.html(
      `<p class="text-muted">${__(
        'Choose the years, optionally upload the section roster, then click Load Students. ' +
          'Each row shows where the student is going and anything that needs attention.'
      )}</p>`
    )
    return
  }
  const counts = {}
  const actions = {}
  rows.forEach((r) => {
    counts[r.status] = (counts[r.status] || 0) + 1
    actions[r.action] = (actions[r.action] || 0) + 1
  })
  const chips = Object.keys(PET_STATUS_COLORS)
    .filter((s) => counts[s])
    .map(
      (s) =>
        `<span class="indicator-pill ${PET_STATUS_COLORS[s]}" style="margin: 0 6px 6px 0">${__(s)}: ${counts[s]}</span>`
    )
    .join('')
  const summary = frm._pet_summary || {}
  let html = `<div style="margin-bottom: 8px">${chips}</div>`
  html += `<p>${__('Actions')}: ${__('Enroll')} <b>${actions.Enroll || 0}</b> · ${__('Record Exit')} <b>${
    actions['Record Exit'] || 0
  }</b> · ${__('Skip')} <b>${actions.Skip || 0}</b></p>`
  const hidden = (summary.counts || {})['Already Enrolled']
  if (hidden && !frm.doc.include_already_enrolled) {
    html += `<p class="text-muted">${__('{0} already-enrolled student(s) are not listed.', [hidden])}</p>`
  }
  if (summary.unpaid_ready) {
    html += `<p class="text-muted">${__('{0} Ready student(s) are not marked Paid on their application.', [
      summary.unpaid_ready,
    ])}</p>`
  }
  if (summary.roster) {
    const roster = summary.roster
    html += `<p>${__('Roster')}: ${__('{0} students read', [roster.students])}`
    if (roster.conflicts) html += ` · <span class="text-danger">${__('{0} listed in two sections', [roster.conflicts])}</span>`
    if (roster.without_application) {
      html += ` · <span class="text-warning">${__('{0} on the roster have no application this year', [
        roster.without_application,
      ])}</span>`
    }
    html += '</p>'
    if ((roster.without_application_sample || []).length) {
      html += `<details><summary>${__('Roster students without an application')}</summary><div class="small">${roster.without_application_sample
        .map((s) => frappe.utils.escape_html(s))
        .join('<br>')}</div></details>`
    }
  }
  html += `<p class="text-muted small">${__(
    'Ready rows are set to Enroll. Review rows need a decision: open the row, read its issues, and set it to Enroll if it is right. ' +
      'Blocked rows must be fixed on the application (or the Not Promoted list) and reloaded.'
  )}</p>`
  wrapper.html(html)
}

function render_groups_help(frm) {
  frm.get_field('groups_help').$wrapper.html(
    `<p class="text-muted small">${__(
      'After enrolling, roll the sections over: each section used in the new year is moved onto it and filled with the students enrolled into it, in alphabetical order. ' +
        'Last year\'s membership is saved on last year\'s enrollments first. Homeroom teachers and instructors are kept; change them on the section if they move.'
    )}</p>`
  )
}

function render_last_run(frm) {
  const wrapper = frm.get_field('last_run').$wrapper
  if (!frm.doc.last_run_log) {
    wrapper.html(`<p class="text-muted">${__('Nothing has been processed yet.')}</p>`)
    return
  }
  let log = {}
  try {
    log = JSON.parse(frm.doc.last_run_log)
  } catch (e) {
    return
  }
  wrapper.html(describe_log(log, true))
}

function describe_log(log, detailed) {
  const esc = frappe.utils.escape_html
  let html = ''
  if (log.kind === 'groups') {
    html += `<p>${__('Sections rolled over: {0}; refreshed: {1}; enrollments given their {2} section: {3}; old memberships made inactive: {4}.', [
      (log.rolled_over || []).length,
      (log.synced || []).length,
      log.previous_year || '',
      log.archived || 0,
      log.deactivated || 0,
    ])}</p>`
    const lists = [
      [__('Program changed'), log.program_changed],
      [__('Mixed programs'), log.mixed_programs],
      [__('Not used this year'), log.unused],
      [__('Disabled'), log.disabled],
      [__('Skipped (serve a later year)'), log.skipped],
    ]
    lists.forEach(([label, items]) => {
      if (items && items.length) html += `<p><b>${label}</b>: ${items.map(esc).join(', ')}</p>`
    })
  } else if (log.kind === 'process') {
    html += `<p>${__('Enrolled')}: <b>${log.enrolled || 0}</b> (${__('{0} new Student records', [
      log.new_students || 0,
    ])}, ${__('{0} readmitted', [log.readmitted || 0])}) · ${__('Exits recorded')}: <b>${log.exits || 0}</b> · ${__(
      'Skipped'
    )}: <b>${(log.skipped || []).length}</b> · ${__('Failed')}: <b>${(log.failed || []).length}</b></p>`
    if ((log.sections_created || []).length) {
      html += `<p>${__('Sections created')}: ${log.sections_created.map(esc).join(', ')}</p>`
    }
  }
  const table = (title, items, key) => {
    if (!items || !items.length) return ''
    const shown = detailed ? items : items.slice(0, 15)
    let out = `<p><b>${title}</b></p><table class="table table-bordered table-condensed small"><tbody>`
    shown.forEach((i) => {
      out += `<tr><td>${esc(i.row || '')}</td><td>${esc(i.name || '')}</td><td>${esc(i[key] || '')}</td></tr>`
    })
    out += '</tbody></table>'
    if (shown.length < items.length) out += `<p class="text-muted">${__('...and {0} more', [items.length - shown.length])}</p>`
    return out
  }
  html += table(__('Failed'), log.failed, 'error')
  html += table(__('Skipped'), log.skipped, 'reason')
  html += table(__('Notes'), log.notes, 'note')
  if (log.finished_on) html += `<p class="text-muted small">${__('Finished')} ${frappe.datetime.str_to_user(log.finished_on)}</p>`
  return html
}

frappe.ui.form.on('Program Enrollment Tool Student', {
  action(frm, cdt, cdn) {
    const row = locals[cdt][cdn]
    if (row.action === 'Enroll' && ['Blocked', 'Already Enrolled', 'Not Returning', 'Graduating'].includes(row.status)) {
      frappe.show_alert({ message: __('{0} rows cannot be enrolled.', [__(row.status)]), indicator: 'red' })
      frappe.model.set_value(cdt, cdn, 'action', 'Skip')
    }
    if (row.action === 'Record Exit' && !['Not Returning', 'Graduating'].includes(row.status)) {
      frappe.show_alert({ message: __('Only students who are not returning can be exited here.'), indicator: 'red' })
      frappe.model.set_value(cdt, cdn, 'action', 'Skip')
    }
    render_summary(frm)
  },
})
