# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date


class HrHospitalPatient(models.Model):
    _name = 'hr.hospital.patient'
    _description = 'Patient'
    _inherit = ['abstract.person']
    _order = 'last_name, first_name'

    # Personal Doctor
    personal_doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Personal Doctor',
        index=True,
        domain="[('license_number', '!=', False)]"
    )

    # Passport data
    passport = fields.Char(
        string='Passport Details',
        size=10,
        help='10-digit passport number'
    )

    # Contact Person
    contact_person_id = fields.Many2one(
        'hr.hospital.contact.person',
        string='Contact Person'
    )

    # Blood Group
    blood_group = fields.Selection([
        ('O+', 'O(I) Rh+'),
        ('O-', 'O(I) Rh-'),
        ('A+', 'A(II) Rh+'),
        ('A-', 'A(II) Rh-'),
        ('B+', 'B(III) Rh+'),
        ('B-', 'B(III) Rh-'),
        ('AB+', 'AB(IV) Rh+'),
        ('AB-', 'AB(IV) Rh-'),
    ], string='Blood Group')

    # Medical Information
    allergies = fields.Text(string='Allergies')
    chronic_diseases = fields.Text(string='Chronic Diseases')

    # Insurance Information
    insurance_company_id = fields.Many2one(
        'res.partner',
        string='Insurance Company',
        domain=[('is_company', '=', True)]
    )

    insurance_policy_number = fields.Char(
        string='Insurance Policy Number'
    )

    # Doctor History
    doctor_history_ids = fields.One2many(
        'hr.hospital.patient.doctor.history',
        'patient_id',
        string='Personal Doctor History'
    )

    # Relations
    visit_ids = fields.One2many(
        'hr.hospital.visit',
        'patient_id',
        string='Visits'
    )

    diagnosis_ids = fields.One2many(
        'hr.hospital.diagnosis',
        'patient_id',
        string='Diagnoses'
    )

    # Computed Fields
    last_visit_date = fields.Datetime(
        string='Last Visit Date',
        compute='_compute_last_visit',
        store=True
    )

    total_visits = fields.Integer(
        string='Total Visits',
        compute='_compute_total_visits',
        store=True
    )

    # SQL Constraints - Odoo 19.0 format
    sql_constraints = [
        ('passport_unique',
         'UNIQUE(passport)',
         'Passport details must be unique!'),
    ]

    # Constraints: Prevent multiple patients assigned to same doctor (if needed)
    # Commented out because one doctor can have many patients
    # @api.constrains('personal_doctor_id')
    # def _check_doctor_assignment(self):
    #     for patient in self:
    #         if patient.personal_doctor_id:
    #             # Check if already assigned to this doctor
    #             existing = self.search([
    #                 ('id', '!=', patient.id),
    #                 ('personal_doctor_id', '=', patient.personal_doctor_id.id)
    #             ])
    #             if existing:
    #                 raise ValidationError(
    #                     'Patient is already assigned to this doctor. '
    #                     'Please choose a different doctor.'
    #                 )

    # Last visit computation
    @api.depends('visit_ids', 'visit_ids.planned_datetime', 'visit_ids.state')
    def _compute_last_visit(self):
        for patient in self:
            visits = patient.visit_ids.filtered(
                lambda v: v.state == 'completed'
            ).sorted(key='planned_datetime', reverse=True)
            patient.last_visit_date = visits[0].planned_datetime if visits else False

    # Total visits computation
    @api.depends('visit_ids')
    def _compute_total_visits(self):
        for patient in self:
            patient.total_visits = len(patient.visit_ids)

    # Display name computation for Odoo 19.0
    @api.depends('full_name', 'passport')
    def _compute_display_name(self):
        for patient in self:
            if patient.passport:
                patient.display_name = f"{patient.full_name} ({patient.passport})"
            else:
                patient.display_name = patient.full_name

    # Passport validation
    @api.constrains('passport')
    def _check_passport(self):
        for record in self:
            if record.passport:
                # Remove any non-digit characters
                cleaned = ''.join(filter(str.isdigit, record.passport))
                if len(cleaned) != 10:
                    raise ValidationError('The passport must contain exactly 10 digits.')
                # Store cleaned version
                record.passport = cleaned

    # Age validation
    @api.constrains('birth_date')
    def _check_age(self):
        for record in self:
            if record.birth_date:
                today = date.today()
                birth_date = record.birth_date
                age = today.year - birth_date.year - (
                        (today.month, today.day) < (birth_date.month, birth_date.day)
                )
                if age <= 0:
                    raise ValidationError('Patient age must be greater than 0.')
                if age > 120:
                    raise ValidationError('Please verify the birth date - patient age seems unrealistic.')

    # Country onchange
    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            # Find language by country code
            lang = self.env['res.lang'].search([
                ('code', 'ilike', self.country_id.code)
            ], limit=1)
            if lang:
                self.lang_id = lang.id
                return {
                    'warning': {
                        'title': 'Language Suggestion',
                        'message': f'Communication language set to {lang.name} based on citizenship.'
                    }
                }

    # Allergies warning onchange
    @api.onchange('allergies')
    def _onchange_allergies(self):
        if self.allergies:
            return {
                'warning': {
                    'title': 'Allergy Alert!',
                    'message': 'This patient has allergies. Please be cautious when prescribing medication.'
                }
            }

    # Personal doctor onchange - show warning about allergies
    @api.onchange('personal_doctor_id')
    def _onchange_personal_doctor(self):
        if self.personal_doctor_id and self.allergies:
            return {
                'warning': {
                    'title': 'Patient Allergies',
                    'message': f'This patient has allergies: {self.allergies}'
                }
            }

    # Override write to create history
    def write(self, vals):
        if 'personal_doctor_id' in vals:
            # Create a history record for each patient in self
            for patient in self:
                old_doctor_id = patient.personal_doctor_id.id if patient.personal_doctor_id else False
                new_doctor_id = vals.get('personal_doctor_id')

                # Convert string to int if needed
                if isinstance(new_doctor_id, str) and new_doctor_id.isdigit():
                    new_doctor_id = int(new_doctor_id)

                if old_doctor_id != new_doctor_id and new_doctor_id:
                    # Deactivate previous active records
                    active_history = self.env['hr.hospital.patient.doctor.history'].search([
                        ('patient_id', '=', patient.id),
                        ('active', '=', True)
                    ])
                    if active_history:
                        active_history.write({
                            'active': False,
                            'change_date': date.today(),
                            'change_reason': 'Automatically deactivated due to doctor change'
                        })

                    # Create new history record
                    self.env['hr.hospital.patient.doctor.history'].create({
                        'patient_id': patient.id,
                        'doctor_id': new_doctor_id,
                        'assignment_date': date.today(),
                        'active': True
                    })

        return super(HrHospitalPatient, self).write(vals)

    # Override unlink to prevent deletion with active visits
    def unlink(self):
        for patient in self:
            active_visits = patient.visit_ids.filtered(
                lambda v: v.state in ['planned', 'in_progress']
            )
            if active_visits:
                raise UserError(
                    'Cannot delete a patient with active visits. '
                    'Please complete or cancel all visits first.'
                )
        return super(HrHospitalPatient, self).unlink()

    @api.model
    def get_patients_by_language_and_country(self, lang_code=None, country_code=None):
        """Get patients by language and country of citizenship"""
        domain = [('active', '=', True)]
        
        if lang_code:
            domain.append(('lang_id.code', '=', lang_code))
            
        if country_code:
            domain.append(('country_id.code', '=', country_code))
            
        return self.search(domain)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Dynamic domain for patients based on language and country"""
        if args is None:
            args = []
            
        domain = args + [('active', '=', True)]
        
        if name:
            domain.append(('full_name', operator, name))
            
        # Filter by language if specified in context
        if self.env.context.get('lang_code'):
            domain.append(('lang_id.code', '=', self.env.context['lang_code']))
            
        # Filter by country if specified in context
        if self.env.context.get('country_code'):
            domain.append(('country_id.code', '=', self.env.context['country_code']))
            
        patients = self.search(domain, limit=limit)
        return patients.name_get()