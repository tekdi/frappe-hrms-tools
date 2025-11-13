"""
Configuration for CV Analyzer module
"""

from frappe import _


def get_data():
    return [
        {
            "label": _("CV Analysis"),
            "items": [
                {
                    "type": "doctype",
                    "name": "CV Analysis Result",
                    "label": _("CV Analysis Results"),
                    "description": _("View CV analysis results"),
                },
                {
                    "type": "doctype",
                    "name": "Position Evaluation Framework",
                    "label": _("Position Frameworks"),
                    "description": _("Manage position-specific evaluation criteria"),
                },
                {
                    "type": "doctype",
                    "name": "Company Evaluation Criteria",
                    "label": _("Company Criteria"),
                    "description": _("Manage company-wide evaluation standards"),
                },
            ],
        },
        {
            "label": _("Settings"),
            "items": [
                {
                    "type": "doctype",
                    "name": "CV Analysis Settings",
                    "label": _("CV Analysis Settings"),
                    "description": _("Configure CV analysis service connection"),
                },
            ],
        },
    ]
