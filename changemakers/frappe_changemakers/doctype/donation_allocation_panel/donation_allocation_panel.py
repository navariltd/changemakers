# Copyright (c) 2026, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class DonationAllocationPanel(Document):

    @frappe.whitelist()
    def get_beneficiaries(self, advanced_filters=None):
        """
        Return list of beneficiaries matching filters for datatable display.
        Filters can include: company, branch, collector, gender, household_size, beneficiary_no
        """
        if isinstance(advanced_filters, str):
            advanced_filters = json.loads(advanced_filters)

        query_filters = {}
        for key in ["collector", "gender", "beneficiary_no"]:
            if getattr(self, key, None) not in (None, ""):
                query_filters[key] = getattr(self, key)
        
        household_size = getattr(self, "household_size", None)
        if household_size and household_size > 0:
            query_filters["household_size"] = household_size

        if advanced_filters:
            for key, value in advanced_filters.items():
                if value not in (None, ""):
                    query_filters[key] = value

        beneficiaries = frappe.get_all(
            "Beneficiary",
            filters=query_filters,
            fields=[
                "beneficiary_no",
                "full_name",
                "collector",
                "gender",
                "household_size",
                "name",
            ],
            order_by="full_name asc",
        )

        return beneficiaries

    @frappe.whitelist()
    def allocate_beneficiaries(self, beneficiaries):
        if isinstance(beneficiaries, str):
            beneficiaries = json.loads(beneficiaries)

        if not beneficiaries:
            frappe.throw("No beneficiaries selected for allocation")

        for ben_no in beneficiaries:
            doc = frappe.get_doc(
                {
                    "doctype": "Donation Allocation",
                    "recipient_type": "Beneficiary",
                    "recipient": ben_no,
                    "project": self.project,
                    "company": self.company,
                    "cost_center": self.cost_center,
                    "branch": self.branch,
                    "donation": self.donation,
                    "donor": self.donor,
                    "from_date": self.from_date,
                    "to_date": self.to_date,
                    "items": self.items,
                }
            )
            doc.insert(ignore_permissions=True)

        frappe.msgprint(f"Allocated donations to {len(beneficiaries)} beneficiaries")
        return {"success": True}
