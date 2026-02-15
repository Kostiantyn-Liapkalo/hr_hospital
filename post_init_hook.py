# -*- coding: utf-8 -*-

def _post_init_hook(cr, registry):
    """Post initialization hook for the Hospital module"""

    # Create indexes to improve database performance
    queries = [
        # Doctor indexes
        "CREATE INDEX IF NOT EXISTS idx_doctor_full_name ON hr_hospital_doctor (last_name, first_name)",
        "CREATE INDEX IF NOT EXISTS idx_doctor_license ON hr_hospital_doctor (license_number)",
        "CREATE INDEX IF NOT EXISTS idx_doctor_speciality ON hr_hospital_doctor (speciality_id)",
        "CREATE INDEX IF NOT EXISTS idx_doctor_intern ON hr_hospital_doctor (is_intern)",

        # Patient indexes
        "CREATE INDEX IF NOT EXISTS idx_patient_full_name ON hr_hospital_patient (last_name, first_name)",
        "CREATE INDEX IF NOT EXISTS idx_patient_doctor ON hr_hospital_patient (personal_doctor_id)",
        "CREATE INDEX IF NOT EXISTS idx_patient_passport ON hr_hospital_patient (passport)",
        "CREATE INDEX IF NOT EXISTS idx_patient_country ON hr_hospital_patient (country_id)",

        # Visit indexes
        "CREATE INDEX IF NOT EXISTS idx_visit_datetime ON hr_hospital_visit (planned_datetime)",
        "CREATE INDEX IF NOT EXISTS idx_visit_state ON hr_hospital_visit (state)",
        "CREATE INDEX IF NOT EXISTS idx_visit_patient_doctor_date ON hr_hospital_visit (patient_id, doctor_id, (planned_datetime::date))",

        # Diagnosis indexes
        "CREATE INDEX IF NOT EXISTS idx_diagnosis_date ON hr_hospital_diagnosis (diagnosis_date)",
        "CREATE INDEX IF NOT EXISTS idx_diagnosis_approved ON hr_hospital_diagnosis (is_approved)",
        "CREATE INDEX IF NOT EXISTS idx_diagnosis_disease ON hr_hospital_diagnosis (disease_id)",
        "CREATE INDEX IF NOT EXISTS idx_diagnosis_patient_doctor ON hr_hospital_diagnosis (patient_id, doctor_id)",
    ]

    for query in queries:
        cr.execute(query)