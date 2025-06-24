# Copyright (c) 2025, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from datetime import datetime, timedelta
from frappe.query_builder import DocType
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
            "fieldname": "actual_amount",
            "fieldtype": "Currency",
            "label": "Actual Amount",
            "width": 150,
        },
        {
            "fieldname": "variance_amount",
            "fieldtype": "Currency",
            "label": "Variance",
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
            "label": "Percentage (Monthly Avg.)",
            "width": 200,
        },
    ]

    sorted_months = get_sorted_months_from_fiscal_years(filters)
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
    GL_Entry = DocType("GL Entry")

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
        # Apply specific budget_against filters
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
            .select(Sum(BudgetAccount.budget_amount).as_("total_amount"))
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

        # Initialize total actuals for the main budget row
        total_actual_amount_for_budget = 0

        # --- PROCESS ACCOUNTS AND THEIR ACTUALS/VARIANCES ---
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

            # --- FETCH ACTUAL AMOUNT FOR THIS ACCOUNT ---
            actual_amount_for_account = get_actual_expenses_for_account(
                account.account,
                fiscal_year_start_date,
                fiscal_year_end_date,
                budget.budget_against,
                budget.employee,
                budget.project,
                budget.task,
                budget.cost_center,
                budget.program,
            )
            # Add to total actuals for the parent budget
            total_actual_amount_for_budget += actual_amount_for_account

            variance_for_account = account.budget_amount - actual_amount_for_account

            data.append(
                {
                    "budget_name": "",
                    "budget_against": "",
                    "name": "",
                    "donor": "",
                    "donation": "",
                    "amount": "",
                    "budget_account": account.account,
                    "budget_amount": account.budget_amount,
                    "actual_amount": actual_amount_for_account,  # Actual for this account
                    "variance_amount": variance_for_account,  # Variance for this account
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
            if filters and filters.get("donation_allocation"):
                allocations_query = allocations_query.where(
                    BudgetDonationAllocationItem.donation_allocation
                    == filters["donation_allocation"]
                )

            allocations = allocations_query.run(as_dict=True)

            for alloc in allocations:
                allocation_month_data = {
                    frappe.scrub(month_label): "" for month_label in sorted_months
                }
                data.append(
                    {
                        "donor": alloc.donor,
                        "donation": alloc.donation,
                        "allocation": alloc.donation_allocation,
                        "amount": alloc.amount,
                        **allocation_month_data,
                    }
                )

        variance_for_budget = total_budget_amount - total_actual_amount_for_budget

        data.insert(
            (
                len(budgets) - 1
                if budgets.index(budget) == 0
                else data.index(data[-1]) + 1
            ),
            {
                "budget_name": budget.budget_name,
                "budget_against": budget.budget_against,
                "name": name,
                "donor": "",
                "donation": "",
                "amount": "",
                "budget_account": "",
                "budget_amount": total_budget_amount,
                "actual_amount": total_actual_amount_for_budget,
                "variance_amount": variance_for_budget,
                "months_distributed": months_distributed,
                "percentage": percentage,
                **month_data_amounts,
            },
        )

    final_report_data = []
    processed_budget_names = set()

    for budget in budgets:
        if budget.budget_name in processed_budget_names:
            continue  # Already added the main budget row and its children

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

        distribution_dict_percentages = {}
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
                            f"Could not determine year for month '{row['month']}' in Fiscal Year '{budget.fiscal_year}'",
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

        total_budget_amount_query = (
            frappe.qb.from_(BudgetAccount)
            .select(Sum(BudgetAccount.budget_amount).as_("total_amount"))
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

        total_actual_amount_for_budget = 0

        current_budget_accounts_data = []

        accounts_query = (
            frappe.qb.from_(BudgetAccount)
            .select(
                BudgetAccount.account,
                BudgetAccount.budget_amount,
            )
            .where(BudgetAccount.parent == budget.budget_name)
            .where(BudgetAccount.parenttype == "Budget")
        )
        if filters and filters.get("budget_account"):
            accounts_query = accounts_query.where(
                BudgetAccount.account == filters["budget_account"]
            )
        accounts = accounts_query.run(as_dict=True)

        for account in accounts:
            account_monthly_amounts = {}
            for (
                month_label_scrubbed,
                percentage_value,
            ) in distribution_dict_percentages.items():
                account_monthly_amounts[month_label_scrubbed] = (
                    percentage_value / 100
                ) * account.budget_amount

            actual_amount_for_account = get_actual_expenses_for_account(
                account.account,
                fiscal_year_start_date,
                fiscal_year_end_date,
                budget.budget_against,
                budget.employee,
                budget.project,
                budget.task,
                budget.cost_center,
                budget.program,
            )
            total_actual_amount_for_budget += actual_amount_for_account

            variance_for_account = account.budget_amount - actual_amount_for_account

            current_budget_accounts_data.append(
                {
                    "budget_name": "",
                    "budget_against": "",
                    "name": "",
                    "donor": "",
                    "donation": "",
                    "amount": "",
                    "budget_account": account.account,
                    "budget_amount": account.budget_amount,
                    "actual_amount": actual_amount_for_account,
                    "variance_amount": variance_for_account,
                    "months_distributed": "",
                    "percentage": "",
                    **account_monthly_amounts,
                }
            )

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
            if filters and filters.get("donation_allocation"):
                allocations_query = allocations_query.where(
                    BudgetDonationAllocationItem.donation_allocation
                    == filters["donation_allocation"]
                )
            allocations = allocations_query.run(as_dict=True)

            for alloc in allocations:
                allocation_month_data = {
                    frappe.scrub(month_label): "" for month_label in sorted_months
                }
                current_budget_accounts_data.append(
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
                        "months_distributed": "",
                        "percentage": "",
                        **allocation_month_data,
                    }
                )

        variance_for_budget = total_budget_amount - total_actual_amount_for_budget

        final_report_data.append(
            {
                "budget_name": budget.budget_name,
                "budget_against": budget.budget_against,
                "name": name,
                "donor": "",
                "donation": "",
                "amount": "",
                "budget_account": "",
                "budget_amount": total_budget_amount,
                "actual_amount": total_actual_amount_for_budget,
                "variance_amount": variance_for_budget,
                "months_distributed": months_distributed,
                "percentage": percentage,
                **month_data_amounts,
            }
        )
        final_report_data.extend(current_budget_accounts_data)
        processed_budget_names.add(budget.budget_name)  # Mark budget as processed

    return final_report_data


def get_actual_expenses_for_account(
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
    GL_Entry = DocType("GL Entry")

    query = (
        frappe.qb.from_(GL_Entry)
        .select(Sum(GL_Entry.debit).as_("total_debit"))
        .where(GL_Entry.account == account)
        .where(GL_Entry.posting_date.between(start_date, end_date))
        .where(GL_Entry.is_cancelled == 0)  # Exclude cancelled entries
    )

    # Apply dimensional filters based on budget_against_type
    if budget_against_type == "Employee" and employee:
        query = query.where(GL_Entry.employee == employee)
    elif budget_against_type == "Project" and project:
        query = query.where(GL_Entry.project == project)
    elif budget_against_type == "Task" and task:
        query = query.where(GL_Entry.task == task)
    elif budget_against_type == "Cost Center" and cost_center:
        query = query.where(GL_Entry.cost_center == cost_center)
    elif budget_against_type == "Program" and program:
        query = query.where(GL_Entry.program == program)

    result = query.run(as_dict=True)
    return (
        result[0]["total_debit"]
        if result and result[0]["total_debit"] is not None
        else 0
    )
