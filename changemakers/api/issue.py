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


@frappe.whitelist()
def create_case(
    requestor_id,
    requestor_phone,
    description,
    county,
    title,
    birth_certificate_type,
    requestor_service_rating=None,
):
    """
    Creates a new legal identity case for a birth certificate request.

    Args:
        requestor_id (str): The ID number of the person requesting the case.
        requestor_phone (str): The phone number of the requestor.
        description (str): Description of the case or issue.
        county (str): The county where the case is being filed.
        title (str): The title of the case (overridden to "Legal Identity Help").
        birth_certificate_type (str): Type of birth certificate request, must be either "New Born Registration" or "Late Registration".
        requestor_service_rating (int, optional): Service rating provided by the requestor. Defaults to 0 if not provided.

    Returns:
        dict: A dictionary containing:
            - "success" (bool): Indicates if the case was created successfully.
            - "message" (str, optional): Error message if creation failed.
            - "case_name" (str, optional): Name of the created case if successful.
            - "case_title" (str, optional): Title of the created case if successful.
    """
    if not requestor_id or not requestor_phone:
        return {
            "success": False,
            "message": "'requestor_id' or 'requestor_phone' must be provided.",
        }

    title = "Legal Identity Help"

    if not county:
        return {"success": False, "message": "'county' must be provided."}

    if not requestor_service_rating:
        requestor_service_rating = 0

    birth_certificate_type = birth_certificate_type.title()

    if birth_certificate_type not in ["New Born Registration", "Late Registration"]:
        return {
            "success": False,
            "message": "'birth_certificate_type' must be either 'New Born Registration' or 'Late Registration'.",
        }

    new_case = frappe.get_doc(
        {
            "doctype": "Case",
            "id_number": requestor_id,
            "requestor_phone": requestor_phone,
            "description": description,
            "title": title,
            "type": "Civil Case",
            "status": "New",
            "requestor_service_rating": requestor_service_rating,
            "birth_certificate_type": birth_certificate_type,
            "county": county,
        }
    )

    new_case.insert()

    return {
        "success": True,
        "case_name": new_case.name,
        "case_title": new_case.title
    }
