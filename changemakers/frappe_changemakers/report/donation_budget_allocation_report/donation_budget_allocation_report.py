# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"fieldname": "name", "fieldtype": "Data", "label": "Name", "width": 250},
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


def get_data(filters=None):
    query = """
        SELECT
            b.name AS name,
            b.budget_against AS budget_against,
            ba.account AS budget_account,
            ba.budget_amount AS budget_amount,
            dai.donation_allocation AS donation_allocation,
            dai.amount AS donation_amount,
            (
                SELECT COUNT(*)
                FROM `tabMonthly Distribution Percentage` mdp
                WHERE mdp.parent = b.monthly_distribution
            ) AS months_distributed
        FROM
            `tabBudget` b
        LEFT JOIN
            `tabBudget Account` ba ON ba.parent = b.name AND ba.parenttype = 'Budget'
        LEFT JOIN
            `tabBudget Donation Allocation Item` dai ON dai.parent = b.name AND dai.parenttype = 'Budget'
        ORDER BY
            b.name, ba.account, dai.donation_allocation
    """
    data = frappe.db.sql(query, as_dict=True)
    return data
