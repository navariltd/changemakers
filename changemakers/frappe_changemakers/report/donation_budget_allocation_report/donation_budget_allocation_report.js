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
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		const blankFields = ["amount", "allocation_amount", "budget_amount"];

		if (
			(blankFields.includes(column.fieldname) ||
				/\d+$/.test(column.fieldname)) &&
			data &&
			(data[column.fieldname] === "" || data[column.fieldname] === "0")
		) {
			return " ";
		}

		return value;
	},
};
