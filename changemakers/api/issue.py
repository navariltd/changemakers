import frappe

@frappe.whitelist()
def get_issue(reporter_id=None, reporter_phone=None):
    if not reporter_id and not reporter_phone:
        return {
            "success": False,
            "message": "Either 'reporter_id' or 'reporter_phone' must be provided."
        }

    issue_name = None
    if reporter_id:
        issue_name = frappe.db.get_value(
            "Issue",
            {"user_document_number": reporter_id},
            "name"
        )
    elif reporter_phone:
        issue_name = frappe.db.get_value(
            "Issue",
            {"phone_number": reporter_phone},
            "name"
        )
        
    if not issue_name:
        return {
            "success": False,
            "message": "No issue found with the provided details."
        }

    status = frappe.db.get_value("Issue", issue_name, "status")
    
    paralegals = frappe.get_all(
        "Paralegal User",
        filters={"parent": issue_name},
        fields=["user"]
    )

    return {
        "success": True,
        "issue_name": issue_name,
        "status": status,
        "assigned_paralegals": [p["user"] for p in paralegals]
    }
