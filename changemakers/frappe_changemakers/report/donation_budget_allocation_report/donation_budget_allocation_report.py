# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Sum


Budget = DocType("Budget")
MonthlyDistribution = DocType("Monthly Distribution")
BudgetDonationAllocationItem = DocType("Budget Donation Allocation Item")
BudgetAccount = DocType("Budget Account")
GL_Entry = DocType("GL Entry")


def execute(filters=None):
    """
    Main function to execute the report.
    """
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_columns(filters=None):
    """
    Defines the columns for the report.
    """
    columns = [
        {
            "fieldname": "budget_name",
            "fieldtype": "Link",
            "label": "Budget",
            "options": "Budget",
            "width": 250,
        },
        {
            "fieldname": "budget_against",
            "fieldtype": "Data",
            "label": "Budget Against",
            "options": "Project",
            "width": 200,
        },
        {"fieldname": "name", "fieldtype": "Data", "label": "Name", "width": 200},
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
            "fieldname": "actual_amount",
            "fieldtype": "Currency",
            "label": "Actual Amount",
            "width": 150,
        },
        {
            "fieldname": "variance_amount",
            "fieldtype": "Currency",
            "label": "Balance after Donation",
            "width": 200,
        },
        {
            "fieldname": "total_donations",
            "fieldtype": "Currency",
            "label": "Total Donations",
            "width": 150,
        },
        {
            "fieldname": "budget_variance",
            "fieldtype": "Currency",
            "label": "Budget Variance",
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
            "label": "Percentage (Monthly Avg.)",
            "width": 200,
        },
    ]

    sorted_months = _get_sorted_months_from_fiscal_years(filters)
    for month_label in sorted_months:
        columns.append(
            {
                "fieldname": frappe.scrub(month_label),
                "fieldtype": "Currency",
                "label": month_label,
                "width": 200,
            }
        )
    return columns


def _get_sorted_months_from_fiscal_years(filters=None):
    """
    Helper function to get a sorted list of month labels based on fiscal years.
    Uses a leading underscore to indicate it's an internal helper function.
    """
    fiscal_year_names = []
    if filters and filters.get("fiscal_year"):
        fiscal_year_names.append(filters["fiscal_year"])
    else:
        budget_fiscal_years_query = (
            frappe.qb.from_(Budget)
            .join(MonthlyDistribution)
            .on(Budget.monthly_distribution == MonthlyDistribution.name)
            .select(MonthlyDistribution.fiscal_year)
            .where(MonthlyDistribution.fiscal_year.isnotnull())
            .where(MonthlyDistribution.fiscal_year != "")
            .distinct()
        )
        if filters and filters.get("budget_name"):
            budget_fiscal_years_query = budget_fiscal_years_query.where(
                Budget.name == filters["budget_name"]
            )
        fiscal_year_names.extend(
            [fy[0] for fy in budget_fiscal_years_query.run(as_list=True)]
        )

    if not fiscal_year_names:
        return []

    unique_month_labels = set()
    month_datetime_map = {}

    for fy_name in list(set(fiscal_year_names)):
        fiscal_year_doc = frappe.get_cached_doc("Fiscal Year", fy_name)
        start_date = fiscal_year_doc.year_start_date
        end_date = fiscal_year_doc.year_end_date

        current_date = frappe.utils.getdate(start_date)
        end_date_obj = frappe.utils.getdate(end_date)

        while current_date <= end_date_obj:
            month_label = current_date.strftime("%B %Y")
            unique_month_labels.add(month_label)
            month_datetime_map[month_label] = current_date
            current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(
                day=1
            )  # Move to next month's 1st day

    return sorted(list(unique_month_labels), key=lambda x: month_datetime_map[x])


