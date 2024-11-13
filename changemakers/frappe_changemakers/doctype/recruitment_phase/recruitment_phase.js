// Copyright (c) 2024, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.ui.form.on("Recruitment Phase", {
	refresh(frm) {
		frm.events.validate_available_slots(frm);
	},

	total_slots(frm) {
		frm.events.validate_total_slots(frm);
	},

	before_save(frm) {
		frm.events.validate_total_slots(frm);
		frm.events.validate_available_slots(frm);
	},

	validate_total_slots(frm) {
		const total_slots = frm.doc.total_slots || 0;
		let slots_total = 0;

		frm.doc.slots.forEach((row) => {
			slots_total += row.slots || 0;
		});

		if (slots_total > total_slots) {
			frappe.throw(
				__(
					"The total slots in Slot Allocation cannot exceed the Total Slots."
				),
				"red"
			);
		}
	},

	validate_available_slots(frm) {
		if (!frm.is_new()) {
			frappe.call({
				method: "changemakers.frappe_changemakers.doctype.recruitment_phase.recruitment_phase.check_available_slots",
				args: {
					phase_name: frm.doc.name,
				},
				callback: function (response) {
					if (response.message) {
						const available_slots = response.message;
						let total_active_beneficiaries = 0;
						let is_valid = true;

						frm.doc.slots.forEach((row) => {
							const branch = row.branch;
							if (available_slots[branch]) {
								row.available_slots =
									available_slots[branch].available_slots;
								total_active_beneficiaries +=
									available_slots[branch]
										.active_beneficiaries;
							}
						});
						if (!is_valid) {
							frappe.validated = false;
						}
						const total_slots = parseInt(frm.doc.total_slots) || 0;
						const overall_available_slots =
							total_slots - total_active_beneficiaries;

						frm.set_value(
							"available_slots",
							overall_available_slots
						);
						frm.refresh_field("slots");
					}
				},
			});
		}
	},
});

frappe.ui.form.on("Recruitment Phase Slot Allocation", {
	slots(frm, cdt, cdn) {
		frm.events.validate_total_slots(frm);
		frm.events.validate_available_slots(frm);
	},
});
