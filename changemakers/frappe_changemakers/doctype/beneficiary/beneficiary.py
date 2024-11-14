# Copyright (c) 2022, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe.contacts.address_and_contact import load_address_and_contact

from changemakers.utils.data import is_valid_indian_phone_number


class Beneficiary(Document):
	def before_save(self):
		self.set_created_by()
		self.full_name = f"{self.first_name} {self.last_name or ''}"

	def validate(self):
		self.validate_age()
		# self.validate_phone_number_fields()

	def validate_age(self):
		if not (self.age < 120):
			frappe.throw(f"Value of {frappe.bold('Age')} should be less than 120!")

	def validate_phone_number_fields(self):
		if self.poc_phone and not is_valid_indian_phone_number(self.poc_phone):
			frappe.throw(
				f"Value of {frappe.bold('POC Phone')} is not a valid Indian Phone number"
			)

		if self.phone_number and not is_valid_indian_phone_number(self.phone_number):
			frappe.throw(f"Value of {frappe.bold('Phone')} is not a valid Indian Phone number")

	def set_created_by(self):
		if not self.created_by:
			owner = frappe.db.get_value("User", self.owner, "full_name")
			self.created_by = owner
   
	def onload(self):
		load_address_and_contact(self)