def get_data(filters=None):
    """
    Retrieves and processes budget data for the report.
    """
    budgets = _get_filtered_budgets(filters)
    final_report_data = []
    fiscal_year_cache = {}

    # Get sorted months for populating empty values in allocation rows
    sorted_months_labels = _get_sorted_months_from_fiscal_years(filters)
    allocation_month_empty_data = {
        frappe.scrub(month_label): "" for month_label in sorted_months_labels
    }

    for budget in budgets:
        fiscal_year_dates = _get_fiscal_year_dates(
            budget.fiscal_year, fiscal_year_cache
        )
        start_date = fiscal_year_dates["start_date"]
        end_date = fiscal_year_dates["end_date"]

        monthly_distribution_data = _get_monthly_distribution_data(
            budget.monthly_distribution, start_date, end_date
        )
        months_distributed = monthly_distribution_data["count"]
        distribution_dict_percentages = monthly_distribution_data["percentages"]

        total_budget_amount = _get_total_budget_amount(budget.budget_name)
        month_data_amounts = _calculate_monthly_allocated_amounts(
            total_budget_amount, distribution_dict_percentages
        )

        percentage_avg = 100 / months_distributed if months_distributed > 0 else 0
        budget_against_name = _get_budget_against_name(budget)

        total_actual_amount_for_budget = 0
        current_budget_accounts_data = []  # To hold account rows
        current_budget_allocations_data = []  # To hold allocation rows

        total_donations_for_budget = _get_total_donations_for_budget(budget.budget_name)

        accounts = _get_budget_accounts(
            budget.budget_name, filters.get("budget_account")
        )

        for account in accounts:
            account_monthly_amounts = _calculate_monthly_allocated_amounts(
                account.budget_amount, distribution_dict_percentages
            )

            actual_amount_for_account = _get_actual_expenses_for_account(
                account.account,
                start_date,
                end_date,
                budget.budget_against,
                budget.employee,
                budget.project,
                budget.task,
                budget.cost_center,
                budget.program,
            )
            total_actual_amount_for_budget += actual_amount_for_account

            total_donations_for_account = _get_total_donations_for_account(
                budget.budget_name, account.account
            )

            variance_for_account = (
                total_donations_for_account - actual_amount_for_account
            )
            budget_variance_for_account = (
                account.budget_amount - actual_amount_for_account
            )

            current_budget_accounts_data.append(
                {
                    "budget_name": "",
                    "budget_against": "",
                    "name": "",
                    "budget_account": account.account,
                    "budget_amount": account.budget_amount,
                    "actual_amount": actual_amount_for_account,
                    "variance_amount": variance_for_account,
                    "total_donations": "",
                    "budget_variance": budget_variance_for_account,
                    "months_distributed": "",
                    "percentage": "",
                    "donor": "",  # Empty for account row
                    "donation": "",  # Empty for account row
                    "allocation": "",  # Empty for account row
                    "amount": "",  # Empty for account row
                    **account_monthly_amounts,
                }
            )

            # Fetch and append Allocation Rows
            allocations = _get_donation_allocations_for_account(
                budget.budget_name, account.account, filters.get("donation_allocation")
            )
            for alloc in allocations:
                current_budget_allocations_data.append(
                    {
                        "budget_name": "",
                        "budget_against": "",
                        "name": "",
                        "donor": alloc.donor,
                        "donation": alloc.donation,
                        "allocation": alloc.donation_allocation,
                        "amount": alloc.amount,
                        "budget_account": "",
                        "budget_amount": "",
                        "actual_amount": "",
                        "variance_amount": "",
                        "total_donations": "",
                        "budget_variance": "",
                        "months_distributed": "",
                        "percentage": "",
                        **allocation_month_empty_data,
                    }
                )

        balance_after_donation_for_budget = (
            total_donations_for_budget - total_actual_amount_for_budget
        )
        budget_variance_for_budget = (
            total_budget_amount - total_actual_amount_for_budget
        )

        final_report_data.append(
            {
                "budget_name": budget.budget_name,
                "budget_against": budget.budget_against,
                "name": budget_against_name,
                "budget_account": "",
                "budget_amount": total_budget_amount,
                "actual_amount": total_actual_amount_for_budget,
                "variance_amount": balance_after_donation_for_budget,
                "total_donations": total_donations_for_budget,
                "budget_variance": budget_variance_for_budget,
                "months_distributed": months_distributed,
                "percentage": percentage_avg,
                "donor": "",  # Empty for main budget row
                "donation": "",  # Empty for main budget row
                "allocation": "",  # Empty for main budget row
                "amount": "",  # Empty for main budget row
                **month_data_amounts,
            }
        )
        final_report_data.extend(current_budget_accounts_data)
        final_report_data.extend(
            current_budget_allocations_data
        )  # Add allocation rows here

    return final_report_data


