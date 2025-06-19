# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from frappe import _

class DonationAllocation(Document):
	def validate(self):
		if not self.date:
			self.date = nowdate()

		total_amount = 0.0
		for item in self.items:
			total_amount += flt(item.amount)
		self.total_amount = total_amount

		if total_amount > 0:
			for item in self.items:
				item.percentage = flt((item.amount / total_amount) * 100, 2)

		self.validate_total_against_donation()

	def before_submit(self):
		self.validate_total_against_donation()
		add_budget_allocations_from_doc(self)

	def validate_total_against_donation(self):
		donation_doc = frappe.get_doc("Donation", self.donation)
		total_distributed = get_total_allocated_amount(self.donation, exclude_allocation=self.name)
		new_total = total_distributed + self.total_amount

		if new_total > donation_doc.amount:
			frappe.db.set_value("Donation", self.donation, "amount_distributed", total_distributed, update_modified=False)
			frappe.throw(
				_("Total distributed amount ({0}) exceeds the original Donation amount ({1}).").format(new_total, donation_doc.amount)
			)
		else:
			frappe.db.set_value("Donation", self.donation, "amount_distributed", new_total, update_modified=False)


@frappe.whitelist()
def get_total_allocated_amount(donation_name, exclude_allocation=None):
	"""
	Returns the total amount already allocated (submitted) for a given Donation.
	Optionally exclude a specific Donation Allocation document (e.g., current draft).
	"""
	filters = {
		"donation": donation_name,
		"docstatus": 1,
	}
	if exclude_allocation:
		filters["name"] = ["!=", exclude_allocation]

	allocations = frappe.get_all("Donation Allocation", filters=filters, fields=["total_amount"])
	return sum(flt(alloc.total_amount) for alloc in allocations)


def add_budget_allocations_from_doc(doc):
	"""
	Inserts new rows into the 'donation_allocations' child table of Budget documents
	for items in Donation Allocation where recipient_type == 'Budget'.
	"""
	for item in doc.items:
		if item.recipient_type == "Budget":
			frappe.get_doc({
				"doctype": "Budget Donation Allocation Item",  
				"parent": item.recipient,                
				"parenttype": "Budget",
				"parentfield": "donation_allocations",   
				"donation_allocation": doc.name,
				"donation": doc.donation,
				"donor": doc.donor,
				"amount": item.amount
			}).insert(ignore_permissions=True)
