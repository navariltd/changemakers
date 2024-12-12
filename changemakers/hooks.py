from . import __version__ as app_version

app_name = "changemakers"
app_title = "Frappe Changemakers"
app_publisher = "hussain@frappe.io"
app_description = "Empowering the people that do good."
app_email = "hussain@frappe.io"
app_license = "AGPL"


fixtures = [
    "Custom HTML Block",
    "Case Type",
    "State",
    "Payment Type",
    {"dt": "Client Script", "filters": {"name": "Action: Create User Profile"}},
    {
        "dt": "Role",
        "filters": {
            "role_name": (
                "in",
                [
                    "Social Worker",
                    "Shelter Team Member",
                    "Healthcare Team Member",
                    "Food Team Member",
                    "SMT(NGO)-Field Co-ordinator",
                    "Medical Co-ordinator",
                    "Program Manager",
                    "Partner SMT",
                    "Data MIS/Documentation (Admin)",
                ],
            )
        },
    },
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                (
                    "Project",
                    "Stock Entry",
                ),
            ],
            ["is_system_generated", "=", 0],
            ["module", "=", "Frappe Changemakers"],
        ],
    },
]

accounting_dimension_doctypes = [
    "Beneficiary",
    "Donor"
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/changemakers/css/changemakers.css"
app_include_js = "/assets/changemakers/js/changemakers.js"

website_route_rules = [
    {"from_route": "/c/<path:app_path>", "to_route": "c"},
]

# include js, css files in header of web template
# web_include_css = "/assets/changemakers/css/changemakers.css"
# web_include_js = "/assets/changemakers/js/changemakers.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "changemakers/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Stock Entry": "frappe_changemakers/overrides/stock_entry.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "changemakers.utils.jinja_methods",
# 	"filters": "changemakers.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "changemakers.install.before_install"
after_install = "changemakers.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "changemakers.uninstall.before_uninstall"
# after_uninstall = "changemakers.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "changemakers.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "User": {
        "after_insert": "changemakers.frappe_changemakers.doctype.changemakers_user_profile.changemakers_user_profile.create_user_profile",
        "on_trash": [
            "changemakers.frappe_changemakers.doctype.changemakers_user_profile.changemakers_user_profile.delete_user_profile",
        ],
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"changemakers.tasks.all"
# 	],
# 	"daily": [
# 		"changemakers.tasks.daily"
# 	],
# 	"hourly": [
# 		"changemakers.tasks.hourly"
# 	],
# 	"weekly": [
# 		"changemakers.tasks.weekly"
# 	],
# 	"monthly": [
# 		"changemakers.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "changemakers.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "changemakers.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "changemakers.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"changemakers.auth.validate"
# ]
