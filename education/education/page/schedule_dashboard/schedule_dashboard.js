frappe.pages['schedule-dashboard'].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __('Schedule Dashboard'),
    single_column: true,
  })
  wrapper.schedule_dashboard = new ScheduleDashboard(page)
}

frappe.pages['schedule-dashboard'].on_page_show = function (wrapper) {
  if (wrapper.schedule_dashboard) {
    wrapper.schedule_dashboard.refresh()
  }
}

class ScheduleDashboard {
  constructor(page) {
    this.page = page
    this.view = 'student_group_now'
    this.setup_controls()
    this.make_body()
  }

  setup_controls() {
    this.page.clear_fields()

    this.view_field = this.page.add_field({
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
        this.view = this.view_field.get_value()
        this.toggle_controls()
        this.clear_results()
      },
    })

    this.student_group_field = this.page.add_field({
      label: __('Student Group'),
      fieldtype: 'Link',
      fieldname: 'student_group',
      options: 'Student Group',
      change: () => this.refresh(),
    })

    this.instructor_field = this.page.add_field({
      label: __('Instructor'),
      fieldtype: 'Link',
      fieldname: 'instructor',
      options: 'Instructor',
      hidden: 1,
      change: () => this.refresh(),
    })

    this.date_field = this.page.add_field({
      label: __('Date'),
      fieldtype: 'Date',
      fieldname: 'date',
      default: frappe.datetime.get_today(),
      change: () => this.refresh(),
    })