def _get_filtered_budgets(filters):
    """Constructs and runs the query for main budget documents based on filters."""
    budgets_query = (
        frappe.qb.from_(Budget)
        .left_join(MonthlyDistribution)
        .on(Budget.monthly_distribution == MonthlyDistribution.name)
        .select(
            Budget.name.as_("budget_name"),
            Budget.budget_against,
            Budget.employee,
            Budget.project,
            Budget.task,
            Budget.cost_center,
            Budget.program,
            Budget.monthly_distribution,
            MonthlyDistribution.fiscal_year,
        )
        .orderby(Budget.name)
    )

    if filters:
        if filters.get("fiscal_year"):
            budgets_query = budgets_query.where(
                MonthlyDistribution.fiscal_year == filters["fiscal_year"]
            )
        if filters.get("budget_against"):
            budgets_query = budgets_query.where(
                Budget.budget_against == filters["budget_against"]
            )

            budget_against_type = filters["budget_against"]
            if budget_against_type == "Employee" and filters.get("employee"):
                budgets_query = budgets_query.where(
                    Budget.employee == filters.get("employee")
                )
            elif budget_against_type == "Project" and filters.get("project"):
                budgets_query = budgets_query.where(
                    Budget.project == filters.get("project")
                )
            elif budget_against_type == "Task" and filters.get("task"):
                budgets_query = budgets_query.where(Budget.task == filters.get("task"))
            elif budget_against_type == "Cost Center" and filters.get("cost_center"):
                budgets_query = budgets_query.where(
                    Budget.cost_center == filters.get("cost_center")
                )
            elif budget_against_type == "Program" and filters.get("program"):
                budgets_query = budgets_query.where(
                    Budget.program == filters.get("program")
                )

        if filters.get("budget_name"):
            budgets_query = budgets_query.where(Budget.name == filters["budget_name"])

        if filters.get("budget_account"):
            budgets_with_account = (
                frappe.qb.from_(BudgetAccount)
                .select(BudgetAccount.parent)
                .where(BudgetAccount.account == filters["budget_account"])
                .where(BudgetAccount.parenttype == "Budget")
                .distinct()
            )
            budgets_query = budgets_query.where(Budget.name.isin(budgets_with_account))

        if filters.get("donor"):
            budgets_with_donor = (
                frappe.qb.from_(BudgetDonationAllocationItem)
                .select(BudgetDonationAllocationItem.parent)
                .where(BudgetDonationAllocationItem.donor == filters["donor"])
                .distinct()
            )
            budgets_query = budgets_query.where(Budget.name.isin(budgets_with_donor))

        if filters.get("donation"):
            budgets_with_donation = (
                frappe.qb.from_(BudgetDonationAllocationItem)
                .select(BudgetDonationAllocationItem.parent)
                .where(BudgetDonationAllocationItem.donation == filters["donation"])
                .distinct()
            )
            budgets_query = budgets_query.where(Budget.name.isin(budgets_with_donation))

        if filters.get("donation_allocation"):
            budgets_with_allocation = (
                frappe.qb.from_(BudgetDonationAllocationItem)
                .select(BudgetDonationAllocationItem.parent)
                .where(
                    BudgetDonationAllocationItem.donation_allocation
                    == filters["donation_allocation"]
                )
                .distinct()
            )
            budgets_query = budgets_query.where(
                Budget.name.isin(budgets_with_allocation)
            )

    return budgets_query.run(as_dict=True)


