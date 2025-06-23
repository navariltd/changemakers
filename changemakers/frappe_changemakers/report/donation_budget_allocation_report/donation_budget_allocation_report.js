// Copyright (c) 2025, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.query_reports["Donation Budget Allocation Report"] = {
	filters: [
		{
			fieldname: "budget_against",
			label: __("Budget Against"),
			fieldtype: "Select",
			options: [
				"", // Added an empty option to allow for no specific budget_against filter
				"Project",
				"Employee",
				"Task",
				"Cost Center",
				"Program",
			],
			// Added default value for "Budget Against" to "Project"
			default: "Project",
			// on_change: function () {
			//     // Get the current value of the "Budget Against" filter
			//     let budget_against_value = frappe.query_report.get_filter_value("budget_against");

			//     // Get a reference to the "Budget Against Docname" filter
			//     let budget_against_docname_filter = frappe.query_report.get_filter("budget_against_docname");

			//     // If "Budget Against" has a value, set options and make visible
			//     if (budget_against_value) {
			//         budget_against_docname_filter.df.options = budget_against_value;
			//         budget_against_docname_filter.df.fieldtype = "Link";
			//         budget_against_docname_filter.df.hidden = 0;
			//     } else {
			//         // If no "Budget Against" is selected, hide and clear the "Budget Against Docname" filter
			//         budget_against_docname_filter.df.hidden = 1;
			//         budget_against_docname_filter.df.options = "";
			//         budget_against_docname_filter.set_input("");
			//     }
			//     // // Refresh the filter to apply changes
			//     // budget_against_docname_filter.refresh();
			// }
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			depends_on: "eval:doc.budget_against == 'Project'", // Show only if "Budget Against" is "Project"
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			depends_on: "eval:doc.budget_against == 'Employee'", // Show only if "Budget Against" is "Employee"
		},
		{
			fieldname: "task",
			label: __("Task"),
			fieldtype: "Link",
			options: "Task",
			depends_on: "eval:doc.budget_against == 'Task'", // Show only if "Budget Against" is "Task"
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			depends_on: "eval:doc.budget_against == 'Cost Center'", // Show only if "Budget Against" is "Cost Center"
		},
		{
			fieldname: "program",
			label: __("Program"),
			fieldtype: "Link",
			options: "Program",
			depends_on: "eval:doc.budget_against == 'Program'", // Show only if "Budget Against" is "Program"
		},
		{
			fieldname: "budget_against_docname",
			label: __("Budget Against (Name)"),
			fieldtype: "Link",
			options: "", // Options will be set dynamically based on "Budget Against"
			hidden: 1, // Hidden by default
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year", // Ensure this is explicitly set if it's a Link field
			default: frappe.defaults.get_user_default("fiscal_year"),
		},
		{
			fieldname: "budget_name",
			label: __("Budget Name"),
			fieldtype: "Link",
			options: "Budget",
		},
		{
			fieldname: "budget_account",
			label: __("Budget Account"),
			fieldtype: "Link",
			options: "Account", // Assuming Budget Account links to Account doctype
		},
		{
			fieldname: "donor",
			label: __("Donor"),
			fieldtype: "Link",
			options: "Donor",
		},
		{
			fieldname: "donation",
			label: __("Donation"),
			fieldtype: "Link",
			options: "Donation",
			depends_on: "eval:doc.donor", // Make this filter dependent on the Donor filter
			get_query: function () {
				let donor = frappe.query_report.get_filter_value("donor");
				if (donor) {
					return {
						filters: {
							donor: donor,
						},
					};
				}
			},
		},
		{
			fieldname: "donation_allocation",
			label: __("Donation Allocation"),
			fieldtype: "Link",
			options: "Donation Allocation",
			depends_on: "eval:doc.donation", // Make this filter dependent on the Donation filter
			get_query: function () {
				let donation = frappe.query_report.get_filter_value("donation");
				if (donation) {
					return {
						filters: {
							donation: donation,
						},
					};
				}
			},
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
