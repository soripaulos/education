// Custom Client Script for Student Term Subject Result
// Add this as a Client Script in your ERPNext system

frappe.ui.form.on('Student Term Subject Result', {
    onload: function(frm) {
        // Calculate percentage on load
        calculate_percentage_custom(frm);
    },
    
    refresh: function(frm) {
        // Calculate percentage on refresh
        calculate_percentage_custom(frm);
    },
    
    score: function(frm) {
        calculate_percentage_custom(frm);
        validate_score_custom(frm);
    },
    
    max_score: function(frm) {
        calculate_percentage_custom(frm);
        validate_score_custom(frm);
    }
});

function calculate_percentage_custom(frm) {
    if (frm.doc.score && frm.doc.max_score && frm.doc.max_score > 0) {
        let percentage = (frm.doc.score / frm.doc.max_score) * 100;
        // Only set if percentage field exists and value has changed
        if (frm.fields_dict.percentage && frm.doc.percentage !== percentage) {
            frm.set_value('percentage', percentage);
        }
    }
}

function validate_score_custom(frm) {
    if (frm.doc.score && frm.doc.max_score) {
        if (parseFloat(frm.doc.score) > parseFloat(frm.doc.max_score)) {
            frappe.msgprint({
                title: __('Invalid Score'),
                indicator: 'red',
                message: __('Score cannot exceed Max Score of {0}', [frm.doc.max_score])
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