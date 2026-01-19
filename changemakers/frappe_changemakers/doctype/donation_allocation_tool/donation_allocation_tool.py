# Copyright (c) 2026, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
import csv
from io import StringIO, BytesIO
from frappe.utils.xlsxutils import make_xlsx


class DonationAllocationTool(Document):

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



    @frappe.whitelist()
    def download_beneficiary_template(self, file_type="csv"):

        meta = frappe.get_meta("Donation Allocation Beneficiary")
        headers = [
            f.fieldname for f in meta.fields
            if f.fieldtype not in ("Section Break", "Column Break", "HTML", "Table")
            and f.fieldname not in ("name", "parent", "parentfield", "parenttype", "idx", "creation", "modified", "owner", "docstatus")
        ]

        sample_rows = []
        for row in (self.beneficiaries or [])[:5]:
            sample_rows.append([getattr(row, h, "") or "" for h in headers])

        if not sample_rows:
            sample_rows = [["" for _ in headers] for _ in range(5)]

        if file_type.lower() == "csv":
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            writer.writerows(sample_rows)
            filedata = output.getvalue().encode("utf-8")
            filename = "donation_beneficiary_template.csv"

        elif file_type.lower() in ["xlsx", "excel"]:
            data = [headers] + sample_rows
            xlsx_file = make_xlsx(data, sheet_name="Beneficiaries")
            filedata = xlsx_file.getvalue()
            filename = "donation_beneficiary_template.xlsx"

        else:
            frappe.throw(_("Invalid file type. Only CSV or Excel supported"))

        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": filename,
            "attached_to_doctype": "Donation Allocation Tool",
            "attached_to_name": self.name or "",
            "content": filedata,
            "is_private": 0,
        })
        file_doc.insert(ignore_permissions=True)
        return file_doc.file_url


