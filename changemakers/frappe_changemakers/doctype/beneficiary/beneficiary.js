// Copyright (c) 2022, hussain@frappe.io and contributors
// For license information, please see license.txt

frappe.ui.form.on("Beneficiary", {
	refresh(frm) {
		frm.toggle_display("address_html", !frm.is_new());
		frm.toggle_display("contact_html", !frm.is_new());

		if (!frm.is_new()) {
			frappe.contacts.render_address_and_contact(frm);

			// Check for existing cases
			check_existing_cases(frm.doc.name).then((case_count) => {
				// Auto-endorsement logic for Waitlist status
				if (frm.doc.status === "Waitlist") {
					check_local_admin_acknowledgement_case(frm.doc.name).then(
						(has_closed_case) => {
							if (has_closed_case) {
								frm.set_value("status", "Endorsed");
								frm.save_or_update();
							}
						}
					);
				}

				// Bereavement logic for Active status
				if (
					frm.doc.status === "Active" ||
					frm.doc.status === "Bereavement Pending"
				) {
					check_bereavement_case(frm.doc.name).then(
						(bereavementStatus) => {
							if (bereavementStatus === "open") {
								frm.set_value("status", "Bereavement Pending");
								frm.save_or_update();
							} else if (bereavementStatus === "closed") {
								frm.set_value("status", "Deceased");

								frm.save_or_update();
							}
						}
					);
				}

				if (frm.doc.status === "Waitlist" && case_count === 0) {
					frm.add_custom_button(
						"Local Administrator Acknowledgement",
						() => {
							create_case(
								"Local Administration Acknowledgement",
								frm
							);
						},
						"Create"
					);
				}

				if (frm.doc.status === "Active") {
					frm.add_custom_button(
						"Bereavement",
						() => {
							create_case("Bereavement", frm);
						},
						"Create"
					);

					frm.add_custom_button(
						"Incident",
						() => {
							create_case("Incident", frm);
						},
						"Create"
					);
				}
			});
		}
	},
	setup: (frm) => {
		changemakers.utils.set_query_for_district(frm);
		changemakers.utils.set_query_for_zone(frm);
		changemakers.utils.set_query_for_ward(frm);
	},
	state: changemakers.utils.handle_state_field,
	district: changemakers.utils.handle_district_field,
	zone: changemakers.utils.handle_zone_field,
	ward: changemakers.utils.handle_ward_field,
	bottom_save_button: (frm) => {
		frm.save();
	},
});

// Helper function to create a new document with the beneficiary information
function create_case(docType, frm) {
	frappe.new_doc("Case", {
		beneficiary: frm.doc.name,
		type: docType,
	});
}

// Helper function to check if there are existing cases for a beneficiary
function check_existing_cases(beneficiary) {
	return frappe.db.count("Case", { filters: { beneficiary } });
}

// Helper function to check if there is a closed or solved "Local Administration Acknowledgement" case
function check_local_admin_acknowledgement_case(beneficiary) {
	return frappe.db
		.count("Case", {
			filters: {
				beneficiary: beneficiary,
				type: "Local Administration Acknowledgement",
				status: ["in", ["Solved", "Closed"]],
			},
		})
		.then((count) => count > 0);
}

// Helper function to check the status of a "Bereavement" case
function check_bereavement_case(beneficiary) {
	return frappe.db
		.get_list("Case", {
			filters: {
				beneficiary: beneficiary,
				type: "Bereavement",
			},
			fields: ["status"],
			limit: 1,
			order_by: "creation desc",
		})
		.then((cases) => {
			if (cases.length > 0) {
				return cases[0].status === "Closed" ? "closed" : "open";
			}
			return null;
		});
}
