// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Result Calculation Tool', {
	refresh: function (frm) {
		frm.page.set_primary_action(__('Preview & Calculate'), function () {
			preview_and_calculate(frm);
		});

		frm.add_custom_button(__('Preview Only'), function () {
			run_preview(frm, false);
		});

		frm.add_custom_button(__('View Calculation Logs'), function () {
			frappe.set_route('List', 'Result Calculation Log');
		});

		frm.add_custom_button(__('Bulk Sign Reports'), function () {
			open_bulk_sign_dialog(frm);
		});

		setup_realtime(frm);
		render_recent_logs(frm);
	},

	calculation_type: function (frm) {
		// stale preview no longer applies to the new mode
		frm.get_field('preview_html').$wrapper.empty();
	},
});

// ---------------------------------------------------------------------------
// Parameter collection & validation
// ---------------------------------------------------------------------------

function collect_params(frm) {
	return {
		calculation_type: frm.doc.calculation_type,
		academic_year: frm.doc.academic_year,
		semester: frm.doc.semester,
		student_group: frm.doc.student_group,
		result_action: frm.doc.result_action,
		run_in_background: cint(frm.doc.run_in_background),
		draft_result_handling: frm.doc.draft_result_handling,
		incomplete_subject_policy: frm.doc.incomplete_subject_policy,
		only_active_students: cint(frm.doc.only_active_students),
		existing_report_policy: frm.doc.existing_report_policy,
		respect_course_exclusion_flags: cint(frm.doc.respect_course_exclusion_flags),
		excluded_courses: (frm.doc.excluded_courses || []).map((r) => r.course),
		missing_term_policy: frm.doc.missing_term_policy,
		year_average_method: frm.doc.year_average_method,
		terms_to_include: (frm.doc.terms_to_include || []).map((r) => r.academic_term),
	};
}

function validate_params(frm) {
	if (!frm.doc.calculation_type) {
		frappe.msgprint(__('Please select a Calculation Type'));
		return false;
	}
	if (!frm.doc.academic_year) {
		frappe.msgprint(__('Please select an Academic Year'));
		return false;
	}
	if (frm.doc.calculation_type === 'Term Results' && !frm.doc.semester) {
		frappe.msgprint(__('Please select a Semester for Term Results calculation'));
		return false;
	}
	return true;
}

// ---------------------------------------------------------------------------
// Preview
// ---------------------------------------------------------------------------

function run_preview(frm, then_calculate) {
	if (!validate_params(frm)) return;

	frappe.call({
		method:
			'education.education.doctype.result_calculation_tool.result_calculation_tool.preview_calculation',
		args: { params: collect_params(frm) },
		freeze: true,
		freeze_message: __('Analyzing data...'),
		callback: function (r) {
			if (!r.message) return;
			let preview = r.message;
			render_preview(frm, preview);
			if (then_calculate) {
				show_confirmation_dialog(frm, preview);
			}
		},
	});
}

function preview_and_calculate(frm) {
	run_preview(frm, true);
}

function level_color(level) {
	return { error: 'red', warning: 'orange', info: 'blue' }[level] || 'gray';
}

function esc(value) {
	return frappe.utils.escape_html(String(value == null ? '' : value));
}

function capped_list_html(capped, formatter) {
	if (!capped || !capped.total) return '';
	let items = capped.items.map(formatter).join('');
	let more = capped.more
		? `<li class="text-muted">${__('...and {0} more', [capped.more])}</li>`
		: '';
	return `<ul style="margin: 4px 0 8px; padding-left: 18px;">${items}${more}</ul>`;
}

