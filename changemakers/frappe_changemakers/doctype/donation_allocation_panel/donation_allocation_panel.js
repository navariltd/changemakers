// Copyright (c) 2026, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.ui.form.on("Donation Allocation Panel", {
	setup: function (frm) {
		frm.trigger("set_query");
		frm.trigger("set_allocation_defaults");
		frm.events.setup_beneficiary_filter_group(frm);
	},

	refresh: function (frm) {
		frm.page.clear_indicator();
		frm.disable_save();
		frm.trigger("get_beneficiaries");
		frm.trigger("set_primary_action");
	},

	collector: (frm) => frm.trigger("get_beneficiaries"),
	gender: (frm) => frm.trigger("get_beneficiaries"),
	name: (frm) => frm.trigger("get_beneficiaries"),
	household_size: (frm) => frm.trigger("get_beneficiaries"),
	from_date: (frm) => frm.trigger("get_beneficiaries"),
	to_date: (frm) => frm.trigger("get_beneficiaries"),

	amount: function (frm) {
		if (frm.doc.allocation_type === "Cash" && frm.doc.amount > 0) {
			frm.doc.beneficiaries.forEach((row) => {
				if (!row.amount || row.amount == 0) {
					frappe.model.set_value(
						row.doctype,
						row.name,
						"amount",
						frm.doc.amount
					);
				}
			});
			frm.refresh_field("beneficiaries");
		}
	},

	set_allocation_defaults(frm) {
		frm.set_value({
			from_date: frappe.datetime.get_today(),
			company: frappe.defaults.get_default("company"),
		});
	},

	setup_beneficiary_filter_group(frm) {
		const filter_wrapper = frm.fields_dict.filter_list.$wrapper;
		filter_wrapper.empty();

		frappe.model.with_doctype("Beneficiary", () => {
			frm.filter_list = new frappe.ui.FilterGroup({
				parent: filter_wrapper,
				doctype: "Beneficiary",
				on_change: () => {
					frm.advanced_filters = frm.filter_list
						.get_filters()
						.reduce((filters, item) => {
							if (item[3]) {
								filters.push(item.slice(1, 4));
							}
							return filters;
						}, []);
					frm.trigger("get_beneficiaries");
				},
			});
		});
	},

	get_beneficiaries(frm) {
		frm.call({
			method: "get_beneficiaries",
			doc: frm.doc,
			args: {
				advanced_filters: JSON.stringify(frm.advanced_filters || {}),
			},
		}).then((r) => {
			frm.clear_table("beneficiaries");
			if (r.message) {
				r.message.forEach((d) => {
					let row = frm.add_child("beneficiaries");
					row.beneficiary = d.name;
					row.beneficiary_no = d.beneficiary_no;
					row.beneficiary_name = d.full_name;
					row.collector = d.collector;
					row.household_size = d.household_size;
					if (frm.doc.allocation_type === "Cash") {
						row.amount = frm.doc.amount || 0;
					}
				});
			}
			frm.refresh_field("beneficiaries");
		});
	},

	set_query(frm) {
		frm.set_query("branch", () => ({
			filters: { company: frm.doc.company },
		}));
	},

	set_primary_action(frm) {
		frm.page.set_primary_action(__("Allocate Beneficiaries"), () => {
			frm.trigger("allocate_beneficiaries");
		});
	},

	allocate_beneficiaries(frm) {
		if (!frm.doc.beneficiaries || frm.doc.beneficiaries.length === 0) {
			frappe.msgprint(__("No beneficiaries loaded"));
			return;
		}

		const required_fields = frappe
			.get_meta(frm.doc.doctype)
			.fields.filter((f) => f.reqd)
			.map((f) => f.fieldname);

		const missing_fields = required_fields.filter((f) => !frm.doc[f]);
		if (missing_fields.length) {
			frappe.msgprint(
				__("Missing fields: {0}", [missing_fields.join(", ")])
			);
			return;
		}

		if (
			frm.doc.allocation_type == "Items" &&
			(!frm.doc.items || frm.doc.items.length === 0)
		) {
			frappe.msgprint(__("Please add at least one item."));
			return;
		}

		const selected_beneficiaries = frm.doc.beneficiaries
			.filter((row) => row.__checked)
			.map((row) => row.beneficiary);

		if (!selected_beneficiaries.length) {
			frappe.msgprint(
				__(
					"Please select beneficiaries from the table using the checkboxes."
				)
			);
			return;
		}

		frappe.confirm(
			__("Allocate donations to {0} selected beneficiary(ies)?", [
				selected_beneficiaries.length,
			]),
			() =>
				frm.events.bulk_allocate_beneficiaries(
					frm,
					selected_beneficiaries
				)
		);
	},

	bulk_allocate_beneficiaries(frm, beneficiaries) {
		frm.call({
			method: "allocate_beneficiaries",
			doc: frm.doc,
			args: { beneficiaries: JSON.stringify(beneficiaries) },
			freeze: true,
			freeze_message: __("Allocating Donations"),
		}).then((r) => {
			if (r.message && !r.message.failed) {
				frappe.msgprint(__("Donation allocation completed"));
				frm.trigger("get_beneficiaries");
			}
		});
	},
});

frappe.ui.form.on("Donation Allocation Item", {
	rate: (frm) => update_items_total_amount(frm),
	qty: (frm) => update_items_total_amount(frm),
	items_add: (frm) => update_items_total_amount(frm),
	items_remove: (frm) => update_items_total_amount(frm),
});

frappe.ui.form.on("Donation Allocation Beneficiary", {
	amount: (frm) => update_total_amount(frm),
	beneficiaries_add: function (frm, cdt, cdn) {
		if (frm.doc.allocation_type === "Cash") {
			frappe.model.set_value(cdt, cdn, "amount", frm.doc.amount || 0);
		}
		update_total_amount(frm);
	},
	beneficiaries_remove: (frm) => update_total_amount(frm),
});

function update_total_amount(frm) {
	let total = 0;
	(frm.doc.beneficiaries || []).forEach((row) => {
		total += flt(row.amount || 0);
	});
	frm.set_value("total_amount", total);
}

function update_items_total_amount(frm) {
	let total = 0;
	(frm.doc.items || []).forEach((row) => {
		row.amount = flt(row.rate || 0) * flt(row.qty || 0);
		total += flt(row.amount || 0);
	});
	frm.set_value("total_items_amount", total);
}
