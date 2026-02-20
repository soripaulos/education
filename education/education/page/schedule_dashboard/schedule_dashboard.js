frappe.pages['schedule-dashboard'].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __('Schedule Dashboard'),
    single_column: true,
  })

  wrapper.schedule_dashboard = new ScheduleDashboard(page, wrapper)
}

frappe.pages['schedule-dashboard'].on_page_show = function (wrapper) {
  if (wrapper.schedule_dashboard) {
    wrapper.schedule_dashboard.on_show()
  }
}

// ─── helpers ───────────────────────────────────────────────────────────────

function fmt12(time_str) {
  if (!time_str) return ''
  const parts = String(time_str).split(':')
  let h = parseInt(parts[0], 10)
  const m = parts[1] || '00'
  const ampm = h >= 12 ? 'PM' : 'AM'
  if (h === 0) h = 12
  else if (h > 12) h -= 12
  return `${h}:${m} ${ampm}`
}

const COLOR_BG = {
  blue: '#EDF6FD',
  green: '#E4F5E9',
  red: '#FFF0F0',
  orange: '#FFF1E7',
  yellow: '#FFF7D3',
  teal: '#E6F7F4',
  violet: '#F5F2FF',
  cyan: '#E0F8FF',
  amber: '#FCF3CF',
  pink: '#FEEEF8',
  purple: '#F9F0FF',
}

// ─── Page class ────────────────────────────────────────────────────────────

class ScheduleDashboard {
  constructor(page, wrapper) {
    this.page = page
    this.wrapper = wrapper
    this._setup_fields()
    this._setup_body()
    this._toggle_fields()
    this._show_prompt()
  }

  // ── setup ──────────────────────────────────────────────────────────────

  _setup_fields() {
    // All fields are added without hidden:1 so they exist in the DOM.
    // Visibility is controlled manually via _toggle_fields().

    this.f_view = this.page.add_field({
      label: __('View'),
      fieldtype: 'Select',
      fieldname: 'view',
      default: 'student_group_now',
      options: [
        { label: __('Who is Teaching Now (Student Group)'), value: 'student_group_now' },
        { label: __('Instructor Daily Schedule'), value: 'instructor_daily' },
        { label: __('Student Group Timetable'), value: 'student_group_timetable' },
      ],
      change: () => {
        this.f_instructor.set_value('')
        this._toggle_fields()
        this._show_prompt()
      },
    })

    this.f_student_group = this.page.add_field({
      label: __('Student Group'),
      fieldtype: 'Link',
      fieldname: 'student_group',
      options: 'Student Group',
      change: () => this.load(),
    })

    this.f_instructor = this.page.add_field({
      label: __('Instructor'),
      fieldtype: 'Link',
      fieldname: 'instructor',
      options: 'Instructor',
      get_query: () => {
        const date = this.f_date ? this.f_date.get_value() : frappe.datetime.get_today()
        return {
          query:
            'education.education.page.schedule_dashboard.schedule_dashboard.get_instructors_query',
          filters: { date: date || frappe.datetime.get_today() },
        }
      },
      change: () => this.load(),
    })

    this.f_date = this.page.add_field({
      label: __('Date'),
      fieldtype: 'Date',
      fieldname: 'date',
      default: frappe.datetime.get_today(),
      change: () => {
        // Clear instructor so user re-picks from the updated filtered list
        if (this._view() === 'instructor_daily') {
          this.f_instructor.set_value('')
          this._show_prompt()
        } else {
          this.load()
        }
      },
    })
  }

  _setup_body() {
    this.$body = $('<div class="sd-results" style="padding:20px 15px;min-height:200px;"></div>')
    // Use wrapper directly — guaranteed to contain .layout-main-section
    $(this.wrapper).find('.layout-main-section').append(this.$body)
  }

  // ── visibility ─────────────────────────────────────────────────────────

  _view() {
    return this.f_view.get_value() || 'student_group_now'
  }

  _toggle_fields() {
    const v = this._view()
    this.f_student_group.$wrapper.toggle(v !== 'instructor_daily')
    this.f_instructor.$wrapper.toggle(v === 'instructor_daily')
    this.f_date.$wrapper.toggle(v !== 'student_group_now')
  }

