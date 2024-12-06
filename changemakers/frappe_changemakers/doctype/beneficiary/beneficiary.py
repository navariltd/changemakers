# Copyright (c) 2022, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.contacts.address_and_contact import load_address_and_contact
from frappe.model.document import Document
from frappe.query_builder import Field
from frappe.utils import cint

from changemakers.utils.data import is_valid_indian_phone_number

class Beneficiary(Document):
    def before_save(self):
        self.set_created_by()
        self.full_name = f"{self.first_name} {self.last_name or ''}"

    def validate(self):
        self.validate_age()
        if self.status == "Active" and self.recruitment_phase and not self.beneficiary_no:
            self.validate_available_slots()
            self.beneficiary_no = generate_beneficiary_no(self)
        # self.validate_phone_number_fields()
        
    def validate_available_slots(self):
        if not self.recruitment_phase:
            return
        recruitment_phase = frappe.get_doc("Recruitment Phase", self.recruitment_phase)

        available_slots = recruitment_phase.available_slots
        if available_slots <= 0:
            frappe.throw(
                _(f"No available slots in {self.recruitment_phase}.")
            )

    def validate_age(self):
        if not (self.age < 120):
            frappe.throw(f"Value of {frappe.bold('Age')} should be less than 120!")

    def validate_phone_number_fields(self):
        if self.poc_phone and not is_valid_indian_phone_number(self.poc_phone):
            frappe.throw(
                f"Value of {frappe.bold('POC Phone')} is not a valid Indian Phone number"
            )

        if self.phone_number and not is_valid_indian_phone_number(self.phone_number):
            frappe.throw(
                f"Value of {frappe.bold('Phone')} is not a valid Indian Phone number"
            )

    def set_created_by(self):
        if not self.created_by:
            owner = frappe.db.get_value("User", self.owner, "full_name")
            self.created_by = owner

    def onload(self):
        load_address_and_contact(self)


def generate_beneficiary_no(doc):
    recruitment_phase = frappe.get_doc("Recruitment Phase", doc.recruitment_phase)
    
    Beneficiary = frappe.qb.DocType("Beneficiary")
    beneficiary_no_field = Field("beneficiary_no")
    
    max_number_query = (
        frappe.qb.from_(Beneficiary)
        .select(beneficiary_no_field)
        .where(
            (Beneficiary.recruitment_phase == doc.recruitment_phase) &
            (Beneficiary.beneficiary_no.like(f"{recruitment_phase.beneficiary_number_series}%"))
        )
    )

    beneficiary_nos = frappe.db.sql(max_number_query, as_dict=False)

    numeric_parts = [
        cint(bn[0][-4:])  
        for bn in beneficiary_nos if bn[0][-4:].isdigit()
    ]

    last_number = max(numeric_parts, default=0)

    new_number = last_number + 1
    formatted_number = f"{new_number:04}"

    beneficiary_no = f"{recruitment_phase.beneficiary_number_series}{formatted_number}"

    return beneficiary_no