function build_preview_html(preview) {
	let html = '';

	// headline stats
	let stats = [
		[__('Students'), preview.total_students],
		[__('Student Groups'), preview.total_groups],
	];
	if (preview.calculation_type === 'Term Results') {
		stats.push([__('Subject Results Used'), preview.results_count]);
		stats.push([__('Draft Subject Results'), preview.draft_count]);
	} else {
		stats.push([__('Term Reports Used'), preview.reports_count]);
		stats.push([__('Draft Term Reports'), preview.draft_count]);
		stats.push([__('Terms in Year'), (preview.expected_terms || []).length]);
	}
	stats.push([
		__('Existing Reports'),
		`${preview.existing_reports.draft} ${__('draft')}, ${preview.existing_reports.submitted} ${__(
			'submitted'
		)}`,
	]);

	html += '<div class="row" style="margin-bottom: 10px;">';
	stats.forEach(([label, value]) => {
		html += `<div class="col-sm-3" style="margin-bottom:8px;">
			<div class="text-muted small">${esc(label)}</div>
			<div style="font-size: 1.2em; font-weight: 600;">${esc(value)}</div>
		</div>`;
	});
	html += '</div>';

	// issues
	if (preview.issues && preview.issues.length) {
		html += `<h6>${__('Findings')}</h6>`;
		preview.issues.forEach((issue) => {
			html += `<div class="indicator-pill-round ${level_color(issue.level)}"
				style="display:block; border-radius:6px; padding:6px 10px; margin-bottom:6px; white-space:normal;">
				<b>${esc(issue.level.toUpperCase())}</b>: ${esc(issue.message)}</div>`;
		});
	} else {
		html += `<div class="indicator-pill-round green" style="display:block; border-radius:6px; padding:6px 10px; margin-bottom:6px;">
			${__('No data quality issues detected.')}</div>`;
	}

	// excluded courses
	if (preview.excluded_courses && preview.excluded_courses.length) {
		html += `<h6 style="margin-top:10px;">${__('Courses excluded from averages')}</h6>
			<p>${preview.excluded_courses.map(esc).join(', ')}
			<br><span class="text-muted small">${__(
				'{0} from Course-level flags, {1} added for this run. Scores still appear on reports.',
				[(preview.flagged_courses || []).length, (preview.manual_courses || []).length]
			)}</span></p>`;
	}

	// terms breakdown (year mode)
	if (preview.expected_terms && preview.expected_terms.length) {
		html += `<h6 style="margin-top:10px;">${__('Terms making up the year')}</h6><ul style="padding-left:18px;">`;
		preview.expected_terms.forEach((t) => {
			let count = (preview.term_report_counts || {})[t];
			html += `<li>${esc(t)} — ${__('{0} term reports', [count == null ? 0 : count])}</li>`;
		});
		html += '</ul>';
	}

	// per-group details
	(preview.groups || []).forEach((g) => {
		let details = '';

		if (g.incomplete_students && g.incomplete_students.total) {
			let label =
				preview.calculation_type === 'Term Results'
					? __('Students with missing subjects')
					: __('Students with missing terms (joined late / left early)');
			details += `<b>${label} (${g.incomplete_students.total}):</b>`;
			details += capped_list_html(g.incomplete_students, (s) => {
				return `<li>${esc(s.student_name)} — ${__('missing')}: ${s.missing
					.map(esc)
					.join(', ')}</li>`;
			});
		}
		if (g.members_without_results && g.members_without_results.total) {
			details += `<b>${__('Active students with no results at all')} (${
				g.members_without_results.total
			}):</b>`;
			details += capped_list_html(g.members_without_results, (n) => `<li>${esc(n)}</li>`);
		}
		if (g.inactive_with_results && g.inactive_with_results.total) {
			details += `<b>${__('Inactive students who have results')} (${
				g.inactive_with_results.total
			}):</b>`;
			details += capped_list_html(g.inactive_with_results, (n) => `<li>${esc(n)}</li>`);
		}
		if (g.non_members_with_results && g.non_members_with_results.total) {
			details += `<b>${__('Students with results but not on the group roster')} (${
				g.non_members_with_results.total
			}):</b>`;
			details += capped_list_html(g.non_members_with_results, (n) => `<li>${esc(n)}</li>`);
		}
		if (g.excluded_subjects && g.excluded_subjects.length) {
			details += `<b>${__('Excluded subjects in this group')}:</b> ${g.excluded_subjects
				.map(esc)
				.join(', ')}<br>`;
		}

		let body = details || `<span class="text-muted">${__('No issues in this group.')}</span>`;
		html += `<details style="margin-top:8px;"><summary style="cursor:pointer;">
			<b>${esc(g.group)}</b> — ${__('{0} students', [g.students_with_results])}</summary>
			<div style="padding: 6px 0 0 10px;">${body}</div></details>`;
	});

	return html;
}

