# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta
from frappe.query_builder import DocType

# Import Sum directly from frappe.query_builder.functions
from frappe.query_builder.functions import Count, Sum


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters=None):
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
            "label": "Percentage (Monthly Avg.)",  # Changed label for clarity
            "width": 100,
        },
    ]

    sorted_months = get_sorted_months_from_fiscal_years(filters)
    for month_label in sorted_months:
        columns.append(
            {
                "fieldname": frappe.scrub(month_label),
                "fieldtype": "Currency",  # Changed to Currency
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
        Budget = DocType("Budget")
        MonthlyDistribution = DocType("Monthly Distribution")

        budget_fiscal_years_query = (
            frappe.qb.from_(Budget)
            .join(MonthlyDistribution)
            .on(Budget.monthly_distribution == MonthlyDistribution.name)
            .select(MonthlyDistribution.fiscal_year)
            .where(MonthlyDistribution.fiscal_year.isnotnull())
            .where(MonthlyDistribution.fiscal_year != "")
            .distinct()
        )
        # Apply budget_name filter if present, to only consider fiscal years of filtered budgets
        if filters and filters.get("budget_name"):
            budget_fiscal_years_query = budget_fiscal_years_query.where(
                Budget.name == filters["budget_name"]
            )

        budget_fiscal_years = budget_fiscal_years_query.run(as_list=True)

        for fy in budget_fiscal_years:
            fiscal_year_names.append(fy[0])

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

            next_month = current_date.replace(day=28) + timedelta(days=4)
            current_date = next_month.replace(day=1)

    sorted_months = sorted(
        list(unique_month_labels), key=lambda x: month_datetime_map[x]
    )
    return sorted_months


def get_data(filters=None):
    Budget = DocType("Budget")
    MonthlyDistribution = DocType("Monthly Distribution")
    BudgetDonationAllocationItem = DocType("Budget Donation Allocation Item")
    BudgetAccount = DocType("Budget Account")

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

    # Apply filters
    if filters:
        if filters.get("fiscal_year"):
            budgets_query = budgets_query.where(
                MonthlyDistribution.fiscal_year == filters["fiscal_year"]
            )
        if filters.get("budget_against"):
            budgets_query = budgets_query.where(
                Budget.budget_against == filters["budget_against"]
            )
        if filters.get("budget_against"):
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
            # Subquery to find Budget names associated with the selected Budget Account
            budgets_with_account = (
                frappe.qb.from_(BudgetAccount)
                .select(BudgetAccount.parent)
                .where(BudgetAccount.account == filters["budget_account"])
                .where(BudgetAccount.parenttype == "Budget")
                .distinct()
            )
            budgets_query = budgets_query.where(Budget.name.isin(budgets_with_account))

        if filters.get("donor"):
            # Subquery to find Budget names associated with the selected Donor
            budgets_with_donor = (
                frappe.qb.from_(BudgetDonationAllocationItem)
                .select(BudgetDonationAllocationItem.parent)
                .where(BudgetDonationAllocationItem.donor == filters["donor"])
                .distinct()
            )
            budgets_query = budgets_query.where(Budget.name.isin(budgets_with_donor))

        if filters.get("donation"):
            # Subquery to find Budget names associated with the selected Donation
            budgets_with_donation = (
                frappe.qb.from_(BudgetDonationAllocationItem)
                .select(BudgetDonationAllocationItem.parent)
                .where(BudgetDonationAllocationItem.donation == filters["donation"])
                .distinct()
            )
            budgets_query = budgets_query.where(Budget.name.isin(budgets_with_donation))

        if filters.get("donation_allocation"):
            # Subquery to find Budget names associated with the selected Donation Allocation
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

    budgets = budgets_query.run(as_dict=True)

    data = []
    sorted_months = get_sorted_months_from_fiscal_years(filters)
    fiscal_year_cache = {}

    for budget in budgets:
        fiscal_year_start_date = None
        fiscal_year_end_date = None
        if budget.fiscal_year:
            if budget.fiscal_year not in fiscal_year_cache:
                fiscal_year_doc = frappe.get_cached_doc(
                    "Fiscal Year", budget.fiscal_year
                )
                fiscal_year_cache[budget.fiscal_year] = {
                    "start_date": fiscal_year_doc.year_start_date,
                    "end_date": fiscal_year_doc.year_end_date,
                }
            fiscal_year_start_date = fiscal_year_cache[budget.fiscal_year]["start_date"]
            fiscal_year_end_date = fiscal_year_cache[budget.fiscal_year]["end_date"]

        MonthlyDistributionPercentage = DocType("Monthly Distribution Percentage")

        months_distributed_query = (
            frappe.qb.from_(MonthlyDistributionPercentage)
            .select(Count("*").as_("cnt"))
            .where(MonthlyDistributionPercentage.parent == budget.monthly_distribution)
        )
        months_distributed = months_distributed_query.run(as_dict=True)[0]["cnt"] or 0

        distribution_rows_query = (
            frappe.qb.from_(MonthlyDistributionPercentage)
            .select(
                MonthlyDistributionPercentage.month,
                MonthlyDistributionPercentage.percentage_allocation,
            )
            .where(MonthlyDistributionPercentage.parent == budget.monthly_distribution)
            .orderby(MonthlyDistributionPercentage.month)
        )
        distribution_rows = distribution_rows_query.run(as_dict=True)

        distribution_dict_percentages = {}  # Store percentages
        for row in distribution_rows:
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
                        next_month = current_fy_date.replace(day=28) + timedelta(days=4)
                        current_fy_date = next_month.replace(day=1)

                    if found_year:
                        full_month_label = f"{row['month']} {found_year}"
                        distribution_dict_percentages[
                            frappe.scrub(full_month_label)
                        ] = row["percentage_allocation"]
                    else:
                        frappe.log_error(
                            f"Could not determine year for month '{row['month']}' in Fiscal Year '{budget.fiscal_year}' (FY Dates: {fiscal_year_start_date} - {fiscal_year_end_date})",
                            "Month Year Mismatch",
                        )
                        distribution_dict_percentages[frappe.scrub(row["month"])] = row[
                            "percentage_allocation"
                        ]
                except ValueError:
                    frappe.log_error(
                        f"Invalid month name '{row['month']}' in Monthly Distribution Percentage for parent {budget.monthly_distribution}",
                        "Invalid Month Name Format",
                    )
                    distribution_dict_percentages[frappe.scrub(row["month"])] = row[
                        "percentage_allocation"
                    ]
            else:
                distribution_dict_percentages[frappe.scrub(row["month"])] = row[
                    "percentage_allocation"
                ]

        # Fetch the sum of budget_amount for the current budget
        total_budget_amount_query = (
            frappe.qb.from_(BudgetAccount)
            .select(Sum(BudgetAccount.budget_amount).as_("total_amount"))  # Fixed here
            .where(BudgetAccount.parent == budget.budget_name)
            .where(BudgetAccount.parenttype == "Budget")
        )
        total_budget_amount_result = total_budget_amount_query.run(as_dict=True)
        total_budget_amount = (
            total_budget_amount_result[0]["total_amount"]
            if total_budget_amount_result
            and total_budget_amount_result[0]["total_amount"] is not None
            else 0
        )

        # Calculate monthly amounts
        month_data_amounts = {}
        for (
            month_label_scrubbed,
            percentage_value,
        ) in distribution_dict_percentages.items():
            month_data_amounts[month_label_scrubbed] = (
                percentage_value / 100
            ) * total_budget_amount

        percentage = 100 / months_distributed if months_distributed > 0 else 0

        name = ""
        if budget.budget_against == "Employee":
            name = frappe.db.get_value("Employee", budget.get("employee"), "first_name")
        elif budget.budget_against == "Project":
            name = frappe.db.get_value("Project", budget.get("project"), "project_name")
        elif budget.budget_against == "Task":
            name = frappe.db.get_value("Task", budget.get("task"), "subject")
        elif budget.budget_against == "Cost Center":
            name = frappe.db.get_value("Cost Center", budget.get("cost_center"), "name")
        elif budget.budget_against == "Program":
            name = frappe.db.get_value("Program", budget.get("program"), "name")

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
                "budget_amount": total_budget_amount,  # Display the sum of budget_amount here
                "months_distributed": months_distributed,
                "percentage": percentage,
                **month_data_amounts,  # Use calculated amounts
            }
        )

        BudgetAccount = DocType("Budget Account")
        accounts_query = (
            frappe.qb.from_(BudgetAccount)
            .select(
                BudgetAccount.account,
                BudgetAccount.budget_amount,
            )
            .where(BudgetAccount.parent == budget.budget_name)
            .where(BudgetAccount.parenttype == "Budget")
        )
        # Apply budget_account filter to accounts_query
        if filters and filters.get("budget_account"):
            accounts_query = accounts_query.where(
                BudgetAccount.account == filters["budget_account"]
            )

        accounts = accounts_query.run(as_dict=True)

        for account in accounts:
            # For account rows, the monthly distribution should be based on the account's budget_amount
            account_monthly_amounts = {}
            for (
                month_label_scrubbed,
                percentage_value,
            ) in distribution_dict_percentages.items():
                account_monthly_amounts[month_label_scrubbed] = (
                    percentage_value / 100
                ) * account.budget_amount

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
                    **account_monthly_amounts,  # Use calculated amounts for accounts
                }
            )

            BudgetDonationAllocationItem = DocType("Budget Donation Allocation Item")
            allocations_query = (
                frappe.qb.from_(BudgetDonationAllocationItem)
                .select(
                    BudgetDonationAllocationItem.donation_allocation,
                    BudgetDonationAllocationItem.amount,
                    BudgetDonationAllocationItem.donor,
                    BudgetDonationAllocationItem.donation,
                )
                .where(BudgetDonationAllocationItem.parent == budget.budget_name)
                .where(BudgetDonationAllocationItem.parenttype == "Budget")
                .where(BudgetDonationAllocationItem.account == account.account)
            )
            # Apply donation_allocation filter to allocations_query
            if filters and filters.get("donation_allocation"):
                allocations_query = allocations_query.where(
                    BudgetDonationAllocationItem.donation_allocation
                    == filters["donation_allocation"]
                )

            allocations = allocations_query.run(as_dict=True)

            for alloc in allocations:
                # For allocation rows, monthly amounts are not directly calculated from percentages.
                # They represent the actual allocated amount for that specific allocation.
                # So we leave the monthly amount columns empty for these rows, or you might
                # consider distributing 'alloc.amount' if that's the business logic.
                # For now, I'll keep them empty as the request focuses on budget distribution.
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
