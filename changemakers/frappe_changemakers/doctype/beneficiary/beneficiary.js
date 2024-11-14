// Copyright (c) 2022, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.ui.form.on("Beneficiary", {
	refresh(frm) {
		frm.toggle_display("address_html", !frm.is_new());
		frm.toggle_display("contact_html", !frm.is_new());
		if (!frm.is_new()) {
			frappe.contacts.render_address_and_contact(frm);
		}
	},
	setup: (frm) => {
		changemakers.utils.set_query_for_district(frm);
		changemakers.utils.set_query_for_zone(frm);
		changemakers.utils.set_query_for_ward(frm);
	},
	state: changemakers.utils.handle_state_field,
	district: changemakers.utils.handle_district_field,
	zone: changemakers.utils.handle_zone_field,
	ward: changemakers.utils.handle_ward_field,
	bottom_save_button: (frm) => {
		frm.save();
	},
});
