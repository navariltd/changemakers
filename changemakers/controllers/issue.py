import frappe


def before_save(doc, method=None):
    # Check if the Todo is an assignment for an Issue
    if doc.reference_type != "Issue":
        return

    parent_issue = frappe.get_doc("Issue", doc.reference_name)

    # Handle a new assignment (Todo status is 'Open')
    if parent_issue.status == "Open":
        user_details = frappe.db.get_value(
            "User", doc.allocated_to, ["full_name", "phone"], as_dict=True
        )

        if user_details:
            parent_issue.append(
                "custom_assigned_paralegals",
                {
                    "user": doc.allocated_to,
                    "full_name": user_details.get("full_name"),
                    "phone": user_details.get("phone"),
                },
            )
            parent_issue.save()

    # Handle a user unassignment (Todo status is changed to 'Cancelled')
    if doc.has_value_changed("status") and doc.status == "Cancelled":
        for row in parent_issue.get("custom_assigned_paralegals"):
            if row.user == doc.allocated_to:
                parent_issue.remove(row)
                parent_issue.save()
                frappe.db.delete(
                    "Paralegal User",
                    {"parent": parent_issue.name, "user": doc.allocated_to}
                )
                frappe.db.commit()
                
                break
    
