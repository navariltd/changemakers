frappe.ui.form.on("Project", {
	refresh: function (frm) {
		setup_state_filter(frm);
	},

	custom_project_countrys: function (frm) {
		filter_states_by_selected_countries(frm);
	},
});

function setup_state_filter(frm) {
	let states_field = frm.fields_dict.custom_states;

	states_field.get_query = function () {
		let selected_countries = (frm.doc.custom_project_countrys || []).map(
			(d) => d.country
		);

		if (selected_countries.length > 0) {
			return {
				filters: {
					country: ["in", selected_countries],
				},
			};
		} else {
			return {};
		}
	};
}

function filter_states_by_selected_countries(frm) {
	if (frm.fields_dict.custom_states) {
		frm.fields_dict.custom_states.refresh();
	}

	let selected_states = frm.doc.custom_states || [];
	let selected_country_names = (frm.doc.custom_project_countrys || []).map(
		(d) => d.country
	);

	if (selected_states.length > 0 && selected_country_names.length > 0) {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "State",
				filters: {
					name: ["in", selected_states.map((d) => d.state)],
					country: ["not in", selected_country_names],
				},
				fields: ["name"],
			},
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					let valid_states = selected_states.filter(
						(d) =>
							!r.message.some(
								(invalid) => invalid.name === d.state
							)
					);

					if (valid_states.length !== selected_states.length) {
						frm.set_value("custom_states", valid_states);
					}
				}
			},
		});
	}
}
