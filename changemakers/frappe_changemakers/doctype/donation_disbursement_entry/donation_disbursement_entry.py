# Copyright (c) 2026, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today
import json
import csv
from io import StringIO, BytesIO
from frappe.utils.xlsxutils import make_xlsx

from ....utils.data import extract_data_from_file, get_doctype_headers

class DonationDisbursementEntry(Document):
    def before_save(self):
        total_amount = 0
        for row in self.beneficiaries or []:
            row.amount = (row.qty or 0) * (row.rate or 0)
            total_amount += row.amount or 0
        self.total_amount = total_amount

    @frappe.whitelist()
    def get_beneficiaries(self, advanced_filters=None):
        """
        Return list of beneficiaries matching filters for datatable display.
        """
        beneficiaries = frappe.get_list(
            "Beneficiary",
            filters=self.get_filters() + (advanced_filters or []),
            fields=[
                "name",
            ],
        )
        if self.donor:
            for ben in beneficiaries:
                beneficiary_no = frappe.get_value(
                    "Beneficiary Donor Assignment",
                    {"parent": ben.name, "parentfield": "donors", "parenttype": "Beneficiary", "donor": self.donor},
                    ["beneficiary_no"],
                )
                ben.beneficiary_no = beneficiary_no if beneficiary_no else None
                
        return beneficiaries

    def get_filters(self):
        filter_fields = [
                "state", 
                "beneficiary_type", 
                "district", 
                "zone", 
                "branch", 
                "donor"
            ]
        filters = [["status", "=", "Active"]]

        for d in filter_fields:
            if self.get(d):
                if d == "donor":
                    filters.append(["Beneficiary Donor Assignment", "donor", "=", self.get(d)])
                else:
                    filters.append([d, "=", self.get(d)])
        return filters


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
        headers = get_doctype_headers("Beneficiary Disbursement Entry Party")

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
            "attached_to_doctype": "Donation Disbursement Entry",
            "attached_to_name": self.name or "",
            "content": filedata,
            "is_private": 0,
        })
        file_doc.insert(ignore_permissions=True)
        return file_doc.file_url
    
    @frappe.whitelist()
    def upload_beneficiaries(self, file_url):
        headers = get_doctype_headers("Beneficiary Disbursement Entry Party")
        rows = extract_data_from_file(file_url)
        
        rows_to_upload = [r for r in rows if not r.get("beneficiary")]
        
        from ..beneficiary.beneficiary import upload_beneficiary_list
        
        upload_results = {"beneficiaries": [], "errors": []}
        if rows_to_upload:
            upload_results = upload_beneficiary_list(file_url, donor=self.donor)

        mapped_rows = []
        
        for idx, row in enumerate(rows):
            beneficiary_id = row.get("beneficiary")
            
            if not beneficiary_id and idx < len(upload_results.get("beneficiaries", [])):
                beneficiary_id = upload_results["beneficiaries"][idx]

            mapped_row = {}
            for header in headers:
                mapped_row[header] = row.get(header, "")
            
            mapped_row["beneficiary"] = beneficiary_id
            mapped_rows.append(mapped_row)

        return {
            "mapped_items": mapped_rows,
            "errors": upload_results.get("errors", [])
        }
    
    @frappe.whitelist()
    def make_payment_entries(self):
        for row in self.beneficiaries:
            if row.payment_entry:
                continue

            supplier = frappe.get_value("Beneficiary", row.beneficiary, "supplier")

            payment_entry = frappe.get_doc(
                {
                    "doctype": "Payment Entry",
                    "payment_type": "Pay",
                    "party_type": "Supplier",
                    "party": supplier,
                    "paid_from": self.paid_from,
                    "paid_to": self.paid_to,
                    "company": self.company,
                    "posting_date": today(),
                    "mode_of_payment": self.mode_of_payment,
                    "cost_center": self.cost_center,
                    "project": self.project,
                    "paid_amount": row.amount,
                    "received_amount": row.amount,
                    "remarks": f"Donation disbursement to beneficiary {row.beneficiary}",
                }
            )
            payment_entry.insert(ignore_permissions=True)
            row.payment_entry = payment_entry.name

        self.save()
        self.submit()
        frappe.msgprint(f"Payment Entries created for {len(self.beneficiaries)} beneficiaries")


