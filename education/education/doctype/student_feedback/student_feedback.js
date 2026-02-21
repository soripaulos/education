// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Feedback', {
    refresh: function(frm) {
        // Fetch taxonomy and setup the form
        get_taxonomy_and_setup(frm);
    },

    category: function(frm) {
        // When category changes, update subcategory options
        update_subcategory_options(frm);
        frm.set_value('subcategory', '');
        frm.set_value('specific_issue', '');
    },

    subcategory: function(frm) {
        // When subcategory changes, update specific issue options
        update_specific_issue_options(frm);
        frm.set_value('specific_issue', '');
    }
});

let feedback_taxonomy = {};

function get_taxonomy_and_setup(frm) {
    // Fetch the taxonomy from Feedback Settings
    frappe.call({
        method: "education.api.get_feedback_taxonomy",
        callback: function(r) {
            if (r.message) {
                feedback_taxonomy = r.message;
                setup_form_options(frm);
            } else {
                // Fallback or error handling
                frappe.msgprint(__("Could not load feedback categories. Please contact the system administrator."));
            }
        }
    });
}

function setup_form_options(frm) {
    // Populate the category dropdown
    let categories = Object.keys(feedback_taxonomy);
    frm.set_df_property('category', 'options', [''].concat(categories));

    // Initial setup for subcategory and issue
    update_subcategory_options(frm);
    update_specific_issue_options(frm);
}

function update_subcategory_options(frm) {
    if (frm.doc.category && feedback_taxonomy[frm.doc.category]) {
        let subcategories = Object.keys(feedback_taxonomy[frm.doc.category]);
        frm.set_df_property('subcategory', 'options', [''].concat(subcategories));
        // Show/hide field based on whether there are options
        frm.set_df_property('subcategory', 'hidden', subcategories.length === 0);
    } else {
        frm.set_df_property('subcategory', 'options', []);
        frm.set_df_property('subcategory', 'hidden', 1);
    }
    frm.refresh_field('subcategory');
}

function update_specific_issue_options(frm) {
    if (frm.doc.category && frm.doc.subcategory && feedback_taxonomy[frm.doc.category][frm.doc.subcategory]) {
        let issues = feedback_taxonomy[frm.doc.category][frm.doc.subcategory];
        frm.set_df_property('specific_issue', 'options', [''].concat(issues));
        // Show/hide field based on whether there are options
        frm.set_df_property('specific_issue', 'hidden', issues.length === 0);
    } else {
        frm.set_df_property('specific_issue', 'options', []);
        frm.set_df_property('specific_issue', 'hidden', 1);
    }
    frm.refresh_field('specific_issue');
} 