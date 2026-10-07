// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student User Creation Tool', {
  setup(frm) {
    frm.set_query('student_group', () => ({
      filters: frm.doc.academic_year ? { academic_year: frm.doc.academic_year } : {},
    }))
  },

  refresh(frm) {
    frm.disable_save()
    ;['get_students', 'create_users'].forEach((f) => frm.fields_dict[f].$input.addClass('btn-primary'))
    render_summary(frm)
    render_last_run(frm)

    frm.add_custom_button(__('Tick All'), () => tick(frm, 1), __('Select'))
    frm.add_custom_button(__('Untick All'), () => tick(frm, 0), __('Select'))
    frm.add_custom_button(
      __('Tick Only Students Without a Login'),
      () => {
        ;(frm.doc.students || []).forEach((r) => (r.include = r.state === __('No login') ? 1 : 0))
        frm.refresh_field('students')
        render_summary(frm)
      },
      __('Select')
    )

    if (!frm._sucd_realtime) {
      frm._sucd_realtime = true
      frappe.realtime.on('student_user_creation_tool', (data) => {
        frappe.show_progress(__('Creating logins'), data.progress[0], data.progress[1])
      })
      frappe.realtime.on('student_user_creation_tool_done', (log) => {
        frappe.hide_progress()
        frm.doc.last_run_log = JSON.stringify(log)
        if (log.credentials_file) frm.doc.credentials_file = log.credentials_file
        frm.refresh_field('credentials_file')
        render_last_run(frm)
        frappe.msgprint({
          title: __('Logins created'),
          message: describe(log),
          indicator: (log.failed || []).length ? 'orange' : 'green',
        })
      })
    }
  },

  get_students(frm) {
    frm.clear_table('students')
    frm.call({
      method: 'get_students',
      doc: frm.doc,
      freeze: true,
      callback(r) {
        frm.set_value('students', r.message || [])
        render_summary(frm)
      },
    })
  },

  create_users(frm) {
    const ticked = (frm.doc.students || []).filter((r) => r.include)
    if (!ticked.length) {
      frappe.msgprint(__('Tick at least one student.'))
      return
    }
    let message = __('Create or repair logins for {0} student(s)?', [ticked.length])
    if (frm.doc.set_password) {
      message += '<br><br>' + __('Initial password: the family phone number, e.g. 0912345678 (or 251912345678 if the password policy rejects the first).')
    }
    if (frm.doc.overwrite_password) {
      message += '<br><br><b class="text-danger">' + __('Existing passwords of the ticked students will be replaced.') + '</b>'
    }
    frappe.confirm(message, () => {
      frm.call({
        method: 'create_users',
        doc: frm.doc,
        freeze: true,
        callback(r) {
          if (r.message) {
            frappe.show_alert({ message: __('{0} student(s) queued.', [r.message.queued]), indicator: 'blue' })
          }
        },
      })
    })
  },
})

frappe.ui.form.on('Student User Creation Tool Student', {
  include: (frm) => render_summary(frm),
})

function tick(frm, value) {
  ;(frm.doc.students || []).forEach((r) => (r.include = value))
  frm.refresh_field('students')
  render_summary(frm)
}

function render_summary(frm) {
  const rows = frm.doc.students || []
  const wrapper = frm.get_field('summary').$wrapper
  if (!rows.length) {
    wrapper.html(
      `<p class="text-muted">${__(
        'Enrollment does not create logins. Pick the students here (for example one academic year, program or section), load them, and create their logins in one go.'
      )}</p>`
    )
    return
  }
  const states = {}
  rows.forEach((r) => (states[r.state] = (states[r.state] || 0) + 1))
  const ticked = rows.filter((r) => r.include).length
  const no_phone = rows.filter((r) => r.include && (r.password_from || '').startsWith('(')).length
  let html = `<p>${__('Ticked')}: <b>${ticked}</b> / ${rows.length} · ${Object.keys(states)
    .map((s) => `${frappe.utils.escape_html(s)}: ${states[s]}`)
    .join(' · ')}</p>`
  if (no_phone && frm.doc.set_password) {
    html += `<p class="text-warning">${__('{0} ticked student(s) have no usable phone number; their login is created without a password.', [no_phone])}</p>`
  }
  wrapper.html(html)
}

function render_last_run(frm) {
  const wrapper = frm.get_field('last_run').$wrapper
  if (!frm.doc.last_run_log) {
    wrapper.html(`<p class="text-muted">${__('No logins have been created with this tool yet.')}</p>`)
    return
  }
  try {
    wrapper.html(describe(JSON.parse(frm.doc.last_run_log), true))
  } catch (e) {
    wrapper.html('')
  }
}

function describe(log, detailed) {
  const esc = frappe.utils.escape_html
  let html = `<p>${__('Created')}: <b>${log.created || 0}</b> · ${__('Linked to existing')}: <b>${
    log.linked || 0
  }</b> · ${__('Already set up')}: <b>${log.unchanged || 0}</b> · ${__('Passwords set')}: <b>${
    log.passwords || 0
  }</b> · ${__('Failed')}: <b>${(log.failed || []).length}</b></p>`
  if (log.credentials_file) {
    html += `<p><a href="${esc(log.credentials_file)}" target="_blank">${__('Download the logins and initial passwords (CSV)')}</a></p>`
  }
  const list = (title, items, key) => {
    if (!items || !items.length) return ''
    const shown = detailed ? items : items.slice(0, 15)
    return (
      `<p><b>${title}</b></p><ul class="small">` +
      shown.map((i) => `<li>${esc(i.row || '')} ${esc(i.name || '')}: ${esc(i[key] || '')}</li>`).join('') +
      '</ul>'
    )
  }
  html += list(__('Failed'), log.failed, 'error')
  html += list(__('Notes'), log.notes, 'note')
  return html
}
