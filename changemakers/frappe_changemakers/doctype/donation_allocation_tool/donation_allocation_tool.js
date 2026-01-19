// Copyright (c) 2026, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.ui.form.on("Donation Allocation Tool", {
	setup: function (frm) {
		frm.trigger("set_query");
		frm.trigger("set_allocation_defaults");
		frm.events.setup_beneficiary_filter_group(frm);
	},

	refresh: function (frm) {
		frm.page.clear_indicator();
		frm.disable_save();
		frm.trigger("render_custom_buttons");
		frm.trigger("get_beneficiaries");
		frm.trigger("set_primary_action");
	},

	render_custom_buttons: function (frm) {
		const $wrapper = frm
			.get_field("beneficiaries")
			.$wrapper.find(".grid-heading-row");
		$wrapper.find(".custom-table-actions").remove();
		const $btn_container = $(`
            <div class="custom-table-actions" style="margin-bottom:10px;display:flex;gap:10px;">
                <button class="btn btn-primary btn-sm btn-download-template">
                    <i class="fa fa-download"></i> ${__("Download Template")}
                </button>
                <button class="btn btn-primary btn-sm btn-upload-list">
                    <i class="fa fa-upload"></i> ${__("Upload List")}
                </button>
            </div>
        `).prependTo(frm.get_field("beneficiaries").$wrapper);
		$btn_container
			.find(".btn-download-template")
			.click(() => frm.trigger("download_template_dialog"));
		$btn_container
			.find(".btn-upload-list")
			.click(() => frm.trigger("upload_list"));
	},

	download_template_dialog: function (frm) {
		const d = new frappe.ui.Dialog({
			title: __("Select Template Format"),
			fields: [
				{
					label: __("Format"),
					fieldname: "format",
					fieldtype: "Select",
					options: ["CSV", "Excel"],
					default: "Excel",
				},
			],
			primary_action_label: __("Download"),
			primary_action(values) {
				frm.events.download_beneficiary_template(
					frm,
					values.format.toLowerCase()
				);
				d.hide();
			},
		});
		d.show();
	},

	download_beneficiary_template: function (frm, type) {
		frm.call({
			method: "download_beneficiary_template",
			doc: frm.doc,
			args: { file_type: type || "csv" },
			freeze: true,
			freeze_message: __("Generating Template..."),
			callback: function (r) {
				if (r.message) {
					const link = document.createElement("a");
					link.href = r.message;
					link.download = "";
					document.body.appendChild(link);
					link.click();
					document.body.removeChild(link);
				} else {
					frappe.msgprint(__("Failed to generate template."));
				}
			},
			error: function (err) {
				frappe.msgprint(__("Failed to generate template."));
				console.error(err);
			},
		});
	},
	upload_list: function (frm) {
		new frappe.ui.FileUploader({
			allow_multiple: false,
			on_success: (file) => {
				frm.call({
					method: "upload_beneficiary_list",
					doc: frm.doc,
					args: { file_url: file.file_url },
					freeze: true,
					freeze_message: __("Processing file..."),
					callback: function (r) {
						if (r.message) {
							frm.clear_table("beneficiaries");
							r.message.forEach((d) => {
								let row = frm.add_child("beneficiaries");
								Object.assign(row, d);
							});
							frm.refresh_field("beneficiaries");
							update_total_amount(frm);
						}
					},
				});
			},
			restrictions: { allowed_file_types: [".csv", ".xlsx", ".xls"] },
		});
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
				if (!row.amount || row.amount == 0)
					frappe.model.set_value(
						row.doctype,
						row.name,
						"amount",
						frm.doc.amount
					);
			});
			frm.refresh_field("beneficiaries");
			update_total_amount(frm);
		}
	},

	set_allocation_defaults(frm) {
		frm.set_value({
			from_date: frappe.datetime.get_today(),
			company: frappe.defaults.get_default("company"),
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
			if (r.message)
				r.message.forEach((d) => {
					let row = frm.add_child("beneficiaries");
					row.beneficiary = d.name;
					row.beneficiary_no = d.beneficiary_no;
					row.beneficiary_name = d.full_name;
					row.collector = d.collector;
					row.household_size = d.household_size;
					if (frm.doc.allocation_type === "Cash")
						row.amount = frm.doc.amount || 0;
				});
			frm.refresh_field("beneficiaries");
			update_total_amount(frm);
		});
	},

	set_query(frm) {
		frm.set_query("branch", () => ({
			filters: { company: frm.doc.company },
		}));
	},

	set_primary_action(frm) {
		frm.page.set_primary_action(__("Allocate Beneficiaries"), () =>
			frm.trigger("allocate_beneficiaries")
		);
	},

	allocate_beneficiaries(frm) {
		if (!frm.doc.beneficiaries || frm.doc.beneficiaries.length === 0) {
			frappe.msgprint(__("No beneficiaries loaded"));
			return;
		}
		const selected_beneficiaries = frm.doc.beneficiaries
			.filter((row) => row.__checked)
			.map((row) => ({
				beneficiary: row.beneficiary,
				amount: row.amount,
			}));
		if (!selected_beneficiaries.length) {
			frappe.msgprint(
				__("Please select beneficiaries using the checkboxes.")
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
							if (item[3]) filters.push(item.slice(1, 4));
							return filters;
						}, []);
					frm.trigger("get_beneficiaries");
				},
			});
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
		if (frm.doc.allocation_type === "Cash")
			frappe.model.set_value(cdt, cdn, "amount", frm.doc.amount || 0);
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
