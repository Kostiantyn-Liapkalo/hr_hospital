{
    'name': 'Hospital Automation',
    'summary': 'Manage doctors, patients, diseases and visits',
    'description': """
        Hospital Automation Module
        ==========================
        This module provides hospital management functionality.
    """,
    'author': 'Kostiantyn Liapkalo',
    'website': 'https://github.com/kostiantyn-liapkalo',
    'category': 'Human Resources',
    'version': '19.0.2.0.0',
    'depends': ['base', 'contacts', 'mail'],
    'data': [
        'security/ir.model.access.csv',

        'data/hr_hospital_sequence_data.xml',
        'data/hr_hospital_doctor_speciality_data.xml',
        'data/hr_hospital_disease_data.xml',

        'views/hr_hospital_abstract_person_views.xml',
        'views/hr_hospital_contact_person_views.xml',
        'views/hr_hospital_disease_views.xml',
        'views/hr_hospital_doctor_views.xml',
        'views/hr_hospital_doctor_speciality_views.xml',
        'views/hr_hospital_doctor_schedule_views.xml',
        'views/hr_hospital_patient_views.xml',
        'views/hr_hospital_patient_doctor_history_views.xml',
        'views/hr_hospital_visit_views.xml',
        'views/hr_hospital_diagnosis_views.xml',

        'wizards/hr_hospital_mass_reassign_doctor_wizard_views.xml',
        'wizards/hr_hospital_disease_report_wizard_views.xml',
        'wizards/hr_hospital_reschedule_visit_wizard_views.xml',
        'wizards/hr_hospital_doctor_schedule_wizard_views.xml',
        'wizards/hr_hospital_patient_card_export_wizard_views.xml',

        'views/menu.xml',

    ],
    'demo': [
        'demo/hr_hospital_doctor_speciality_demo.xml',
        'demo/hr_hospital_doctor_demo.xml',
        'demo/hr_hospital_patient_demo.xml',
        'demo/hr_hospital_disease_demo.xml',
        'demo/hr_hospital_visit_demo.xml',
        'demo/hr_hospital_diagnosis_demo.xml',
        'demo/hr_hospital_doctor_schedule_demo.xml',
        'demo/hr_hospital_patient_history_demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'],
    'post_init_hook': '_post_init_hook',
}