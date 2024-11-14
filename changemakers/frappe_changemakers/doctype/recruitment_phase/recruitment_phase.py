# Copyright (c) 2024, hussain@frappe.io and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class RecruitmentPhase(Document):
    pass


@frappe.whitelist()
def check_available_slots(phase_name):
    recruitment_phase = frappe.get_doc("Recruitment Phase", phase_name)
    branch_slot_details = {}

    for slot in recruitment_phase.slots:
        branch = slot.branch
        allocated_slots = slot.slots or 0
        active_beneficiary_count = frappe.db.count(
            "Beneficiary",
            {"status": "Active", "recruitment_phase": phase_name, "branch": branch},
        )
        available_slots = max(allocated_slots - active_beneficiary_count, 0)

        branch_slot_details[branch] = {
            "slots": allocated_slots,
            "active_beneficiaries": active_beneficiary_count,
            "available_slots": available_slots,
        }

        if active_beneficiary_count > allocated_slots:
            frappe.throw(
                _(
                    "Allocated slots exceeded for {0} branch. Active Beneficiaries: {1}, Allocated Slots: {2}"
                ).format(branch, active_beneficiary_count, allocated_slots)
            )

        slot.available_slots = available_slots

    return branch_slot_details
