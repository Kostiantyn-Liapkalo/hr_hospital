# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
class TestHrHospitalModels(TransactionCase):
    """Test cases for HR Hospital module models"""
    def setUp(self):
        super(TestHrHospitalModels, self).setUp()
        # Create test data
        self.specialty = self.env['hr.hospital.doctor.speciality'].create({
            'name': 'Test Specialty',
            'code': 'TEST001',
            'description': 'Test specialty description'
        })
        self.doctor = self.env['hr.hospital.doctor'].create({
            'first_name': 'John',
            'last_name': 'Doe',
            'speciality_id': self.specialty.id,
            'license_number': 'TEST123456',
            'license_date': '2020-01-01'
        })
        self.patient = self.env['hr.hospital.patient'].create({
            'first_name': 'Jane',
            'last_name': 'Smith',
            'personal_doctor_id': self.doctor.id,
            'passport': '1234567890'
        })
    def test_abstract_person_validation(self):
        """Test abstract person validation"""
        # Test phone validation
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.patient'].create({
                'first_name': 'Test',
                'last_name': 'User',
                'phone': 'invalid-phone'
            })
        # Test email validation
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.patient'].create({
                'first_name': 'Test',
                'last_name': 'User',
                'email': 'invalid-email'
            })
    def test_doctor_constraints(self):
        """Test doctor model constraints"""
        # Test unique license number
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.doctor'].create({
                'first_name': 'Another',
                'last_name': 'Doctor',
                'speciality_id': self.specialty.id,
                'license_number': 'TEST123456',  # Same as existing
                'license_date': '2020-01-01'
            })
        # Test rating validation
        with self.assertRaises(ValidationError):
            self.doctor.write({'rating': 6.0})  # Above 5.0
    def test_patient_constraints(self):
        """Test patient model constraints"""
        # Test unique passport
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.patient'].create({
                'first_name': 'Another',
                'last_name': 'Patient',
                'passport': '1234567890'  # Same as existing
            })
    def test_visit_constraints(self):
        """Test visit model constraints"""
        # Test unique visit per day
        visit_date = '2024-01-01 10:00:00'
        # Create first visit
        self.env['hr.hospital.visit'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'planned_datetime': visit_date,
            'visit_type': 'first'
        })
        # Try to create second visit same day
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.visit'].create({
                'patient_id': self.patient.id,
                'doctor_id': self.doctor.id,
                'planned_datetime': '2024-01-01 14:00:00',
                'visit_type': 'follow_up'
            })
    def test_doctor_schedule_constraints(self):
        """Test doctor schedule constraints"""
        # Test time validation
        with self.assertRaises(ValidationError):
            self.env['hr.hospital.doctor.schedule'].create({
                'doctor_id': self.doctor.id,
                'day_of_week': '0',  # Monday
                'start_time': 18.0,   # 6 PM
                'end_time': 9.0,      # 9 AM (earlier than start)
                'schedule_type': 'work'
            })
    def test_disease_hierarchy(self):
        """Test disease hierarchical structure"""
        # Create parent disease
        parent_disease = self.env['hr.hospital.disease'].create({
            'name': 'Parent Disease',
            'icd10_code': 'A00',
            'danger_level': 'medium'
        })
        # Create child disease
        child_disease = self.env['hr.hospital.disease'].create({
            'name': 'Child Disease',
            'parent_id': parent_disease.id,
            'icd10_code': 'A00.1',
            'danger_level': 'high'
        })
        # Check hierarchy
        self.assertEqual(child_disease.parent_id, parent_disease)
        self.assertIn(child_disease, parent_disease.child_ids)
        self.assertEqual(child_disease.complete_name, 'Parent Disease / Child Disease')
    def test_patient_doctor_history(self):
        """Test patient doctor history functionality"""
        # Create new doctor
        new_doctor = self.env['hr.hospital.doctor'].create({
            'first_name': 'New',
            'last_name': 'Doctor',
            'speciality_id': self.specialty.id,
            'license_number': 'NEW123456',
            'license_date': '2021-01-01'
        })
        # Change patient's doctor
        self.patient.write({'personal_doctor_id': new_doctor.id})
        # Check history was created
        history = self.env['hr.hospital.patient.doctor.history'].search([
            ('patient_id', '=', self.patient.id),
            ('doctor_id', '=', new_doctor.id),
            ('active', '=', True)
        ])
        self.assertTrue(history)
        # Check old history was deactivated
        old_history = self.env['hr.hospital.patient.doctor.history'].search([
            ('patient_id', '=', self.patient.id),
            ('doctor_id', '=', self.doctor.id),
            ('active', '=', False)
        ])
        self.assertTrue(old_history)
    def test_diagnosis_approval(self):
        """Test diagnosis approval workflow"""
        # Create visit and diagnosis
        disease = self.env['hr.hospital.disease'].create({
            'name': 'Test Disease',
            'icd10_code': 'Z00.1',
            'danger_level': 'low'
        })
        visit = self.env['hr.hospital.visit'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'planned_datetime': '2024-01-01 10:00:00',
            'visit_type': 'first',
            'state': 'completed'
        })
        diagnosis = self.env['hr.hospital.diagnosis'].create({
            'visit_id': visit.id,
            'disease_id': disease.id,
            'description': 'Test diagnosis',
            'severity': 'mild'
        })
        # Test approval
        self.assertFalse(diagnosis.is_approved)
        diagnosis.action_approve_diagnosis()
        self.assertTrue(diagnosis.is_approved)
        self.assertEqual(diagnosis.approved_doctor_id, self.doctor.id)

    def test_doctor_toggle_active_with_active_visits(self):
        """Test that doctor cannot be archived with active visits"""
        # Create a planned visit
        self.env['hr.hospital.visit'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'planned_datetime': '2025-01-01 10:00:00',
            'visit_type': 'consultation',
            'state': 'planned'
        })
        # Try to archive the doctor - should raise UserError
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            self.doctor.toggle_active()
        # Doctor should still be active
        self.assertTrue(self.doctor.active)

    def test_doctor_toggle_active_without_active_visits(self):
        """Test that doctor can be archived when no active visits"""
        # Create a completed visit
        visit = self.env['hr.hospital.visit'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'planned_datetime': '2020-01-01 10:00:00',
            'visit_type': 'consultation',
            'state': 'completed'
        })
        # Archive the doctor
        self.doctor.toggle_active()
        self.assertFalse(self.doctor.active)
        # Reactivate
        self.doctor.toggle_active()
        self.assertTrue(self.doctor.active)

    def test_doctor_action_create_quick_visit_from_doctor(self):
        """Test action_create_quick_visit_from_doctor method"""
        result = self.doctor.action_create_quick_visit_from_doctor()
        # Check action structure
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'hr.hospital.visit')
        self.assertEqual(result['view_mode'], 'form')
        self.assertEqual(result['target'], 'new')
        # Check default values in context
        context = result['context']
        self.assertEqual(context['default_doctor_id'], self.doctor.id)
        self.assertEqual(context['default_visit_type'], 'consultation')
        self.assertEqual(context['default_state'], 'planned')

    def test_compute_upcoming_visits_count(self):
        """Test _compute_upcoming_visits_count method"""
        # Initially no upcoming visits
        self.doctor._compute_upcoming_visits_count()
        initial_count = self.doctor.upcoming_visits_count
        # Create an upcoming planned visit
        self.env['hr.hospital.visit'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'planned_datetime': '2025-12-31 10:00:00',
            'visit_type': 'consultation',
            'state': 'planned'
        })
        # Recompute
        self.doctor._compute_upcoming_visits_count()
        self.assertEqual(self.doctor.upcoming_visits_count, initial_count + 1)

    def test_visit_get_available_visit_dates(self):
        """Test get_available_visit_dates method"""
        # Create doctor schedule for Monday
        self.env['hr.hospital.doctor.schedule'].create({
            'doctor_id': self.doctor.id,
            'day_of_week': '0',  # Monday
            'start_time': 9.0,
            'end_time': 17.0,
            'schedule_type': 'work'
        })
        # Test method returns available dates
        available_dates = self.env['hr.hospital.visit'].get_available_visit_dates(
            self.doctor.id,
            days=14
        )
        # Should return list
        self.assertIsInstance(available_dates, list)