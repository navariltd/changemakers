frappe.ui.form.on("Stock Entry", {
	setup: function (frm) {
		setup_beneficiary_query(frm);
		setup_collector_query(frm);
	},

	refresh: function (frm) {
		if (frm.doc.collector && frm.doc.beneficiary) {
			auto_set_collector(frm);
		}
	},

	project: function (frm) {
		load_bom_items(frm);
		setup_beneficiary_query(frm);
	},

	stock_entry_type: function (frm) {
		load_bom_items(frm);
		setup_beneficiary_query(frm);
	},

	custom_beneficiary: function (frm) {
		setup_collector_query(frm);
	},

	before_submit: function (frm) {
		if (
			frm.doc.stock_entry_type == "Distribution" &&
			!frm.doc.beneficiary_signature
		) {
			frappe.throw(
				__("The beneficiary or collector signature is mandatory.")
			);
		}
	},
});

function setup_beneficiary_query(frm) {
	const project = frm.doc.project;

	if (project && frm.doc.stock_entry_type == "Distribution") {
		frappe.call({
			method: "changemakers.frappe_changemakers.overrides.stock_entry_query.get_filtered_beneficiaries",
			args: {
				project: project,
			},
			callback: function (r) {
				if (r.message) {
					const beneficiary_list = r.message;
					frm.set_query("custom_beneficiary", function () {
						return {
							filters: [["name", "in", beneficiary_list]],
						};
					});
				}
			},
		});
	}
}

function setup_collector_query(frm) {
	if (frm.doc.custom_beneficiary) {
		frappe.call({
			method: "changemakers.frappe_changemakers.overrides.stock_entry_query.get_collector",
			args: { beneficiary: frm.doc.custom_beneficiary },
			callback: function (r) {
				if (r.message) {
					frm.set_value("collector", r.message[0]);
					frm.set_query("collector", function () {
						return {
							filters: [["name", "in", r.message]],
						};
					});
				}
			},
		});
	}
}

function load_bom_items(frm) {
	if (frm.doc.project && frm.doc.stock_entry_type == "Distribution") {
		frappe.call({
			method: "changemakers.frappe_changemakers.overrides.stock_entry_query.get_bom_items",
			args: { project: frm.doc.project },
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					frm.clear_table("items");

					$.each(r.message, function (_, item) {
						let d = frappe.model.add_child(
							frm.doc,
							"Stock Entry Detail",
							"items"
						);
						d.item_code = item.item_code;
						d.item_name = item.item_name;
						d.item_group = item.item_group;
						d.s_warehouse = frm.doc.source_warehouse;
						d.t_warehouse = frm.doc.target_warehouse;
						d.uom = item.stock_uom;
						d.stock_uom = item.stock_uom;
						d.conversion_factor = item.conversion_factor
							? item.conversion_factor
							: 1;
						d.qty = item.qty;
						d.transfer_qty = item.stock_qty;
						d.expense_account = item.expense_account;
					});

					frm.refresh_field("items");
				} else {
					frappe.throw(
						__("No BOM items found for the selected project.")
					);
				}
			},
		});
	}
}