  // ── public ─────────────────────────────────────────────────────────────

  on_show() {
    // Refresh data when navigating back to this page
    this.load()
  }

  load() {
    const v = this._view()
    if (v === 'student_group_now') this._load_sg_now()
    else if (v === 'instructor_daily') this._load_instructor_daily()
    else if (v === 'student_group_timetable') this._load_sg_timetable()
  }

  // ── helpers ────────────────────────────────────────────────────────────

  _show_prompt() {
    const v = this._view()
    if (v === 'student_group_now') {
      this.$body.html(
        `<p class="text-muted" style="margin-top:20px;">${__('Select a Student Group to see who is teaching right now.')}</p>`
      )
    } else if (v === 'instructor_daily') {
      this.$body.html(
        `<p class="text-muted" style="margin-top:20px;">${__('Select a date then choose an Instructor to see their daily schedule.')}</p>`
      )
    } else {
      this.$body.html(
        `<p class="text-muted" style="margin-top:20px;">${__('Select a Student Group to see the timetable.')}</p>`
      )
    }
  }

  _loading() {
    this.$body.html(
      `<div style="padding:30px;text-align:center;">
        <div class="text-muted">${frappe.utils.icon('loading', 'lg')} ${__('Loading...')}</div>
      </div>`
    )
  }

  _empty(msg) {
    this.$body.html(
      `<div style="padding:40px;text-align:center;">
        <p class="text-muted">${msg}</p>
      </div>`
    )
  }

  // ── view loaders ───────────────────────────────────────────────────────

  _load_sg_now() {
    const sg = this.f_student_group.get_value()
    if (!sg) {
      this._show_prompt()
      return
    }

    this._loading()

    frappe.call({
      method:
        'education.education.page.schedule_dashboard.schedule_dashboard.get_student_group_current_instructor',
      args: { student_group: sg },
      callback: (r) => {
        const data = r.message || []
        if (!data.length) {
          this._empty(
            `${__('No class is currently in session for')} <strong>${frappe.utils.escape_html(sg)}</strong>`
          )
          return
        }

        let html = `<h5 style="margin-bottom:16px;">${__('Currently in session')} — <strong>${frappe.utils.escape_html(sg)}</strong></h5><div class="row">`

        for (const s of data) {
          html += `
            <div class="col-sm-6 col-md-4" style="margin-bottom:14px;">
              <div style="background:${COLOR_BG[s.class_schedule_color] || '#fff'};border-left:4px solid var(--primary);padding:14px 16px;border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,.06);">
                <h5 style="margin:0 0 8px;">${frappe.utils.escape_html(s.course)}</h5>
                <p style="margin:0 0 4px;"><strong>${__('Instructor')}:</strong> ${frappe.utils.escape_html(s.instructor_name || s.instructor)}</p>
                <p style="margin:0 0 4px;"><strong>${__('Time')}:</strong> ${fmt12(s.from_time)} – ${fmt12(s.to_time)}</p>
                <p style="margin:0;"><strong>${__('Room')}:</strong> ${frappe.utils.escape_html(s.room || '—')}</p>
              </div>
            </div>`
        }

        html += '</div>'
        this.$body.html(html)
      },
      error: () => {
        this._empty(__('Error loading schedule. Please try again.'))
      },
    })
  }