function render_preview(frm, preview) {
	frm.get_field('preview_html').$wrapper.html(
		`<div class="frappe-card" style="padding: 12px;">
			<h5 style="margin-top:0;">${__('Pre-Calculation Check')} — ${esc(preview.calculation_type)}</h5>
			${build_preview_html(preview)}
		</div>`
	);
}

// ---------------------------------------------------------------------------
// Confirmation & execution
// ---------------------------------------------------------------------------

function show_confirmation_dialog(frm, preview) {
	if (!preview.can_proceed) {
		frappe.msgprint({
			title: __('Cannot Calculate'),
			indicator: 'red',
			message: __(
				'Blocking problems were found — see the preview below the form. Fix the data or relax the policies, then try again.'
			),
		});
		return;
	}

	let warnings = (preview.issues || []).filter((i) => i.level === 'warning');
	let action_text =
		frm.doc.result_action === 'Save and Submit'
			? __('calculate and SUBMIT reports')
			: __('calculate and save reports as drafts');

	let message = `<p>${__('About to {0} for <b>{1}</b> student(s) in <b>{2}</b> group(s).', [
		action_text,
		preview.total_students,
		preview.total_groups,
	])}</p>`;

	if (warnings.length) {
		message += `<p><b>${__('Please note')}:</b></p><ul>`;
		warnings.forEach((w) => (message += `<li>${esc(w.message)}</li>`));
		message += '</ul>';
	}
	message += `<p class="text-muted small">${__(
		'A detailed log of everything done will be saved as a Result Calculation Log.'
	)}</p>`;

	let d = new frappe.ui.Dialog({
		title: __('Confirm Calculation'),
		fields: [{ fieldtype: 'HTML', fieldname: 'body', options: message }],
		primary_action_label: __('Start Calculation'),
		primary_action: function () {
			d.hide();
			start_calculation(frm);
		},
	});
	d.show();
}

function start_calculation(frm) {
	frappe.call({
		method:
			'education.education.doctype.result_calculation_tool.result_calculation_tool.start_calculation',
		args: { params: collect_params(frm) },
		freeze: !cint(frm.doc.run_in_background),
		freeze_message: __('Calculating results...'),
		callback: function (r) {
			if (!r.message) return;
			frm._active_log = r.message.log_name;
			if (r.message.queued) {
				frappe.show_alert({
					message: __('Calculation started in the background (log: {0})', [
						`<a href="/app/result-calculation-log/${r.message.log_name}">${r.message.log_name}</a>`,
					]),
					indicator: 'blue',
				});
			} else {
				show_completion(frm, r.message.log_name, r.message.status, r.message.summary);
			}
			render_recent_logs(frm);
		},
		error: function () {
			frappe.show_alert({
				message: __('Calculation failed to start. Check the Error Log.'),
				indicator: 'red',
			});
		},
	});
}

function show_completion(frm, log_name, status, summary) {
	let indicator =
		status === 'Completed' ? 'green' : status === 'Completed with Warnings' ? 'orange' : 'red';
	frappe.msgprint({
		title: __('Calculation {0}', [__(status)]),
		indicator: indicator,
		message: `${esc(summary || '')}<br><br>
			<a class="btn btn-sm btn-default" href="/app/result-calculation-log/${log_name}">
				${__('Open Calculation Log')}</a>`,
	});
	render_recent_logs(frm);
}

// ---------------------------------------------------------------------------
// Realtime updates
// ---------------------------------------------------------------------------

function setup_realtime(frm) {
	if (frm._realtime_bound) return;
	frm._realtime_bound = true;

	frappe.realtime.on('result_calculation_complete', function (data) {
		show_completion(frm, data.log, data.status, data.summary);
	});
}

// ---------------------------------------------------------------------------
// Bulk sign
// ---------------------------------------------------------------------------

