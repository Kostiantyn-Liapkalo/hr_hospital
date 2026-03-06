Hospital Automation System
==========================

Complete hospital management system for Odoo 19.0

.. image:: https://img.shields.io/badge/version-19.0.2.0.0-blue.svg
   :target: https://github.com/kostiantyn-liapkalo/hr_hospital
.. image:: https://img.shields.io/badge/license-LGPL--3-green.svg
   :target: https://www.gnu.org/licenses/lgpl-3.0.en.html

Overview
--------

Hospital Automation is a professional hospital management system designed for healthcare institutions. It provides comprehensive tools for managing doctors, patients, visits, diagnoses, and medical records efficiently.

Features
--------

Doctor Management
~~~~~~~~~~~~~~~~~

* Comprehensive doctor profiles with specialties
* License tracking and validation
* Intern and mentor relationships
* Doctor ratings and experience tracking
* Schedule management

Patient Management
~~~~~~~~~~~~~~~~~~~

* Complete patient records
* Personal doctor assignment
* Medical history tracking
* Blood group and allergy records
* Emergency contact management

Visit Scheduling
~~~~~~~~~~~~~~~~

* Appointment booking system
* Visit status tracking (Planned, In Progress, Completed, Cancelled)
* Automatic doctor availability check
* Visit history with diagnoses

Diagnosis & Disease
~~~~~~~~~~~~~~~~~~~~

* Disease classification with ICD-10 codes
* Hierarchical disease categories
* Diagnosis approval workflow
* Severity level tracking

Security & Access Control
--------------------------

Role-based access control with 5 user levels:

**Patient**: View own visits and medical history

**Intern**: Create and manage own patient visits

**Doctor**: Full patient management, manage own and intern visits

**Manager**: View all visits, manage doctors, view reports

**Administrator**: Complete control including data deletion

Reporting & Visualization
--------------------------

* Professional PDF reports for doctors (A4 format)
* Visual kanban board for doctors
* Quick visit creation buttons
* Statistics badges

Technical Features
------------------

* Full Ukrainian translation support
* Multi-language ready
* Comprehensive test coverage
* Unit tests for critical methods

Installation
------------

1. Install the module from Apps menu
2. Configure user groups in Settings > Users & Companies
3. Set up company information for reports (logo, address, contacts)
4. Configure disease classifications
5. Create doctor specialties
6. Start managing patients and visits!

Dependencies
------------

* base
* contacts
* mail

Configuration
-------------

User Groups
~~~~~~~~~~~

Assign users to appropriate groups:

1. Go to Settings > Users & Companies > Users
2. Select a user
3. In "Hospital Automation" section, assign appropriate group

Company Information
~~~~~~~~~~~~~~~~~~~

For reports to display correctly:

1. Go to Settings > Users & Companies > Companies
2. Upload company logo
3. Set company address and contact information

Usage
-----

Doctors
~~~~~~~

* Create doctors with specialties and licenses
* Assign interns to mentors
* Track doctor experience and ratings

Patients
~~~~~~~~

* Register patients with complete medical profiles
* Assign personal doctors
* Track patient history

Visits
~~~~~~

* Schedule appointments
* Track visit status
* Add diagnoses to visits

Diagnoses
~~~~~~~~~

* Create diagnoses linked to visits
* Approve diagnoses (for doctors)
* Track disease severity

Bug Tracker
-----------

Bugs are tracked on GitHub Issues. In case of trouble, please check there if your issue has already been reported.

Credits
-------

Author
~~~~~~

* Kostiantyn Liapkalo <https://github.com/kostiantyn-liapkalo>

Maintainer
~~~~~~~~~~

This module is maintained by Kostiantyn Liapkalo.

License
-------

This module is licensed under the LGPL-3 License.

.. seealso::

   :alt: Odoo Community Association
   `Odoo Community Association <https://odoo-community.org/>`__