def _get_donation_allocations_for_account(
    budget_name, account_name, filter_allocation=None
):
    """Fetches donation allocation items for a given budget and account."""
    allocations_query = (
        frappe.qb.from_(BudgetDonationAllocationItem)
        .select(
            BudgetDonationAllocationItem.donation_allocation,
            BudgetDonationAllocationItem.amount,
            BudgetDonationAllocationItem.donor,
            BudgetDonationAllocationItem.donation,
        )
        .where(BudgetDonationAllocationItem.parent == budget_name)
        .where(BudgetDonationAllocationItem.parenttype == "Budget")
        .where(BudgetDonationAllocationItem.account == account_name)
    )
    if filter_allocation:
        allocations_query = allocations_query.where(
            BudgetDonationAllocationItem.donation_allocation == filter_allocation
        )
    return allocations_query.run(as_dict=True)


def _get_fiscal_year_dates(fiscal_year_name, fiscal_year_cache):
    """Retrieves and caches fiscal year start and end dates."""
    if not fiscal_year_name:
        return {"start_date": None, "end_date": None}

    if fiscal_year_name not in fiscal_year_cache:
        fiscal_year_doc = frappe.get_cached_doc("Fiscal Year", fiscal_year_name)
        fiscal_year_cache[fiscal_year_name] = {
            "start_date": fiscal_year_doc.year_start_date,
            "end_date": fiscal_year_doc.year_end_date,
        }
    return fiscal_year_cache[fiscal_year_name]


def _get_monthly_distribution_data(
    monthly_distribution_name, fiscal_year_start_date, fiscal_year_end_date
):
    """Fetches monthly distribution percentages and count for a given monthly distribution."""
    MonthlyDistributionPercentage = DocType("Monthly Distribution Percentage")

    months_distributed_count = (
        frappe.qb.from_(MonthlyDistributionPercentage)
        .select(Count("*").as_("cnt"))
        .where(MonthlyDistributionPercentage.parent == monthly_distribution_name)
    ).run(as_dict=True)[0]["cnt"] or 0

    distribution_rows = (
        frappe.qb.from_(MonthlyDistributionPercentage)
        .select(
            MonthlyDistributionPercentage.month,
            MonthlyDistributionPercentage.percentage_allocation,
        )
        .where(MonthlyDistributionPercentage.parent == monthly_distribution_name)
        .orderby(MonthlyDistributionPercentage.month)
    ).run(as_dict=True)

    distribution_dict_percentages = {}
    for row in distribution_rows:
        month_label = row["month"]
        if fiscal_year_start_date and fiscal_year_end_date:
            try:
                month_number = datetime.strptime(row["month"], "%B").month
                current_fy_date = frappe.utils.getdate(fiscal_year_start_date)
                fy_end_date_obj = frappe.utils.getdate(fiscal_year_end_date)
                found_year = None
                while current_fy_date <= fy_end_date_obj:
                    if current_fy_date.month == month_number:
                        found_year = current_fy_date.year
                        break
                    current_fy_date = (
                        current_fy_date.replace(day=28) + timedelta(days=4)
                    ).replace(day=1)
                if found_year:
                    month_label = f"{row['month']} {found_year}"
                else:
                    frappe.log_error(
                        f"Could not determine year for month '{row['month']}' in Fiscal Year.",
                        "Month Year Mismatch",
                    )
            except ValueError:
                frappe.log_error(
                    f"Invalid month name '{row['month']}' in Monthly Distribution Percentage.",
                    "Invalid Month Name Format",
                )
        distribution_dict_percentages[frappe.scrub(month_label)] = row[
            "percentage_allocation"
        ]

    return {
        "count": months_distributed_count,
        "percentages": distribution_dict_percentages,
    }


def _get_total_budget_amount(budget_name):
    """Calculates the total allocated budget amount for a given budget."""
    total_budget_amount_result = (
        frappe.qb.from_(BudgetAccount)
        .select(Sum(BudgetAccount.budget_amount).as_("total_amount"))
        .where(BudgetAccount.parent == budget_name)
        .where(BudgetAccount.parenttype == "Budget")
    ).run(as_dict=True)
    return total_budget_amount_result[0]["total_amount"] or 0


