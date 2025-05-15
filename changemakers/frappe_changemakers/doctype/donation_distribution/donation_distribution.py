# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class DonationDistribution(Document):
	def before_submit(self):
		submitted_distributions = frappe.get_all(
			"Donation Distribution",
			filters={
				"donation": self.donation,
				"docstatus": 1,
				"name": ["!=", self.name], 
			},
			fields=["total_amount"]
		)

		total_distributed = sum([d.total_amount for d in submitted_distributions])
		new_total = total_distributed + self.total_amount

		donation_doc = frappe.get_doc("Donation", self.donation)

		if new_total > donation_doc.amount:
			frappe.db.set_value("Donation", self.donation, "amount_distributed", total_distributed, update_modified=False)
			frappe.throw(
				f"Total distributed amount ({new_total}) exceeds the original Donation amount ({donation_doc.amount})."
			)
		else:
			frappe.db.set_value("Donation", self.donation, "amount_distributed", new_total, update_modified=False)

