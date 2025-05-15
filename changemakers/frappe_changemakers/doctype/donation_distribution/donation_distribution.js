// Copyright (c) 2025, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.ui.form.on("Donation Distribution", {
	refresh(frm) {
		if (!frm.doc.date) {
			frm.set_value("date", frappe.datetime.get_today());
		}
	},

	validate(frm) {
		let total = 0;

		(frm.doc.items || []).forEach((row) => {
			total += flt(row.amount);
		});

		if (!frm.doc.total_amount || frm.doc.total_amount == 0) {
			frm.set_value("total_amount", total);
		} else if (total > frm.doc.total_amount) {
			frappe.throw(
				`Total of distribution amounts (${total}) exceeds Total Amount (${frm.doc.total_amount})`
			);
		}
	},

	before_submit(frm) {
		let total = 0;

		(frm.doc.items || []).forEach((row) => {
			total += flt(row.amount);
		});

		if (flt(total) !== flt(frm.doc.total_amount)) {
			frappe.throw(
				`All funds must be fully allocated. Distributed amount (${total}) does not equal Total Amount (${frm.doc.total_amount}).`
			);
		}
	},
});

frappe.ui.form.on("Donation Distribution Item", {
	amount(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const total = frm.doc.total_amount || 0;

		if (total > 0) {
			row.percentage = flt((row.amount / total) * 100, 2);
			frm.refresh_field("items");
		}
	},

	percentage(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const total = frm.doc.total_amount || 0;

		if (total > 0) {
			row.amount = flt((row.percentage / 100) * total, 2);
			frm.refresh_field("items");
		}
	},
});
