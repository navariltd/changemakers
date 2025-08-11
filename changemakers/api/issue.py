import frappe


@frappe.whitelist()
def get_case(reporter_id=None, reporter_phone=None):
    if not reporter_id and not reporter_phone:
        return {
            "success": False,
            "message": "Either 'reporter_id' or 'reporter_phone' must be provided.",
        }

    case_name = None
    if reporter_id:
        case_name = frappe.db.get_value(
            "Case", {"user_document_number": reporter_id}, "name"
        )
    elif reporter_phone:
        case_name = frappe.db.get_value(
            "Case", {"requestor_phone": reporter_phone}, "name"
        )

    if not case_name:
        return {
            "success": False,
            "message": "No issue found with the provided details.",
        }

    status = frappe.db.get_value("Case", case_name, "status")

    paralegals = frappe.get_all(
        "Paralegal User", filters={"parent": case_name}, fields=["user", "phone"]
    )

    return {
        "success": True,
        "case_name": case_name,
        "status": status,
        "assigned_paralegals": [p for p in paralegals],
    }
