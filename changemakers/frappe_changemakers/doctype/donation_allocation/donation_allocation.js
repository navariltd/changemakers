// Copyright (c) 2025, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.ui.form.on("Donation Allocation", {
	refresh(frm) {
		// Set today's date if not already set
		if (!frm.doc.date) {
			frm.set_value("date", frappe.datetime.get_today());
		}

		if (frm.doc.donation) {
			calculate_unallocated_amount(frm);
		}
	},

	donation_total_paid_amount(frm) {
		calculate_unallocated_amount(frm);
	},

	donation(frm) {
		calculate_unallocated_amount(frm);
	},
});

function calculate_unallocated_amount(frm) {
	if (!frm.doc.donation || !frm.doc.donation_total_paid_amount) return;

	frappe.call({
		method: "changemakers.frappe_changemakers.doctype.donation_allocation.donation_allocation.get_total_allocated_amount",
		args: {
			donation_name: frm.doc.donation,
			exclude_allocation: frm.doc.name || null,
		},
		callback: function (r) {
			if (r.message !== undefined) {
				let allocated = r.message;
				let unallocated =
					frm.doc.donation_total_paid_amount - allocated;
				frm.set_value("donation_unallocated_amount", unallocated);
			}
		},
	});
}
