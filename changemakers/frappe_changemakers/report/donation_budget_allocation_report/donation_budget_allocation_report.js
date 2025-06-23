// Copyright (c) 2025, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.query_reports["Donation Budget Allocation Report"] = {
	filters: [
		{
			fieldname: "budget_against",
			label: __("Budget Against"),
			fieldtype: "Select",
			options: [
				"Donor",
				"Project",
				"Employee",
				"Task",
				"Cost Center",
				"Program",
			],
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			default: frappe.defaults.get_user_default("fiscal_year"),
		},
	],
};
