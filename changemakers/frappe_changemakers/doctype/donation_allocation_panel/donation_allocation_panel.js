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

	collector: function (frm) {
		frm.trigger("get_beneficiaries");
	},
	gender: function (frm) {
		frm.trigger("get_beneficiaries");
	},
	name: function (frm) {
		frm.trigger("get_beneficiaries");
	},
	household_size: function (frm) {
		frm.trigger("get_beneficiaries");
	},
	from_date: function (frm) {
		frm.trigger("get_beneficiaries");
	},
	to_date: function (frm) {
		frm.trigger("get_beneficiaries");
	},

	set_allocation_defaults(frm) {
		frm.set_value({
			from_date: frappe.datetime.get_today(),
			to_date: null,
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
			frm.beneficiaries_datatable =
				frm.events.render_beneficiaries_datatable(frm, r.message);
		});
	},

	render_beneficiaries_datatable(frm, beneficiaries) {
		const columns = frm.events.get_beneficiaries_datatable_columns();

		const wrapper = frm.get_field("beneficiaries_html").$wrapper;
		wrapper.empty();

		if (!beneficiaries || beneficiaries.length === 0) {
			wrapper.html(`
				<div class="text-muted text-center" style="padding: 40px;">
					<i class="fa fa-users fa-3x" style="opacity: 0.3; margin-bottom: 15px;"></i>
					<p>${__("No beneficiaries found matching the criteria")}</p>
					<small>${__("Adjust your filters to find eligible beneficiaries")}</small>
				</div>
			`);
			return;
		}

		return new frappe.DataTable(wrapper[0], {
			columns: columns,
			data: beneficiaries,
			checkboxColumn: true,
			layout: "fluid",
			cellHeight: 40,
			noDataMessage: __("No beneficiaries found matching the criteria"),
		});
	},

	get_beneficiaries_datatable_columns() {
		return [
			{
				name: "name",
				id: "name",
				content: __("Beneficiary ID"),
				width: 120,
				format: (value, row, column, data) => {
					return value
						? `<a href="/app/beneficiary/${data.name}" target="_blank">${value}</a>`
						: "";
				},
			},
			{
				name: "full_name",
				id: "full_name",
				content: __("Name"),
				width: 180,
				format: (value, row, column, data) => {
					return value
						? `<a href="/app/beneficiary/${data.name}" target="_blank">${value}</a>`
						: "";
				},
			},
			{
				name: "collector",
				id: "collector",
				content: __("Collector"),
				width: 150,
			},
			{ name: "gender", id: "gender", content: __("Gender"), width: 100 },
			{
				name: "household_size",
				id: "household_size",
				content: __("Household Size"),
				width: 120,
			},
		].map((x) => ({
			...x,
			editable: false,
			focusable: false,
			dropdown: false,
			align: "left",
		}));
	},

	set_query(frm) {
		frm.set_query("branch", function () {
			return { filters: { company: frm.doc.company } };
		});
	},

	set_primary_action(frm) {
		frm.page.set_primary_action(__("Allocate Beneficiaries"), () => {
			frm.trigger("allocate_beneficiaries");
		});
	},

	allocate_beneficiaries(frm) {
		if (!frm.beneficiaries_datatable) {
			frappe.msgprint(__("No beneficiaries loaded"));
			return;
		}

		const required_fields = frappe
			.get_meta(frm.doc.doctype)
			.fields.filter((f) => f.reqd)
			.map((f) => f.fieldname);

		const missing_fields = required_fields.filter((f) => !frm.doc[f]);
		if (missing_fields.length) {
			frappe.msgprint({
				title: __("Missing Required Fields"),
				message: __(
					"Please ensure the following required fields are filled: {0}",
					[missing_fields.join(", ")]
				),
				indicator: "error",
			});
			return;
		}

		if (!frm.doc.items || frm.doc.items.length === 0) {
			frappe.msgprint({
				title: __("No Items Found"),
				message: __(
					"Please add at least one item to allocate donations."
				),
				indicator: "error",
			});
			return;
		}

		const check_map = frm.beneficiaries_datatable.rowmanager.checkMap;
		const selected_beneficiaries = [];

		check_map.forEach((is_checked, idx) => {
			if (is_checked) {
				selected_beneficiaries.push(
					frm.beneficiaries_datatable.datamanager.data[idx].name
				);
			}
		});

		if (!selected_beneficiaries.length) {
			frappe.msgprint(__("No beneficiaries selected"));
			return;
		}

		frappe.confirm(
			__("Allocate donations to {0} beneficiary(ies)?", [
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
			if (r.message.failed && !r.message.success) return;
			frappe.msgprint(__("Donation allocation completed"));
			frm.trigger("get_beneficiaries");
		});
	},
});

frappe.ui.form.on("Donation Allocation Item", {
	rate: function (frm, cdt, cdn) {
		update_total_amount(frm);
	},

	amount: function (frm, cdt, cdn) {
		update_total_amount(frm);
	},

	items_add: function (frm, cdt, cdn) {
		update_total_amount(frm);
	},

	items_remove: function (frm, cdt, cdn) {
		update_total_amount(frm);
	},
});

function update_total_amount(frm) {
	let total = 0;
	(frm.doc.items || []).forEach((row) => {
		row.amount = flt(row.rate || 0) * flt(row.qty || 0);
		total += flt(row.amount || 0);
	});
	frm.set_value("total_amount", total);
}