    this.toggle_controls()
  }

  toggle_controls() {
    const v = this.view

    if (v === 'student_group_now') {
      this.show_field('student_group')
      this.hide_field('instructor')
      this.hide_field('date')
    } else if (v === 'instructor_daily') {
      this.hide_field('student_group')
      this.show_field('instructor')
      this.show_field('date')
    } else if (v === 'student_group_timetable') {
      this.show_field('student_group')
      this.hide_field('instructor')
      this.show_field('date')
    }
  }

  show_field(name) {
    const $el = this.page.fields_dict[name]
    if ($el) $el.$wrapper.show()
  }

  hide_field(name) {
    const $el = this.page.fields_dict[name]
    if ($el) $el.$wrapper.hide()
  }

  make_body() {
    this.$body = $('<div class="schedule-dashboard-results" style="padding: 15px;"></div>')
    $(this.page.body).find('.layout-main-section').append(this.$body)
  }

  clear_results() {
    this.$body.html('')
  }

  refresh() {
    const v = this.view
    if (v === 'student_group_now') {
      this.load_student_group_now()
    } else if (v === 'instructor_daily') {
      this.load_instructor_daily()
    } else if (v === 'student_group_timetable') {
      this.load_student_group_timetable()
    }
  }

  format_time_12hr(time_str) {
    if (!time_str) return ''
    const parts = String(time_str).split(':')
    let h = parseInt(parts[0], 10)
    const m = parts[1] || '00'
    const ampm = h >= 12 ? 'PM' : 'AM'
    if (h === 0) h = 12
    else if (h > 12) h -= 12
    return `${h}:${m} ${ampm}`
  }

  color_bg(color) {
    const map = {
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
    return map[color] || '#FFFFFF'
  }

  load_student_group_now() {
    const sg = this.page.fields_dict.student_group.get_value()
    if (!sg) {
      this.$body.html(`<p class="text-muted">${__('Select a Student Group to see who is teaching now.')}</p>`)
      return
    }

    frappe.call({
      method: 'education.education.page.schedule_dashboard.schedule_dashboard.get_student_group_current_instructor',
      args: { student_group: sg },
      callback: (r) => {
        const data = r.message || []
        if (!data.length) {
          this.$body.html(`
            <div class="text-center" style="padding:40px;">
              <h4 class="text-muted">${__('No class is currently in session for')} <strong>${sg}</strong></h4>
            </div>
          `)
          return
        }

        let html = `
          <h5 style="margin-bottom:15px;">${__('Currently Teaching')} — <strong>${sg}</strong></h5>
          <div class="row">
        `
        for (const s of data) {
          html += `
            <div class="col-sm-6 col-md-4" style="margin-bottom:15px;">
              <div class="card" style="background:${this.color_bg(s.class_schedule_color)};border-left:4px solid var(--primary);padding:15px;border-radius:8px;">
                <h5 style="margin:0 0 8px;">${s.course}</h5>
                <p style="margin:0 0 4px;"><strong>${__('Instructor')}:</strong> ${s.instructor_name || s.instructor}</p>
                <p style="margin:0 0 4px;"><strong>${__('Time')}:</strong> ${this.format_time_12hr(s.from_time)} – ${this.format_time_12hr(s.to_time)}</p>
                <p style="margin:0;"><strong>${__('Room')}:</strong> ${s.room || '—'}</p>
              </div>
            </div>
          `
        }
        html += '</div>'
        this.$body.html(html)
      },
    })
  }

  load_instructor_daily() {
    const instructor = this.page.fields_dict.instructor.get_value()
    const date = this.page.fields_dict.date.get_value()
    if (!instructor) {
      this.$body.html(`<p class="text-muted">${__('Select an Instructor to see their daily schedule.')}</p>`)
      return
    }

    frappe.call({
      method: 'education.education.page.schedule_dashboard.schedule_dashboard.get_instructor_daily_schedule',
      args: { instructor: instructor, date: date },
      callback: (r) => {
        const data = r.message || []
        const display_date = frappe.datetime.str_to_user(date)

        if (!data.length) {
          this.$body.html(`
            <div class="text-center" style="padding:40px;">
              <h4 class="text-muted">${__('No classes scheduled for this instructor on')} ${display_date}</h4>
            </div>
          `)
          return
        }

        let html = `
          <h5 style="margin-bottom:15px;">${__('Schedule for')} <strong>${data[0].instructor_name || instructor}</strong> — ${display_date}</h5>
          <table class="table table-bordered">
            <thead>
              <tr>
                <th>${__('Time')}</th>
                <th>${__('Subject')}</th>
                <th>${__('Student Group')}</th>
                <th>${__('Room')}</th>
                <th>${__('Status')}</th>
              </tr>
            </thead>
            <tbody>
        `
        for (const s of data) {
          const bg = s.is_ongoing ? 'background:#E4F5E9;font-weight:600;' : ''
          const status = s.is_ongoing
            ? `<span class="indicator-pill green">${__('Ongoing')}</span>`
            : ''
          html += `
              <tr style="${bg}">
                <td>${this.format_time_12hr(s.from_time)} – ${this.format_time_12hr(s.to_time)}</td>
                <td><a href="/app/course-schedule/${s.name}">${s.course}</a></td>
                <td><a href="/app/student-group/${s.student_group}">${s.student_group}</a></td>
                <td>${s.room || '—'}</td>
                <td>${status}</td>
              </tr>
          `
        }
        html += '</tbody></table>'
        this.$body.html(html)
      },
    })
  }

  load_student_group_timetable() {
    const sg = this.page.fields_dict.student_group.get_value()
    const date = this.page.fields_dict.date.get_value()
    if (!sg) {
      this.$body.html(`<p class="text-muted">${__('Select a Student Group to see the timetable.')}</p>`)
      return
    }

    frappe.call({
      method: 'education.education.page.schedule_dashboard.schedule_dashboard.get_student_group_timetable',
      args: { student_group: sg, date: date },
      callback: (r) => {
        const result = r.message || {}
        const periods = result.periods || []
        const display_date = frappe.datetime.str_to_user(date)

        if (!periods.length) {
          this.$body.html(`
            <div class="text-center" style="padding:40px;">
              <h4 class="text-muted">${__('No period time blocks configured for the program of')} <strong>${sg}</strong></h4>
              <p class="text-muted">${__('Create Period Time Block records for program')} <strong>${result.program || ''}</strong> ${__('first.')}</p>
            </div>
          `)
          return
        }

        let html = `
          <h5 style="margin-bottom:15px;">${__('Timetable for')} <strong>${sg}</strong> — ${display_date}</h5>
          <table class="table table-bordered">
            <thead>
              <tr>
                <th style="width:60px;">${__('Period')}</th>
                <th style="width:140px;">${__('Time')}</th>
                <th>${__('Subject')}</th>
                <th>${__('Instructor')}</th>
                <th>${__('Room')}</th>
              </tr>
            </thead>
            <tbody>
        `
        for (const p of periods) {
          const bg_style = p.is_ongoing ? 'background:#E4F5E9;font-weight:600;' : ''
          const ongoing_badge = p.is_ongoing
            ? ` <span class="indicator-pill green">${__('Now')}</span>`
            : ''

          const subject_cell = p.schedule_name
            ? `<a href="/app/course-schedule/${p.schedule_name}">${p.course}</a>`
            : `<span class="text-muted">—</span>`

          const instructor_cell = p.instructor_name
            ? `<a href="/app/instructor/${p.instructor}">${p.instructor_name}</a>`
            : `<span class="text-muted">—</span>`

          html += `
              <tr style="${bg_style}">
                <td>${p.period_label || __('Period') + ' ' + p.period_number}${ongoing_badge}</td>
                <td>${this.format_time_12hr(p.from_time)} – ${this.format_time_12hr(p.to_time)}</td>
                <td>${subject_cell}</td>
                <td>${instructor_cell}</td>
                <td>${p.room || '—'}</td>
              </tr>
          `
        }
        html += '</tbody></table>'
        this.$body.html(html)
      },
    })
  }
}
