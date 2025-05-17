import frappe
from collections import Counter

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	report_summary = get_report_summary(data)
	chart = get_chart(data)
	return columns, data, None, chart, report_summary

def get_columns():
	return [
		{"label": "Beneficiary", "fieldname": "name", "fieldtype": "Link", "options": "Beneficiary", "width": 180},
		{"label": "Student", "fieldname": "student", "fieldtype": "Data", "width": 180},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Beneficiary Type", "fieldname": "beneficiary_type", "fieldtype": "Data", "width": 140},
		{"label": "Program", "fieldname": "program", "fieldtype": "Data", "width": 160},
		{"label": "Start Date", "fieldname": "programme_start_date", "fieldtype": "Date", "width": 120},
		{"label": "End Date", "fieldname": "programme_end_date", "fieldtype": "Date", "width": 120},
		{"label": "Lead Donor", "fieldname": "lead_donor", "fieldtype": "Link", "options": "Donor", "width": 130},
		{"label": "Subdonor", "fieldname": "subdonor", "fieldtype": "Link", "options": "Donor", "width": 130},
		{"label": "Scholarship Status", "fieldname": "scholarship_status", "fieldtype": "Data", "width": 140},
		{"label": "Country", "fieldname": "program_country", "fieldtype": "Data", "width": 130},
		{"label": "State", "fieldname": "programme_state", "fieldtype": "Data", "width": 130},
		{"label": "County", "fieldname": "programme_county", "fieldtype": "Data", "width": 130},
		{"label": "Institution", "fieldname": "institution", "fieldtype": "Data", "width": 150},
		{"label": "Course", "fieldname": "course", "fieldtype": "Data", "width": 150},
		{"label": "Thematic Area", "fieldname": "thematic_area", "fieldtype": "Data", "width": 130},
	]

def get_data(filters):
	frappe_filters = {}

	# Direct filters
	for field in [
		"program", "lead_donor", "subdonor", "beneficiary_type", "status",
		"program_country", "programme_state", "programme_county",
		"institution", "course", "thematic_area"
	]:
		if filters.get(field):
			frappe_filters[field] = filters[field]

	# Date range filters
	if filters.get("start_date_from"):
		frappe_filters["programme_start_date"] = [">=", filters["start_date_from"]]
	if filters.get("start_date_to"):
		frappe_filters.setdefault("programme_start_date", []).append(["<=", filters["start_date_to"]])

	if filters.get("end_date_from"):
		frappe_filters["programme_end_date"] = [">=", filters["end_date_from"]]
	if filters.get("end_date_to"):
		frappe_filters.setdefault("programme_end_date", []).append(["<=", filters["end_date_to"]])

	# Flatten date range lists into AND condition filters
	date_filters = {}
	for key in ["programme_start_date", "programme_end_date"]:
		if isinstance(frappe_filters.get(key), list) and isinstance(frappe_filters[key][0], list):
			# Already in range form
			pass
		elif isinstance(frappe_filters.get(key), list) and len(frappe_filters[key]) == 2:
			date_filters.update({
				key: ("between", (frappe_filters[key][0], frappe_filters[key][1]))
			})
			del frappe_filters[key]

	frappe_filters.update(date_filters)

	# Get data using frappe ORM
	beneficiaries = frappe.get_all("Beneficiary",
		fields=[
			"name", "student", "program", "programme_start_date", "programme_end_date",
			"lead_donor", "subdonor", "scholarship_status",
			"program_country", "programme_state", "programme_county",
			"institution", "course", "thematic_area",
			"beneficiary_type", "status"
		],
		filters=frappe_filters,
		order_by="modified desc"
	)

	return beneficiaries

def get_report_summary(data):
	if not data:
		return []

	program_count = Counter(row.get("program") for row in data if row.get("program"))
	type_count = Counter(row.get("beneficiary_type") for row in data if row.get("beneficiary_type"))
	status_count = Counter(row.get("status") for row in data if row.get("status"))

	return [
		{"label": "Top Program", "value": max(program_count, key=program_count.get, default="N/A")},
		{"label": "Top Beneficiary Type", "value": max(type_count, key=type_count.get, default="N/A")},
		{"label": "Top Status", "value": max(status_count, key=status_count.get, default="N/A")},
		{"label": "Total Beneficiaries", "value": len(data)},
	]

def get_chart(data):
	if not data:
		return {}

	program_count = Counter(row.get("program") for row in data if row.get("program"))

	return {
		"data": {
			"labels": list(program_count.keys()),
			"datasets": [{
				"name": "Beneficiaries",
				"values": list(program_count.values())
			}]
		},
		"type": "bar",
		"colors": ["#34d399"]
	}
