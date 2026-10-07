frappe.listview_settings['Not Promoted Student'] = {
  onload(listview) {
    listview.page.add_inner_button(__('Suggest from Promotion Rules'), () => suggest())
  },
}

function suggest() {
  const dialog = new frappe.ui.Dialog({
    title: __('Suggest Not Promoted Students'),
    fields: [
      {
        fieldname: 'academic_year',
        label: __('Academic Year (the year just finished)'),
        fieldtype: 'Link',
        options: 'Academic Year',
        reqd: 1,
      },
      { fieldname: 'result', fieldtype: 'HTML' },
    ],
    primary_action_label: __('Check'),
    primary_action(values) {
      frappe.call({
        method: 'education.education.lifecycle.promotion.get_not_promoted_suggestions',
        args: { academic_year: values.academic_year },
        freeze: true,
        callback(r) {
          const data = r.message || {}
          const rows = data.suggestions || []
          const esc = frappe.utils.escape_html
          let html = `<p>${__('Checked {0} enrolled students. {1} are not promoted by the rules and not on the list yet. {2} have no result to judge (no year report or exam result).', [
            data.checked || 0,
            rows.length,
            data.pending || 0,
          ])}</p>`
          if (rows.length) {
            html += `<div style="max-height: 360px; overflow: auto"><table class="table table-bordered table-condensed small"><thead><tr>
              <th><input type="checkbox" class="np-all" checked></th><th>${__('Student')}</th><th>${__('Program')}</th><th>${__('Average')}</th><th>${__('Why')}</th></tr></thead><tbody>`
            rows.forEach((s) => {
              html += `<tr><td><input type="checkbox" class="np-row" data-student="${esc(s.student)}" checked></td>
                <td>${esc(s.student_name || '')}<br><span class="text-muted">${esc(s.school_id || '')}</span></td>
                <td>${esc(s.program || '')}</td><td>${s.average != null ? format_number(s.average, null, 1) : ''}</td>
                <td>${esc(s.reasons || '')}</td></tr>`
            })
            html += '</tbody></table></div>'
          }
          dialog.fields_dict.result.$wrapper.html(html)
          dialog.$wrapper.find('.np-all').on('change', function () {
            dialog.$wrapper.find('.np-row').prop('checked', this.checked)
          })
          if (rows.length) {
            dialog.set_primary_action(__('Add Ticked to Not Promoted List'), () => {
              const students = dialog.$wrapper
                .find('.np-row:checked')
                .map(function () {
                  return $(this).data('student')
                })
                .get()
              if (!students.length) return
              frappe.call({
                method: 'education.education.lifecycle.promotion.create_not_promoted_records',
                args: { academic_year: values.academic_year, students },
                freeze: true,
                callback(res) {
                  dialog.hide()
                  frappe.show_alert({ message: __('{0} added', [(res.message || []).length]), indicator: 'green' })
                  cur_list && cur_list.refresh()
                },
              })
            })
          }
        },
      })
    },
  })
  dialog.show()
}
