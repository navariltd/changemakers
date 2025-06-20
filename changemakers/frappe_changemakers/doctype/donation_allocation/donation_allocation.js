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

		// Setup account query for all existing rows
		setup_account_query(frm);
	},

	donation_total_paid_amount(frm) {
		calculate_unallocated_amount(frm);
	},

	donation(frm) {
		calculate_unallocated_amount(frm);
	},

});

function setup_account_query(frm) {
	if (!frm.fields_dict.items) return;

	frm.fields_dict.items.grid.grid_rows.forEach(function (row) {
		setup_account_query_for_row(frm, row.doc.doctype, row.doc.name);
	});
}

function setup_account_query_for_row(frm, cdt, cdn) {
	let grid = frm.fields_dict.items.grid;
	let row = locals[cdt][cdn];

	if (!grid || !row) return;

	let account_field = grid.get_field("account", cdn);

	if (!account_field) return;

	let filters = { name: ["in", []] };

	if (row.recipient_type === "Budget" && row.recipient) {
		frappe
			.call({
				method: "changemakers.frappe_changemakers.doctype.donation_allocation.donation_allocation.get_budget_accounts",
				args: {
					budget_name: row.recipient,
				},
			})
			.then((r) => {
				if (r.message) {
					filters = { name: ["in", r.message] };
				}

				account_field.get_query = function () {
					return { filters };
				};

				frm.fields_dict.items.grid.refresh();
			})
			.catch((err) => {
				console.error("Error fetching budget accounts:", err);
			});
		}
}



frappe.ui.form.on("Donation Allocation Item", {
	recipient_type: function (frm, cdt, cdn) {
		setup_account_query_for_row(frm, cdt, cdn);
		refresh_field("account", cdn, "items");
	},

	recipient: function (frm, cdt, cdn) {
		setup_account_query_for_row(frm, cdt, cdn);
		refresh_field("account", cdn, "items");
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
