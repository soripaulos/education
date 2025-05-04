// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Assessment Result Tool', {
  setup: function (frm) {
    frm.add_fetch('assessment_plan', 'student_group', 'student_group')
    console.log("Setup function called")
  },

  refresh: function (frm) {
    console.log("Refresh function called")
    if (frappe.route_options) {
      frm.set_value('student_group', frappe.route_options.student_group)
      frm.set_value('assessment_plan', frappe.route_options.assessment_plan)
      frappe.route_options = null
    } else {
      frm.trigger('assessment_plan')
    }
    frm.disable_save()
    frm.page.clear_indicator()

    // Always setup the submit button on refresh if an assessment plan is selected
    if (frm.doc.assessment_plan) {
      frm.events.setup_submit_button(frm);
    }
  },

  assessment_plan: function (frm) {
    console.log("Assessment plan function called with assessment_plan:", frm.doc.assessment_plan)
    if (frm.doc.assessment_plan) {
      if (!frm.doc.student_group) return
      frappe.call({
        method: 'education.education.api.get_assessment_students',
        args: {
          assessment_plan: frm.doc.assessment_plan,
          student_group: frm.doc.student_group,
        },
        callback: function (r) {
          if (r.message) {
            console.log("Got students response:", r.message.length, "students")
            frm.doc.students = r.message
            frm.events.render_table(frm)

            // Setup the submit button after students are loaded
            frm.events.setup_submit_button(frm);
          }
        },
      })
    }
  },

  render_table: function (frm) {
    $(frm.fields_dict.result_html.wrapper).empty()
    let assessment_plan = frm.doc.assessment_plan
    frappe.call({
      method: 'education.education.api.get_assessment_details',
      args: {
        assessment_plan: assessment_plan,
      },
      callback: function (r) {
        frm.events.get_marks(frm, r.message)
      },
    })
  },

  get_marks: function (frm, criteria_list) {
    let max_total_score = 0
    criteria_list.forEach(function (c) {
      max_total_score += c.maximum_score
    })
    var result_table = $(
      frappe.render_template('assessment_result_tool', {
        frm: frm,
        students: frm.doc.students,
        criteria: criteria_list,
        max_total_score: max_total_score,
      })
    )
    result_table.appendTo(frm.fields_dict.result_html.wrapper)

    $('.assessment-criteria').on('keydown', function (e) {
      // get data-criteria attribute
      let criteriaIndex = cint(
        e.target.parentElement.getAttribute('data-criteria-index')
      )
      changeFocusToNextCell(e, 2 + criteriaIndex)
    })

    $('.result-comment').on('keydown', function (e) {
      changeFocusToNextCell(e, 5)
    })

    function changeFocusToNextCell(e, cellIndex) {
      if (e.keyCode === 13 && !e.shiftKey) {
        let nextRow = e.target.parentElement.parentElement.nextElementSibling
        if (nextRow) {
          nextRow.cells[cellIndex].lastElementChild.focus()
        }
      }
      if (e.keyCode === 13 && e.shiftKey) {
        let prevRow =
          e.target.parentElement.parentElement.previousElementSibling
        if (prevRow) {
          prevRow.cells[cellIndex].lastElementChild.focus()
        }
      }
    }

    result_table.on('change', 'input.student-result-data', function (e) {
      let $input = $(e.target)
      let student = $input.data().student
      let assessment_criteria = $input.data().criteria
      let max_score = $input.data().maxScore
      let score = parseFloat($input.val()) || 0; // Use 0 if NaN

      // Client-side validation
      if (score < 0) {
        $input.val(0)
        score = 0;
      } else if (score > max_score) {
        $input.val(max_score)
        score = max_score;
        frappe.show_alert({ message: __("Score cannot exceed Maximum Score ({0})", [max_score]), indicator: 'orange' })
      }

      // Call the new backend function for this single score change
      frappe.call({
        method: 'education.education.api.log_single_assessment_score',
        args: {
          student: student,
          assessment_plan: frm.doc.assessment_plan,
          assessment_criteria: assessment_criteria,
          score: score,
        },
        callback: function (r) {
          if (r.message) {
            let result = r.message;
            // Update the specific grade badge
            $input.siblings('.student-result-grade') // Find the badge next to the input
              .html(result.detail_grade);

            // Update total score and grade for the student's row
            let student_row = $input.closest('tr'); // Find the parent table row
            student_row.find('.total-score').html(result.overall_score);
            student_row.find('.total-score-grade').html(result.overall_grade);

            // Update link if it exists or show it if new
            let link_span = student_row.find('.total-result-link');
            link_span.css('display', 'block');
            link_span.find('a').attr('href', '/app/assessment-result/' + result.name);
          }
        },
        error: function(r) {
            // Optional: Add better error handling on the frontend
            console.error("Error saving assessment score:", r);
            frappe.show_alert({ message: __("Error saving score. Check console."), indicator: 'red' });
        }
      });

      // Ensure submit button is visible after a score change/save
      frm.events.setup_submit_button(frm);
    })

    result_table.on('change', 'input.result-comment', function (e) {
        // Placeholder: Decide how/when to save comments
        console.log("Comment changed, but auto-save not implemented for comments yet.");
        // You could potentially call log_single_assessment_score or a new function here
        // let $input = $(e.target);
        // let student = $input.data().student;
        // let comment = $input.val();
        // // ... call backend to save comment ...

        // Ensure submit button is visible after comment change
        frm.events.setup_submit_button(frm);
    });
  },

  // New function to consistently setup the submit button
  setup_submit_button: function(frm) {
    // Remove existing button first to avoid duplicates if called multiple times
    if (frm.page.primary_action) {
      frm.page.clear_primary_action();
    }

    // Add the button only if an assessment plan is selected
    if (frm.doc.assessment_plan) {
      console.log("Setting up submit button");
      frm.page.set_primary_action(__('Submit Results'), function () {
        frappe.call({
          method: 'education.education.api.submit_assessment_results',
          args: {
            assessment_plan: frm.doc.assessment_plan,
            student_group: frm.doc.student_group,
          },
          callback: function (r) {
            if (r.message) {
              frappe.msgprint(__('{0} Results submitted', [r.message]));
              // Optionally refresh the view after submission
              frm.refresh();
            } else {
              frappe.msgprint(__('No Results to submit or an error occurred.'));
            }
          },
        });
      });
    }
  }
})
