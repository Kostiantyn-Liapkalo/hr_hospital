Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[19.0.2.0.0] - 2026-03-06
-------------------------

Added
~~~~~~~

* **Doctor Report**: Professional PDF report for doctors including:
  * Company logo and contact information in header
  * Doctor's personal and professional details
  * Statistics section
  * Visit history in reverse chronological order
  * Patient list with visit status color-coded badges
  * A4 paper format optimized

* **Enhanced Kanban View**: Improved kanban view for doctors displaying:
  * First name and last name
  * Specialty
  * List of interns (if mentor)
  * Quick visit creation buttons
  * Standard control menu with edit/delete options

* **User Groups & Security**: Implemented hierarchical user groups:
  * Patient - view only own visits
  * Intern - view and edit own visits
  * Doctor - manage own and intern visits
  * Manager - view all visits
  * Administrator - full access with delete permissions

* **Record Rules**: Added record-level access control for visits based on user groups

* **Ukrainian Translation**: Complete Ukrainian localization including:
  * All model names and fields
  * Menu items and actions
  * Reports and templates
  * Security groups and rules
  * Disease classifier entries

* **Unit Tests**: Added comprehensive test coverage for:
  * Doctor toggle_active method
  * Doctor action_create_quick_visit_from_doctor method
  * Doctor _compute_upcoming_visits_count method
  * Visit get_available_visit_dates method
  * Existing constraint and workflow tests

* **Module Documentation**: Created detailed module description with:
  * Feature overview
  * Security matrix
  * Installation instructions
  * Technical specifications

Changed
~~~~~~~~

* Updated manifest to include new security and report files
* Enhanced existing views with additional functionality
* Improved code quality based on pylint recommendations

Security
~~~~~~~~~~

* Implemented role-based access control with 5 user levels
* Added record rules restricting visit visibility per user group
* Defined group inheritance: Patient < Intern < Doctor < Manager < Administrator

Technical
~~~~~~~~~~

* Added security files:
  * ``security/hr_hospital_groups.xml`` - user group definitions
  * ``security/hr_hospital_security_rules.xml`` - record access rules
  * ``security/ir.model.access.csv`` - model access rights

* Added report files:
  * ``reports/hr_hospital_doctor_report.xml`` - report action
  * ``reports/hr_hospital_doctor_report_templates.xml`` - QWeb template

* Added translation:
  * ``i18n/uk_UA.po`` - Ukrainian translations

* Added tests:
  * ``tests/test_hr_hospital_models.py`` - extended with new test methods

* Updated documentation:
  * ``static/description/index.html`` - comprehensive module description
  * ``README.rst`` - module documentation in reStructuredText format

[19.0.1.0.0] - 2024-XX-XX
-------------------------

Initial release of Hospital Automation module.

Added
~~~~~~~

* **Core Models**:
  * Doctor management with specialties and schedules
  * Patient management with medical history
  * Visit tracking and appointment system
  * Diagnosis recording and approval workflow
  * Disease classification with ICD-10 codes
  * Contact person management

* **Views**:
  * List, form, and search views for all models
  * Calendar view for visits
  * Basic kanban view for doctors

* **Wizards**:
  * Mass doctor reassignment
  * Disease report generation
  * Visit rescheduling
  * Patient card export
  * Doctor schedule management

* **Demo Data**:
  * Sample doctors with specialties
  * Sample patients with medical records
  * Sample visits and diagnoses
  * Disease classifications
  * Doctor schedules

* **Security**:
  * Basic access rights configuration
  * Model-level permissions

Dependencies
~~~~~~~~~~~~~~

* base
* contacts
* mail
