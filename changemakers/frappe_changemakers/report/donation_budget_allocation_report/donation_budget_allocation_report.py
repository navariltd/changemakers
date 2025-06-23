# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns, data = [], []
    return columns, data


def get_columns():
    return [
        {"fieldname": "name", "fieldtype": "Data", "label": "Name", "width": 150},
        {
            "fieldname": "budget_against",
            "fieldtype": "Data",
            "label": "Budget Against",
            "options": "Project",
            "width": 200,
        },
        {
            "fieldname": "donor",
            "fieldtype": "Link",
            "label": "Donor",
            "options": "Donor",
            "width": 200,
        },
        {
            "fieldname": "donation",
            "fieldtype": "Link",
            "label": "Donation",
            "options": "Donation",
            "width": 200,
        },
        {
            "fieldname": "amount",
            "fieldtype": "Currency",
            "label": "Amount",
        },
        {
            "fieldname": "budget_account",
            "fieldtype": "Link",
            "label": "Budget Account",
            "options": "Budget Account",
        },
        {
            "fieldname": "budget_amount",
            "fieldtype": "Currency",
            "label": "Allocation",
            "width": 150,
        },
        {
            "fieldname": "months_distributed",
            "fieldtype": "Int",
            "label": "Months Distributed",
            "width": 150,
        },
        {
            "fieldname": "percentage",
            "fieldtype": "Percent",
            "label": "Percentage",
            "width": 100,
        },
    ]
