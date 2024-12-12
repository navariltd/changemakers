import frappe

@frappe.whitelist()
def get_filtered_beneficiaries(project):
    branch = frappe.db.get_value("Project", project, "custom_branch")
    if not branch:
        return []

    beneficiaries = frappe.get_all(
        'Beneficiary', filters={'status': 'Active', 'branch': branch}, fields=['name']
    )
    stock_entries = frappe.get_all(
        'Stock Entry', filters={'project': project,}, fields=['custom_beneficiary']
    )
    excluded = {entry['custom_beneficiary'] for entry in stock_entries}
    return [b['name'] for b in beneficiaries if b['name'] not in excluded]


@frappe.whitelist()
def get_bom_items(project):
    bom_name = frappe.db.get_value('BOM', {'project': project}, 'name')
    if not bom_name:
        return []

    bom_items = frappe.get_all(
        'BOM Item',
        filters={'parent': bom_name},
        fields=['item_code', 'qty', 'rate', 'amount']
    )
    return bom_items

@frappe.whitelist()
def get_collector(beneficiary):
    collector = frappe.get_all(
        'Collector',
        filters={'beneficiary': beneficiary},
        fields=['name'],
        limit=1
    )
    return [c['name'] for c in collector] if collector else []
