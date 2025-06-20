// Copyright (c) 2024, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('School Feedback', {
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
		
		// Setup dynamic category options
		setup_category_options(frm);
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
	
	category: function(frm) {
		// Clear dependent fields when category changes
		frm.set_value('subcategory', '');
		frm.set_value('specific_issue', '');
		
		// Setup subcategory options based on selected category
		setup_subcategory_options(frm);
	},
	
	subcategory: function(frm) {
		// Clear specific issue when subcategory changes
		frm.set_value('specific_issue', '');
		
		// Setup specific issue options based on selected subcategory
		setup_specific_issue_options(frm);
	},
	
	feedback_categories_config: function(frm) {
		// Refresh category options when configuration changes
		setup_category_options(frm);
	}
});

function get_categories_config(frm) {
	// Get categories configuration from the document or use default
	let config = frm.doc.feedback_categories_config;
	
	if (!config) {
		// Default configuration
		config = {
			"Academic Issues": {
				"Curriculum": ["Content Difficulty", "Pace Too Fast", "Pace Too Slow", "Missing Topics"],
				"Teaching Methods": ["Unclear Explanations", "Lack of Examples", "No Interactive Activities", "Poor Use of Technology"],
				"Assessment": ["Unfair Grading", "Too Many Tests", "Unclear Instructions", "Late Feedback"]
			},
			"Facility Issues": {
				"Classroom": ["Poor Lighting", "Uncomfortable Seating", "Temperature Issues", "Cleanliness"],
				"Technology": ["Broken Equipment", "Internet Issues", "Software Problems", "Lack of Resources"],
				"Safety": ["Security Concerns", "Emergency Procedures", "Maintenance Issues", "Accessibility"]
			},
			"Administrative Issues": {
				"Communication": ["Poor Information Sharing", "Late Notifications", "Unclear Policies", "Language Barriers"],
				"Scheduling": ["Conflicting Times", "Too Many Classes", "Break Time Issues", "Event Planning"],
				"Documentation": ["Missing Records", "Incorrect Information", "Slow Processing", "Lost Documents"]
			},
			"Other Issues": {}
		};
	}
	
	// Parse if it's a string
	if (typeof config === 'string') {
		try {
			config = JSON.parse(config);
		} catch (e) {
			console.error('Error parsing categories config:', e);
			return {};
		}
	}
	
	return config;
}

function setup_category_options(frm) {
	let config = get_categories_config(frm);
	let categories = Object.keys(config);
	
	// Set category field options
	frm.set_df_property('category', 'options', categories.join('\n'));
}

function setup_subcategory_options(frm) {
	if (!frm.doc.category || frm.doc.category === 'Other Issues') {
		frm.set_df_property('subcategory', 'options', '');
		return;
	}
	
	let config = get_categories_config(frm);
	let subcategories = Object.keys(config[frm.doc.category] || {});
	
	// Set subcategory field options
	frm.set_df_property('subcategory', 'options', subcategories.join('\n'));
}

function setup_specific_issue_options(frm) {
	if (!frm.doc.category || !frm.doc.subcategory || frm.doc.category === 'Other Issues') {
		frm.set_df_property('specific_issue', 'options', '');
		return;
	}
	
	let config = get_categories_config(frm);
	let specific_issues = config[frm.doc.category][frm.doc.subcategory] || [];
	
	// Set specific issue field options
	frm.set_df_property('specific_issue', 'options', specific_issues.join('\n'));
} 
