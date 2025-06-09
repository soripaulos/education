// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Term Subject Result', {
    // 1. INITIALIZATION
    onload: function(frm) {
        frm.__lastExaminer = frm.doc.examiner;
        frm.__lastGrade = frm.doc.grade;
        frm.__lastSubject = frm.doc.subject;
        frm.__lastStudentGroup = frm.doc.student_group;
        
        if (frm.doc.grade) filterStudentGroups(frm);
    },

    // 2. FIELD CHANGE HANDLERS
    examiner: function(frm) {
        filterStudentGroups(frm);
        clearDownstreamFields(frm, ['student_group', 'student']);
    },

    grade: function(frm) {
        filterStudentGroups(frm);
        clearDownstreamFields(frm, ['student_group', 'student']);
    },

    subject: function(frm) {
        filterStudentGroups(frm);
        clearDownstreamFields(frm, ['student_group', 'student']);
    },

    student_group: function(frm) {
        if (!frm.doc.student_group) return;
        
        // Clear student when group changes
        if (frm.__lastStudentGroup !== frm.doc.student_group) {
            frm.set_value('student', '');
            frm.__lastStudentGroup = frm.doc.student_group;
        }

        // FETCH STUDENTS USING WORKING APPROACH
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Student Group',
                name: frm.doc.student_group
            },
            callback: function(r) {
                if (r.message) {
                    // Extract student list from child table
                    const student_list = r.message.students.map(
                        student => student.student
                    );
                    
                    // Set query filter for student field
                    frm.set_query('student', function() {
                        return {
                            filters: [
                                ['name', 'in', student_list]
                            ]
                        };
                    });
                    
                    // Debugging
                    console.log('Students in group:', student_list);
                }
            }
        });
    },

    // 3. SCORE VALIDATION
    score: function(frm) {
        calculate_percentage(frm);
        validate_score(frm);
    },

    max_score: function(frm) {
        calculate_percentage(frm);
        validate_score(frm);
    },

    student: function(frm) {
        if (frm.doc.student) {
            frappe.db.get_value('Student', frm.doc.student, 'student_name')
                .then(r => {
                    if (r.message) {
                        frm.set_value('student_name', r.message.student_name);
                    }
                });
        }
    },

    refresh: function(frm) {
        // Set student name when student is selected
        if (frm.doc.student && !frm.doc.student_name) {
            frappe.db.get_value('Student', frm.doc.student, 'student_name')
                .then(r => {
                    if (r.message) {
                        frm.set_value('student_name', r.message.student_name);
                    }
                });
        }
    }
});

// ======================
// CORE FILTERING FUNCTIONS
// ======================
function filterStudentGroups(frm) {
    // Clear when dependencies change
    if (frm.doc.examiner !== frm.__lastExaminer || 
        frm.doc.grade !== frm.__lastGrade || 
        frm.doc.subject !== frm.__lastSubject) {
        frm.set_value('student_group', '');
    }

    // Update tracking
    frm.__lastExaminer = frm.doc.examiner;
    frm.__lastGrade = frm.doc.grade;
    frm.__lastSubject = frm.doc.subject;

    // CASE 1: Filter by examiner + subject + grade
    if (frm.doc.examiner && frm.doc.subject && frm.doc.grade) {
        filterByExaminer(frm);
    } 
    // CASE 2: Fallback to grade-only filtering
    else if (frm.doc.grade) {
        filterByGrade(frm);
    }
    // CASE 3: No filters
    else {
        frm.set_query('student_group', () => ({}));
    }
}

function filterByExaminer(frm) {
    // Fetch instructor's details
    frappe.db.get_doc('Instructor', frm.doc.examiner)
    .then(instructor => {
        if (!instructor || !instructor.instructor_log) {
            filterByGrade(frm);
            return;
        }
        
        // Get valid groups from instructor_log
        const validGroups = instructor.instructor_log
            .filter(log => 
                log.course === frm.doc.subject &&  // 'course' = subject
                log.program === frm.doc.grade      // 'program' = grade
            )
            .map(log => log.student_group)
            .filter(Boolean); // Remove empty values

        // If no valid groups, fallback to grade filtering
        if (validGroups.length === 0) {
            filterByGrade(frm);
            return;
        }

        // Apply filter to student_group field
        frm.set_query('student_group', () => ({
            filters: { 
                'name': ['in', validGroups],
                'program': frm.doc.grade
            }
        }));
    })
    .catch(error => {
        console.error('Error fetching instructor:', error);
        filterByGrade(frm); // Fallback on error
    });
}

function filterByGrade(frm) {
    // Apply grade filter using program field
    frm.set_query('student_group', () => ({
        filters: { 
            'program': frm.doc.grade
        }
    }));
}

function clearDownstreamFields(frm, fields) {
    fields.forEach(field => {
        if (frm.doc[field]) frm.set_value(field, '');
    });
}

function calculate_percentage(frm) {
    if (frm.doc.score && frm.doc.maximum_score && frm.doc.maximum_score > 0) {
        let percentage = (frm.doc.score / frm.doc.maximum_score) * 100;
        frm.set_value('percentage', percentage);
    }
}

function validate_score(frm) {
    if (frm.doc.score && frm.doc.maximum_score) {
        if (parseFloat(frm.doc.score) > parseFloat(frm.doc.maximum_score)) {
            frappe.msgprint({
                title: __('Invalid Score'),
                indicator: 'red',
                message: __('Score cannot exceed Maximum Score of {0}', [frm.doc.maximum_score])
            });
            frm.set_value('score', '');
        }
        
        if (parseFloat(frm.doc.score) < 0) {
            frappe.msgprint({
                title: __('Invalid Score'),
                indicator: 'red',
                message: __('Score cannot be negative')
            });
            frm.set_value('score', '');
        }
    }
} 