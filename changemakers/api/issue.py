import frappe


@frappe.whitelist()
def get_case(requestor_id=None, requestor_phone=None):
    if not requestor_id and not requestor_phone:
        return {
            "success": False,
            "message": "Either 'requestor_id' or 'requestor_phone' must be provided.",
        }

    case_name = None
    if requestor_id:
        case_name = frappe.db.get_value("Case", {"id_number": requestor_id}, "name")
    elif requestor_phone:
        case_name = frappe.db.get_value(
            "Case", {"requestor_phone": requestor_phone}, "name"
        )

    if not case_name:
        return {
            "success": False,
            "message": "No case found with the provided details.",
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
