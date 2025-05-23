# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate

class DonationAllocation(Document):
	def validate(self):
		# Set date if not already set
		if not self.date:
			self.date = nowdate()

		total_amount = 0.0

		# Sum up total amount from the items
		for item in self.items:
			total_amount += flt(item.amount)

		# Set total_amount field to the sum of all item amounts
		self.total_amount = total_amount

		# Calculate and set percentage for each item
		if total_amount > 0:
			for item in self.items:
				item.percentage = flt((item.amount / total_amount) * 100, 2)
				
	def before_submit(self):
		submitted_distributions = frappe.get_all(
			"Donation Allocation",
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

