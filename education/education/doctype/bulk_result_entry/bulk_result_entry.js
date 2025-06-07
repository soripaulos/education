frappe.ui.form.on('Bulk Result Entry', {
    student_group: function(frm) {
        if (frm.doc.student_group) {
            // Fetch students in the selected group
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Student Group',
                    fieldname: 'students',
                    filters: { name: frm.doc.student_group }
                },
                callback: function(r) {
                    if (r.message && r.message.students) {
                        // Clear existing table
                        frm.clear_table('results');
                        
                        // Add each student to the table
                        r.message.students.forEach(function(student) {
                            var row = frm.add_child('results');
                            row.student = student.student;
                            
                            // Fetch and set student name
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
    
    before_save: function(frm) {
        // Validate scores
        var max_score = frm.doc.max_score;
        frm.doc.results.forEach(function(row) {
            if (row.score > max_score) {
                frappe.throw("Score for " + row.student_name + " exceeds max score of " + max_score);
            }
        });
    },
    
    on_submit: function(frm) {
        // Create individual exam result records
        frm.doc.results.forEach(function(row) {
            var exam_result = frappe.model.make_new_doc({
                doctype: 'Student Exam Result',
                student: row.student,
                academic_term: frm.doc.academic_term,
                subject: frm.doc.subject,
                assessment_criteria: frm.doc.assessment_criteria,
                score: row.score,
                max_score: frm.doc.max_score,
                student_group: frm.doc.student_group
            });
            
            exam_result.insert();
        });
        
        frappe.msgprint("Created individual exam records for all students");
    }
});
