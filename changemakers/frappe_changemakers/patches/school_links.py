import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Student": [
            {
                "fieldname": "school",
                "fieldtype": "Link",
                "label": "School",
                "options": "Learning Centre",
                "translatable": 1,
                "insert_after": "last_name"
            }
        ],
        "Instructor": [
            {
                "fieldname": "school",
                "fieldtype": "Link",
                "label": "School",
                "options": "Learning Centre",
                "translatable": 1,
                "insert_after": "gender"
            }
        ]
    }

    create_custom_fields(custom_fields, update=True)