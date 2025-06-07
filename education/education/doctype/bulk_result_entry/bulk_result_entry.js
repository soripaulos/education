frappe.ui.form.on('Bulk Result Entry', {
    student_group: function(frm) {
        if (frm.doc.student_group) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Student Group',
                    fieldname: 'students',
                    filters: { name: frm.doc.student_group }
                },
                callback: function(r) {
                    if (r.message && r.message.students) {
                        frm.clear_table('results');
                        r.message.students.forEach(student => {
                            const row = frm.add_child('results');
                            row.student = student.student;
                            frappe.model.set_value(
                                row.doctype,
                                row.name,
                                'student_name',
                                student.student_name
                            );
                        });
                        frm.refresh_field('results');
                    }
                }
            });
        }
    },
    
    validate: function(frm) {
        // Validate scores before saving
        const max_score = frm.doc.max_score;
        frm.doc.results.forEach(row => {
            if (row.score > max_score) {
                frappe.throw(`Score for ${row.student_name} exceeds max score of ${max_score}`);
            }
        });
    },
    
    on_submit: function(frm) {
        // Create and submit individual exam results
        frm.call({
            method: 'education_tools.utils.create_exam_results_from_bulk',
            args: {
                bulk_entry: frm.doc.name
            },
            freeze: true,
            freeze_message: __('Creating exam records...'),
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint({
                        title: __('Success'),
                        message: __('Created {0} exam records', [r.message.length])
                    });
                }
            }
        });
    }
});
