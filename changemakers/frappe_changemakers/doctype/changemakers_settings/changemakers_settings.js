// Copyright (c) 2023, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.ui.form.on("Changemakers Settings", {
	setup: function (frm) {
		frm.set_query(
			"account",
			"beneficiary_accounts",
			function (doc, cdt, cdn) {
				let d = locals[cdt][cdn];
				return {
					filters: {
						account_type: "Payable",
						root_type: "Liability",
						company: d.company,
						is_group: 0,
					},
				};
			},
		);
	},

	refresh(frm) {
		// TODO: Add a progress bar later
		const button = frm.add_custom_button(
			"Import Indian District List",
			(frm) => {
				frappe
					.call({
						method: "changemakers.utils.data.scrap_and_import_india_district_list",
						btn: button,
					})
					.then(() => {
						frappe.show_alert("Import Complete");
					});
			},
		);
	},
});