def _calculate_monthly_allocated_amounts(base_amount, distribution_percentages):
    """Calculates monthly allocated amounts based on a base amount and distribution percentages."""
    month_data_amounts = {}
    for month_label_scrubbed, percentage_value in distribution_percentages.items():
        month_data_amounts[month_label_scrubbed] = (
            percentage_value / 100
        ) * base_amount
    return month_data_amounts


def _get_budget_against_name(budget):
    """Fetches the name of the 'budget against' entity (e.g., Employee, Project)."""
    name_field_map = {
        "Employee": "first_name",
        "Project": "project_name",
        "Task": "subject",
        "Cost Center": "name",
        "Program": "name",
    }
    doctype_map = {
        "Employee": "Employee",
        "Project": "Project",
        "Task": "Task",
        "Cost Center": "Cost Center",
        "Program": "Program",
    }

    budget_against_type = budget.budget_against
    if budget_against_type and budget.get(
        budget_against_type.lower().replace(" ", "_")
    ):
        doc_name = budget.get(budget_against_type.lower().replace(" ", "_"))
        field_name = name_field_map.get(budget_against_type)
        doctype_name = doctype_map.get(budget_against_type)
        if doc_name and field_name and doctype_name:
            return frappe.db.get_value(doctype_name, doc_name, field_name)
    return ""


def _get_total_donations_for_budget(budget_name):
    """Calculates total donations for a given budget."""
    total_donations_result = (
        frappe.qb.from_(BudgetDonationAllocationItem)
        .select(Sum(BudgetDonationAllocationItem.amount).as_("total_donated_amount"))
        .where(BudgetDonationAllocationItem.parent == budget_name)
        .where(BudgetDonationAllocationItem.parenttype == "Budget")
    ).run(as_dict=True)
    return total_donations_result[0]["total_donated_amount"] or 0


def _get_budget_accounts(budget_name, filter_account=None):
    """Fetches budget accounts for a given budget, optionally filtered by account."""
    accounts_query = (
        frappe.qb.from_(BudgetAccount)
        .select(
            BudgetAccount.account,
            BudgetAccount.budget_amount,
        )
        .where(BudgetAccount.parent == budget_name)
        .where(BudgetAccount.parenttype == "Budget")
    )
    if filter_account:
        accounts_query = accounts_query.where(BudgetAccount.account == filter_account)
    return accounts_query.run(as_dict=True)


def _get_total_donations_for_account(budget_name, account_name):
    """Calculates total donations for a specific account within a budget."""
    total_donations_account_result = (
        frappe.qb.from_(BudgetDonationAllocationItem)
        .select(Sum(BudgetDonationAllocationItem.amount).as_("total_donated_amount"))
        .where(BudgetDonationAllocationItem.parent == budget_name)
        .where(BudgetDonationAllocationItem.parenttype == "Budget")
        .where(BudgetDonationAllocationItem.account == account_name)
    ).run(as_dict=True)
    return total_donations_account_result[0]["total_donated_amount"] or 0


def _get_actual_expenses_for_account(
    account,
    start_date,
    end_date,
    budget_against_type,
    employee=None,
    project=None,
    task=None,
    cost_center=None,
    program=None,
):
    """
    Fetches the total actual expense (debit) for a given account within a date range,
    considering budget against dimensions.
    """
    query = (
        frappe.qb.from_(GL_Entry)
        .select(Sum(GL_Entry.debit).as_("total_debit"))
        .where(GL_Entry.account == account)
        .where(GL_Entry.posting_date >= start_date)
        .where(GL_Entry.posting_date <= end_date)
        .where(GL_Entry.docstatus == 1)  # Only consider submitted GL Entries
    )

    dimension_map = {
        "Employee": GL_Entry.employee,
        "Project": GL_Entry.project,
        "Task": GL_Entry.task,
        "Cost Center": GL_Entry.cost_center,
        "Program": GL_Entry.program,
    }

    # Get the value for the specific dimension
    dimension_value = locals().get(budget_against_type.lower().replace(" ", "_"))

    if budget_against_type in dimension_map and dimension_value:
        query = query.where(dimension_map[budget_against_type] == dimension_value)

    result = query.run(as_dict=True)
    return result[0]["total_debit"] or 0
