# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters=None):
    columns = [
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
            "fieldname": "budget_account",
            "fieldtype": "Link",
            "label": "Account",
            "options": "Budget Account",
            "width": 200,
        },
        {
            "fieldname": "budget_amount",
            "fieldtype": "Currency",
            "label": "Budget Allocation",
            "width": 150,
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
            "fieldname": "allocation",
            "fieldtype": "Link",
            "label": "Donation Allocation",
            "options": "Donation Allocation",
            "width": 200,
        },
        {
            "fieldname": "amount",
            "fieldtype": "Currency",
            "label": "Allocated Amount",
            "width": 200,
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

    sorted_months = get_sorted_months_from_fiscal_years(filters)
    for month_label in sorted_months:
        columns.append(
            {
                "fieldname": frappe.scrub(month_label),
                "fieldtype": "Percent",
                "label": month_label,
                "width": 200,
            }
        )
    return columns


def get_sorted_months_from_fiscal_years(filters=None):
    fiscal_year_names = []
    if filters and filters.get("fiscal_year"):
        fiscal_year_names.append(filters["fiscal_year"])
    else:
        budget_fiscal_years = frappe.db.sql(
            """
            SELECT DISTINCT tmd.fiscal_year
            FROM `tabBudget` tb
            JOIN `tabMonthly Distribution` tmd ON tb.monthly_distribution = tmd.name
            WHERE tmd.fiscal_year IS NOT NULL AND tmd.fiscal_year != ''
            """,
            as_list=True,
        )
        for fy in budget_fiscal_years:
            fiscal_year_names.append(fy[0])

    if not fiscal_year_names:
        return []

    unique_month_labels = set()
    month_datetime_map = {}

    for fy_name in list(set(fiscal_year_names)):
        fiscal_year_doc = frappe.get_cached_doc("Fiscal Year", fy_name)
        # Corrected field names here:
        start_date = fiscal_year_doc.year_start_date
        end_date = fiscal_year_doc.year_end_date

        current_date = frappe.utils.getdate(start_date)
        end_date_obj = frappe.utils.getdate(end_date)

        while current_date <= end_date_obj:
            month_label = current_date.strftime("%B %Y")
            unique_month_labels.add(month_label)
            month_datetime_map[month_label] = current_date

            next_month = current_date.replace(day=28) + timedelta(days=4)
            current_date = next_month.replace(day=1)

    sorted_months = sorted(
        list(unique_month_labels), key=lambda x: month_datetime_map[x]
    )
    return sorted_months


def get_data(filters=None):
    budgets = frappe.db.sql(
        """
        SELECT
            tb.name AS budget_name,
            tb.budget_against,
            tb.employee,
            tb.project,
            tb.task,
            tb.monthly_distribution,
            tmd.fiscal_year
        FROM `tabBudget` tb
        LEFT JOIN `tabMonthly Distribution` tmd ON tb.monthly_distribution = tmd.name
        ORDER BY
            tb.name
    """,
        as_dict=True,
    )

    data = []
    sorted_months = get_sorted_months_from_fiscal_years(filters)

    fiscal_year_cache = {}

    for budget in budgets:
        if (
            filters
            and filters.get("fiscal_year")
            and budget.fiscal_year != filters["fiscal_year"]
        ):
            continue

        fiscal_year_start_date = None
        fiscal_year_end_date = None  # Also cache end date for month inferring
        if budget.fiscal_year:
            if budget.fiscal_year not in fiscal_year_cache:
                fiscal_year_doc = frappe.get_cached_doc(
                    "Fiscal Year", budget.fiscal_year
                )
                # Corrected field names here:
                fiscal_year_cache[budget.fiscal_year] = {
                    "start_date": fiscal_year_doc.year_start_date,
                    "end_date": fiscal_year_doc.year_end_date,
                }
            fiscal_year_start_date = fiscal_year_cache[budget.fiscal_year]["start_date"]
            fiscal_year_end_date = fiscal_year_cache[budget.fiscal_year]["end_date"]

        months_distributed = (
            frappe.db.sql(
                """
            SELECT COUNT(*) AS cnt
            FROM `tabMonthly Distribution Percentage`
            WHERE parent = %s
            """,
                (budget.monthly_distribution,),
                as_dict=True,
            )[0]["cnt"]
            or 0
        )

        distribution_rows = frappe.db.sql(
            """
            SELECT month, percentage_allocation
            FROM `tabMonthly Distribution Percentage`
            WHERE parent = %s
            ORDER BY month
            """,
            (budget.monthly_distribution,),
            as_dict=True,
        )

        distribution_dict = {}
        for row in distribution_rows:
            if fiscal_year_start_date and fiscal_year_end_date:
                try:
                    month_number = datetime.strptime(row["month"], "%B").month

                    current_fy_date = frappe.utils.getdate(fiscal_year_start_date)
                    fy_end_date_obj = frappe.utils.getdate(
                        fiscal_year_end_date
                    )  # Use the cached end date

                    found_year = None
                    while current_fy_date <= fy_end_date_obj:
                        if current_fy_date.month == month_number:
                            found_year = current_fy_date.year
                            break
                        next_month = current_fy_date.replace(day=28) + timedelta(days=4)
                        current_fy_date = next_month.replace(day=1)

                    if found_year:
                        full_month_label = f"{row['month']} {found_year}"
                        distribution_dict[frappe.scrub(full_month_label)] = row[
                            "percentage_allocation"
                        ]
                    else:
                        frappe.log_error(
                            f"Could not determine year for month '{row['month']}' in Fiscal Year '{budget.fiscal_year}' (FY Dates: {fiscal_year_start_date} - {fiscal_year_end_date})",
                            "Month Year Mismatch",
                        )
                        # Fallback to just scrubbing the month name if year inference fails
                        distribution_dict[frappe.scrub(row["month"])] = row[
                            "percentage_allocation"
                        ]
                except ValueError:
                    frappe.log_error(
                        f"Invalid month name '{row['month']}' in Monthly Distribution Percentage for parent {budget.monthly_distribution}",
                        "Invalid Month Name Format",
                    )
                    distribution_dict[frappe.scrub(row["month"])] = row[
                        "percentage_allocation"
                    ]
            else:
                distribution_dict[frappe.scrub(row["month"])] = row[
                    "percentage_allocation"
                ]

        percentage = 100 / months_distributed if months_distributed > 0 else 0

        name = ""
        if budget.budget_against == "Employee":
            name = frappe.db.get_value("Employee", budget.get("employee"), "first_name")
        elif budget.budget_against == "Project":
            name = frappe.db.get_value("Project", budget.get("project"), "project_name")
        elif budget.budget_against == "Task":
            name = frappe.db.get_value("Task", budget.get("task"), "subject")

        month_data = {frappe.scrub(month_label): "" for month_label in sorted_months}
        month_data.update(distribution_dict)

        data.append(
            {
                "row_type": "budget",
                "budget_name": budget.budget_name,
                "budget_against": budget.budget_against,
                "name": name,
                "donor": "",
                "donation": "",
                "amount": "",
                "budget_account": "",
                "budget_amount": "",
                "months_distributed": months_distributed,
                "percentage": percentage,
                **month_data,
            }
        )

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
            account_month_data = {
                frappe.scrub(month_label): "" for month_label in sorted_months
            }
            data.append(
                {
                    "row_type": "account",
                    "budget_name": "",
                    "budget_against": "",
                    "name": "",
                    "donor": "",
                    "donation": "",
                    "amount": "",
                    "budget_account": account.account,
                    "budget_amount": account.budget_amount,
                    "months_distributed": "",
                    "percentage": "",
                    **account_month_data,
                }
            )

            allocations = frappe.db.sql(
                """
                SELECT
                    donation_allocation,
                    amount, donor, donation
                FROM
                    `tabBudget Donation Allocation Item`
                WHERE
                    parent = %s AND parenttype = 'Budget' AND account = %s
            """,
                (budget.budget_name, account.account),
                as_dict=True,
            )

            for alloc in allocations:
                allocation_month_data = {
                    frappe.scrub(month_label): "" for month_label in sorted_months
                }
                data.append(
                    {
                        "row_type": "allocation",
                        "budget_name": "",
                        "budget_against": "",
                        "name": "",
                        "donor": alloc.donor,
                        "donation": alloc.donation,
                        "allocation": alloc.donation_allocation,
                        "amount": alloc.amount,
                        "budget_account": "",
                        "budget_amount": "",
                        "months_distributed": "",
                        "percentage": "",
                        **allocation_month_data,
                    }
                )

    return data
