import frappe

def update_links_for_donation_distribution() -> None:
    doctypes = ["Donation", "Donor"]
    for doctype in doctypes:
        try:
            doc = frappe.get_doc("DocType", doctype)

            doc.links = [
                link for link in doc.get("links", [])
                if link.link_doctype != "Donation Distribution"
            ]

            link_data = {
                "link_doctype": "Donation Distribution",
                "link_fieldname": "donation" if doctype == "Donation" else "donor",
            }
            if doctype == "Donation":
                link_data["group"] = "Distribution"

            doc.append("links", link_data)

            doc.save()
            frappe.db.commit()

        except Exception as e:
            frappe.log_error(
                message=f"Error updating links for {doctype}: {str(e)}",
                title="Update Links Error"
            )

def execute() -> None:
    update_links_for_donation_distribution()


