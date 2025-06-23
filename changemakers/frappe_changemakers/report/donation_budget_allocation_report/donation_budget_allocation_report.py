# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "fieldname": "budget_name",
            "fieldtype": "Data",
            "label": "Budget",
            "width": 250,
        },
        {
            "fieldname": "budget_against",
            "fieldtype": "Data",
            "label": "Budget Against",
            "options": "Project",
            "width": 200,
        },
        {
            "fieldname": "name",
            "fieldtype": "Data",
            "label": "Name",
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
    # Fetch all budgets
    budgets = frappe.db.sql(
        """
        SELECT
            name AS budget_name,
            budget_against
        FROM
            `tabBudget`
        ORDER BY
            name
    """,
        as_dict=True,
    )

    data = []

    for budget in budgets:
        # Add the budget row
        data.append(
            {
                "row_type": "budget",
                "budget_name": budget.budget_name,
                "budget_against": budget.budget_against,
                "name": "",  # Not applicable for budget row
                "donor": "",
                "donation": "",
                "amount": "",
                "budget_account": "",
                "budget_amount": "",
                "months_distributed": "",
                "percentage": "",
            }
        )

        # Fetch accounts for this budget
        accounts = frappe.db.sql(
            """
            SELECT
                account,
                budget_amount
            FROM
                `tabBudget Account`
            WHERE
                parent = %s AND parenttype = 'Budget'
        """,
            (budget.budget_name,),
            as_dict=True,
        )

        for account in accounts:
            # Add the account row as a subrow to the budget
            data.append(
                {
                    "row_type": "account",
                    "budget_name": "",  # Leave blank for subrow
                    "budget_against": "",
                    "name": "",
                    "donor": "",
                    "donation": "",
                    "amount": "",
                    "budget_account": account.account,
                    "budget_amount": account.budget_amount,
                    "months_distributed": "",
                    "percentage": "",
                }
            )

            # Fetch allocation items for this account
            allocations = frappe.db.sql(
                """
                SELECT
                    donation_allocation,
                    amount
                FROM
                    `tabBudget Donation Allocation Item`
                WHERE
                    parent = %s AND parenttype = 'Budget' AND account = %s
            """,
                (budget.budget_name, account.account),
                as_dict=True,
            )

            for alloc in allocations:
                # Add the allocation item as a subrow to the account
                data.append(
                    {
                        "row_type": "allocation",
                        "budget_name": "",
                        "budget_against": "",
                        "name": "",
                        "donor": "",
                        "donation": alloc.donation_allocation,
                        "amount": alloc.amount,
                        "budget_account": "",
                        "budget_amount": "",
                        "months_distributed": "",
                        "percentage": "",
                    }
                )

    return data
