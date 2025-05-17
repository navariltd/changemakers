# Copyright (c) 2025, hussain@frappe.io
# For license information, please see license.txt

import frappe
from collections import defaultdict

def execute(filters=None):
    report = DonorContributionReport(filters)
    return report.run()

class DonorContributionReport:
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.columns = []
		self.data = []
		self.chart = None
		self.report_summary = []

	def run(self):
		self.columns = self.get_columns()
		self.data = self.get_data()
		self.get_chart_data()
		self.get_report_summary()
		return self.columns, self.data, None, self.chart, self.report_summary

	def get_columns(self):
		columns = [
			{"label": "Donor", "fieldname": "donor", "fieldtype": "Link", "options": "Donor", "width": 150},
			{"label": "Donation", "fieldname": "donation", "fieldtype": "Link", "options": "Donation", "width": 230},
			{"label": "Donation Date", "fieldname": "date", "fieldtype": "Date", "width": 130}, 
		]

		if self.filters.get("show_total_pledged"):
			columns.append({"label": "Pledged Amount", "fieldname": "pledged_amount", "fieldtype": "Currency", "width": 150})

		if self.filters.get("show_total_paid"):
			columns.append({"label": "Total Paid Amount", "fieldname": "total_paid_amount", "fieldtype": "Currency", "width": 150})

		if self.filters.get("show_total_distributed"):
			columns.append({"label": "Total Distributed Amount", "fieldname": "amount_distributed", "fieldtype": "Currency", "width": 170})

		columns += [
			{"label": "Distribution", "fieldname": "distribution", "fieldtype": "Link", "options": "Donation Distribution", "width": 150},
			{"label": "Date Distributed", "fieldname": "distribution_date", "fieldtype": "Date", "width": 150},
			{"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 150},
			{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
			{"label": "Percentage", "fieldname": "percentage", "fieldtype": "Percent", "width": 120}, 
			{"label": "Beneficiary", "fieldname": "beneficiary", "fieldtype": "Link", "options": "Beneficiary", "width": 150},
			{"label": "Student", "fieldname": "student", "fieldtype": "Link", "options": "Student", "width": 150},
			{"label": "Learning Centre", "fieldname": "learning_centre", "fieldtype": "Link", "options": "Learning Centre", "width": 150},
			{"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 150},
			{"label": "Cost Center", "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 150},
			{"label": "Remarks", "fieldname": "remarks", "fieldtype": "Text", "width": 200},
		]

		return columns

	def get_data(self):
		filters = self.filters
		frappe_filters = {}
		item_filters = {}

		
		if filters.get("from_date"):
			frappe_filters["date"] = [">=", filters.get("from_date")]
		if filters.get("to_date"):
			frappe_filters.setdefault("date", []).extend(["<=", filters.get("to_date")])

		
		donation_filters = {}
		if filters.get("from_date"):
			donation_filters["date"] = [">=", filters["from_date"]]
		if filters.get("to_date"):
			donation_filters.setdefault("date", []).extend(["<=", filters["to_date"]])

		if filters.get("donor"):
			frappe_filters["donor"] = filters.get("donor")

		for key in ["beneficiary", "student"]:
			if filters.get(key):
				item_filters[key] = filters[key]

		if isinstance(frappe_filters.get("date"), list) and len(frappe_filters["date"]) > 2:
			dates = frappe_filters.pop("date")[1::2]
			frappe_filters["date"] = ["between", dates]

		distributions = frappe.get_all(
			"Donation Distribution",
			filters=frappe_filters,
			fields=["name", "donation", "donor", "total_amount", "date as distribution_date", "remarks"],
			order_by="donation, date ASC"
		)

		if not distributions:
			return []

		distribution_names = [d.name for d in distributions]
		item_filters["parent"] = ["in", distribution_names]

		items = frappe.get_all(
			"Donation Distribution Item",
			filters=item_filters,
			fields=["*"],  
			order_by="parent, idx"
		)

		items_by_distribution = defaultdict(list)
		for item in items:
			items_by_distribution[item.parent].append(item)

		distributions = [d for d in distributions if d.name in items_by_distribution]
		donation_names = list(set(d.donation for d in distributions))

		
		donations = frappe.get_all(
			"Donation",
			filters={"name": ["in", donation_names], **donation_filters},
			fields=["name", "donor", "amount as pledged_amount", "amount_distributed", "total_amount_paid", "date"],  
			order_by="creation DESC"
		)

		donation_map = {d.name: d for d in donations}
		donor_ids = list(set([d.donor for d in donations if d.donor]))

		donor_names = {}
		if donor_ids:
			for d in frappe.get_all("Donor", filters={"name": ["in", donor_ids]}, fields=["name", "donor_name"]):
				donor_names[d.name] = d.donor_name

		distributions_by_donation = defaultdict(list)
		for dist in distributions:
			distributions_by_donation[dist.donation].append(dist)

		data = []
		donations_by_donor = defaultdict(list)

		
		for donation in donations:
			donations_by_donor[donation.donor].append(donation)

		for donor, donor_donations in donations_by_donor.items():
			donor_name = donor_names.get(donor, "")
			first_donor_row = True

			for donation in donor_donations:
				dists = distributions_by_donation.get(donation.name, [])
				if not dists:
					continue

				first_dist = dists[0]
				first_items = items_by_distribution.get(first_dist.name, [])
				first_item = first_items[0] if first_items else None

				
				row = {
					"donation": donation.name,
					"date": donation.date,
					"donor": donor if first_donor_row else None,
					"donor_name": donor_name if first_donor_row else None,
					"pledged_amount": donation.pledged_amount,
					"total_paid_amount": donation.total_amount_paid ,
					"amount_distributed": donation.amount_distributed ,
					"distribution": first_dist.name,
					"distribution_date": first_dist.distribution_date,
					"total_amount": first_dist.total_amount,
					"amount": first_item.amount if first_item else None,
					"percentage": first_item.percentage if first_item else None,
					"beneficiary": first_item.beneficiary if first_item else None,
					"student": first_item.student if first_item else None,
					"learning_centre": first_item.learning_centre if first_item else None,
					"project": first_item.project if first_item else None,
					"cost_center": first_item.cost_center if first_item else None,
					"remarks": first_item.remarks if first_item else None,
					"indent": 0 if first_donor_row else 1,
					"is_group": 1,
					"bold": 1
				}
				data.append(row)
				first_donor_row = False 

				for item in first_items[1:]:
					data.append({
						"amount": item.amount,
						"percentage": item.percentage,
						"beneficiary": item.beneficiary,
						"student": item.student,
						"learning_centre": item.learning_centre,
						"project": item.project,
						"cost_center": item.cost_center,
						"remarks": item.remarks,
						"indent": 2
					})

				for dist in dists[1:]:
					items = items_by_distribution.get(dist.name, [])
					if not items:
						continue
					first_item = items[0]
					data.append({
						"distribution": dist.name,
						"distribution_date": dist.distribution_date,
						"total_amount": dist.total_amount,
						"remarks": dist.remarks,
						"amount": first_item.amount,
						"percentage": first_item.percentage,
						"beneficiary": first_item.beneficiary,
						"student": first_item.student,
						"learning_centre": first_item.learning_centre,
						"project": first_item.project,
						"cost_center": first_item.cost_center,
						"remarks": first_item.remarks,
						"indent": 2,
						"is_group": 1
					})
					for item in items[1:]:
						data.append({
							"amount": item.amount,
							"percentage": item.percentage,
							"beneficiary": item.beneficiary,
							"student": item.student,
							"learning_centre": item.learning_centre,
							"project": item.project,
							"cost_center": item.cost_center,
							"remarks": item.remarks,
							"indent": 3
						})


		return data

	def get_chart_data(self):
		summary = defaultdict(lambda: {"pledged": 0, "paid": 0, "distributed": 0})
		current_donor = None
		current_donor_name = None

		for row in self.data:
			indent = row.get("indent", 0)
			if indent == 0:
				current_donor = row.get("donor")
				current_donor_name = row.get("donor_name") or current_donor
				if current_donor_name:
					summary[current_donor_name]["pledged"] += row.get("pledged_amount", 0)
					summary[current_donor_name]["paid"] += row.get("total_paid_amount", 0)
			elif current_donor_name:
				summary[current_donor_name]["distributed"] += row.get("amount", 0)

		self.chart = {
			"data": {
				"labels": list(summary.keys()),
				"datasets": [
					{"name": "Pledged", "values": [v["pledged"] for v in summary.values()]},
					{"name": "Paid", "values": [v["paid"] for v in summary.values()]},
					{"name": "Distributed", "values": [v["distributed"] for v in summary.values()]}
				]
			},
			"type": "bar"
		}

	def get_report_summary(self):
		total_pledged = sum((row.get("pledged_amount") or 0) for row in self.data if row.get("indent", 0) == 0)
		total_paid = sum((row.get("total_paid_amount") or 0) for row in self.data if row.get("indent", 0) == 0)

		self.report_summary = [
			{"label": "Total Pledged Amount", "value": total_pledged, "indicator": "blue"},
			{"label": "Total Paid Amount", "value": total_paid, "indicator": "green"}
		]
