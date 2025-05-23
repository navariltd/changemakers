// Copyright (c) 2025, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.ui.form.on("Donation Allocation", {
	refresh(frm) {
		if (!frm.doc.date) {
			frm.set_value("date", frappe.datetime.get_today());
		}
	},
});