function open_bulk_sign_dialog(frm) {
	let d = new frappe.ui.Dialog({
		title: __('Bulk Sign Reports'),
		fields: [
			{
				fieldname: 'calculation_type',
				fieldtype: 'Select',
				label: __('Report Type'),
				options: 'Term Results\nYear Results',
				default: frm.doc.calculation_type || 'Term Results',
				reqd: 1,
			},
			{
				fieldname: 'director',
				fieldtype: 'Link',
				label: __('Director'),
				options: 'School Director',
				reqd: 1,
				description: __("The selected director's stored signature is stamped onto every matching report."),
			},
			{ fieldname: 'cb_scope', fieldtype: 'Column Break' },
			{
				fieldname: 'academic_year',
				fieldtype: 'Link',
				label: __('Academic Year'),
				options: 'Academic Year',
				default: frm.doc.academic_year,
				reqd: 1,
			},
			{
				fieldname: 'semester',
				fieldtype: 'Link',
				label: __('Semester'),
				options: 'Academic Term',
				default: frm.doc.semester,
				depends_on: "eval:doc.calculation_type=='Term Results'",
			},
			{
				fieldname: 'student_group',
				fieldtype: 'Link',
				label: __('Student Group (optional)'),
				options: 'Student Group',
				default: frm.doc.student_group,
			},
			{ fieldname: 'sb_opts', fieldtype: 'Section Break' },
			{
				fieldname: 'only_unsigned',
				fieldtype: 'Check',
				label: __('Only reports not yet signed'),
				default: 0,
			},
			{
				fieldname: 'also_submit',
				fieldtype: 'Check',
				label: __('Also submit draft reports after signing'),
				default: 0,
			},
		],
		primary_action_label: __('Sign Reports'),
		primary_action: function (values) {
			frappe.call({
				method: 'education.education.doctype.result_calculation_tool.result_calculation_tool.bulk_sign_reports',
				args: { params: values },
				freeze: true,
				freeze_message: __('Signing reports...'),
				callback: function (r) {
					if (!r.message) return;
					let m = r.message;
					d.hide();
					frappe.msgprint({
						title: __('Bulk Sign Complete'),
						indicator: m.failed ? 'orange' : 'green',
						message: __(
							'{0} of {1} report(s) signed by {2}.{3}{4}',
							[
								m.signed,
								m.total,
								frappe.utils.escape_html(m.director),
								m.submitted ? '<br>' + __('{0} submitted.', [m.submitted]) : '',
								m.failed ? '<br>' + __('{0} failed (see Error Log).', [m.failed]) : '',
							]
						),
					});
				},
			});
		},
	});
	d.show();
}

// ---------------------------------------------------------------------------
// Recent runs
// ---------------------------------------------------------------------------

function render_recent_logs(frm) {
	frappe.call({
		method:
			'education.education.doctype.result_calculation_tool.result_calculation_tool.get_recent_logs',
		args: { limit: 5 },
		callback: function (r) {
			let logs = r.message || [];
			let $wrapper = frm.get_field('logs_html').$wrapper;
			if (!logs.length) {
				$wrapper.html(`<p class="text-muted">${__('No calculation runs yet.')}</p>`);
				return;
			}
			let colors = {
				Queued: 'orange',
				'In Progress': 'blue',
				Completed: 'green',
				'Completed with Warnings': 'orange',
				Failed: 'red',
			};
			let rows = logs
				.map((log) => {
					let scope = [log.academic_year, log.semester, log.student_group]
						.filter(Boolean)
						.map(esc)
						.join(' / ');
					return `<tr>
						<td><a href="/app/result-calculation-log/${log.name}">${esc(log.name)}</a></td>
						<td><span class="indicator-pill ${colors[log.status] || 'gray'}">${esc(
							__(log.status)
						)}</span></td>
						<td>${esc(__(log.calculation_type || ''))}</td>
						<td>${scope}</td>
						<td>${esc(log.started_at ? frappe.datetime.str_to_user(log.started_at) : '')}</td>
						<td class="small">${esc(log.summary || '')}</td>
					</tr>`;
				})
				.join('');
			$wrapper.html(`<table class="table table-bordered small" style="margin-top:4px;">
				<thead><tr>
					<th>${__('Log')}</th><th>${__('Status')}</th><th>${__('Type')}</th>
					<th>${__('Scope')}</th><th>${__('Started')}</th><th>${__('Summary')}</th>
				</tr></thead><tbody>${rows}</tbody></table>`);
		},
	});
}