  _load_instructor_daily() {
    const instructor = this.f_instructor.get_value()
    const date = this.f_date.get_value() || frappe.datetime.get_today()

    if (!instructor) {
      this._show_prompt()
      return
    }

    this._loading()

    frappe.call({
      method:
        'education.education.page.schedule_dashboard.schedule_dashboard.get_instructor_daily_schedule',
      args: { instructor, date },
      callback: (r) => {
        const data = r.message || []
        const display_date = frappe.datetime.str_to_user(date)

        if (!data.length) {
          this._empty(
            `${__('No classes scheduled for')} <strong>${frappe.utils.escape_html(data[0] ? data[0].instructor_name : instructor)}</strong> ${__('on')} ${display_date}`
          )
          return
        }

        const name_display = frappe.utils.escape_html(data[0].instructor_name || instructor)

        let html = `
          <h5 style="margin-bottom:14px;">${__('Schedule for')} <strong>${name_display}</strong> — ${display_date}</h5>
          <table class="table table-bordered" style="font-size:13px;">
            <thead class="grid-heading-row">
              <tr>
                <th>${__('Time')}</th>
                <th>${__('Subject')}</th>
                <th>${__('Student Group')}</th>
                <th>${__('Room')}</th>
                <th>${__('Status')}</th>
              </tr>
            </thead>
            <tbody>`

        for (const s of data) {
          const row_style = s.is_ongoing ? 'background:#d9f5e4;font-weight:600;' : ''
          const badge = s.is_ongoing
            ? `<span class="indicator-pill green nowrap">${__('Ongoing')}</span>`
            : ''

          html += `
            <tr style="${row_style}">
              <td class="nowrap">${fmt12(s.from_time)} – ${fmt12(s.to_time)}</td>
              <td><a href="/app/course-schedule/${s.name}">${frappe.utils.escape_html(s.course)}</a></td>
              <td><a href="/app/student-group/${encodeURIComponent(s.student_group)}">${frappe.utils.escape_html(s.student_group)}</a></td>
              <td>${frappe.utils.escape_html(s.room || '—')}</td>
              <td>${badge}</td>
            </tr>`
        }

        html += '</tbody></table>'
        this.$body.html(html)
      },
      error: () => {
        this._empty(__('Error loading schedule. Please try again.'))
      },
    })
  }

  _load_sg_timetable() {
    const sg = this.f_student_group.get_value()
    const date = this.f_date.get_value() || frappe.datetime.get_today()

    if (!sg) {
      this._show_prompt()
      return
    }

    this._loading()

    frappe.call({
      method:
        'education.education.page.schedule_dashboard.schedule_dashboard.get_student_group_timetable',
      args: { student_group: sg, date },
      callback: (r) => {
        const result = r.message || {}
        const periods = result.periods || []
        const display_date = frappe.datetime.str_to_user(date)

        if (!periods.length) {
          const prog = frappe.utils.escape_html(result.program || '')
          this._empty(
            `${__('No Period Time Blocks found for program')} <strong>${prog}</strong>. ${__('Create Period Time Block records for this program first.')}`
          )
          return
        }

        let html = `
          <h5 style="margin-bottom:14px;">${__('Timetable for')} <strong>${frappe.utils.escape_html(sg)}</strong> — ${display_date}</h5>
          <table class="table table-bordered" style="font-size:13px;">
            <thead class="grid-heading-row">
              <tr>
                <th style="width:130px;">${__('Period')}</th>
                <th style="width:155px;">${__('Time')}</th>
                <th>${__('Subject')}</th>
                <th>${__('Instructor')}</th>
                <th>${__('Room')}</th>
              </tr>
            </thead>
            <tbody>`

        for (const p of periods) {
          const row_style = p.is_ongoing ? 'background:#d9f5e4;font-weight:600;' : ''
          const badge = p.is_ongoing
            ? ` <span class="indicator-pill green nowrap">${__('Now')}</span>`
            : ''

          const label = frappe.utils.escape_html(
            p.period_label || `${__('Period')} ${p.period_number}`
          )

          const subject_cell = p.schedule_name
            ? `<a href="/app/course-schedule/${p.schedule_name}">${frappe.utils.escape_html(p.course)}</a>`
            : `<span class="text-muted">—</span>`

          const instructor_cell = p.instructor
            ? `<a href="/app/instructor/${encodeURIComponent(p.instructor)}">${frappe.utils.escape_html(p.instructor_name || p.instructor)}</a>`
            : `<span class="text-muted">—</span>`

          html += `
            <tr style="${row_style}">
              <td>${label}${badge}</td>
              <td class="nowrap">${fmt12(p.from_time)} – ${fmt12(p.to_time)}</td>
              <td>${subject_cell}</td>
              <td>${instructor_cell}</td>
              <td>${frappe.utils.escape_html(p.room || '—')}</td>
            </tr>`
        }

        html += '</tbody></table>'
        this.$body.html(html)
      },
      error: () => {
        this._empty(__('Error loading timetable. Please try again.'))
      },
    })
  }
}
