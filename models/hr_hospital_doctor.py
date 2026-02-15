# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime


class HrHospitalDoctor(models.Model):
    _name = 'hr.hospital.doctor'
    _description = 'Doctor'
    _inherit = ['abstract.person']
    _order = 'last_name, first_name'

    # System User
    user_id = fields.Many2one(
        'res.users',
        string='System User',
        help='User account for system login'
    )

    # Specialty
    speciality_id = fields.Many2one(
        'hr.hospital.doctor.speciality',
        string='Specialty',
        required=True,
        domain="[('active', '=', True)]"
    )

    # Intern Status
    is_intern = fields.Boolean(string='Is Intern', default=False)

    # Mentor (only for interns)
    mentor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Mentor Doctor',
        domain="[('is_intern', '=', False), ('id', '!=', id)]"
    )

    # License
    license_number = fields.Char(
        string='License Number',
        required=True,
        copy=False,
        index=True,
        readonly=False
    )

    license_date = fields.Date(
        string='License Issue Date',
        required=True
    )

    # Experience
    experience = fields.Integer(
        string='Experience (years)',
        compute='_compute_experience',
        store=True,
        readonly=True
    )

    # Rating
    rating = fields.Float(
        string='Rating',
        digits=(3, 2),
        default=0.0,
        help='Rating from 0.00 to 5.00'
    )

    # Doctor Schedule
    schedule_ids = fields.One2many(
        'hr.hospital.doctor.schedule',
        'doctor_id',
        string='Doctor Schedule'
    )

    # Country of Study
    study_country_id = fields.Many2one(
        'res.country',
        string='Country of Study'
    )

    # Relations with other models
    patient_ids = fields.One2many(
        'hr.hospital.patient',
        'personal_doctor_id',
        string='Patients'
    )

    visit_ids = fields.One2many(
        'hr.hospital.visit',
        'doctor_id',
        string='Visits'
    )

    diagnosis_ids = fields.One2many(
        'hr.hospital.diagnosis',
        'doctor_id',
        string='Diagnoses'
    )

    # Computed fields
    active_patients_count = fields.Integer(
        string='Active Patients Count',
        compute='_compute_active_patients_count',
        store=True
    )

    upcoming_visits_count = fields.Integer(
        string='Upcoming Visits Count',
        compute='_compute_upcoming_visits_count',
        store=True
    )

    # Performance Indexes & Constraints - Odoo 19.0 format
    sql_constraints = [
        ('license_number_unique',
         'UNIQUE(license_number)',
         'The license number must be unique!'),
        ('rating_range_check',
         'CHECK(rating >= 0.00 AND rating <= 5.00)',
         'The rating must be between 0.00 and 5.00'),
    ]

    # Experience computation
    @api.depends('license_date')
    def _compute_experience(self):
        for record in self:
            if record.license_date:
                today = date.today()
                license_date = record.license_date
                record.experience = today.year - license_date.year - (
                        (today.month, today.day) < (license_date.month, license_date.day)
                )
            else:
                record.experience = 0

    # Active patients computation
    @api.depends('patient_ids')
    def _compute_active_patients_count(self):
        for doctor in self:
            doctor.active_patients_count = len(doctor.patient_ids)

    # Upcoming visits computation
    @api.depends('visit_ids', 'visit_ids.planned_datetime', 'visit_ids.state')
    def _compute_upcoming_visits_count(self):
        for doctor in self:
            today = datetime.now()
            upcoming = doctor.visit_ids.filtered(
                lambda v: v.planned_datetime and v.planned_datetime > today
                          and v.state in ['planned', 'in_progress']
            )
            doctor.upcoming_visits_count = len(upcoming)

    # Display name computation for Odoo 19.0
    @api.depends('full_name', 'speciality_id')
    def _compute_display_name(self):
        for doctor in self:
            if doctor.speciality_id:
                doctor.display_name = f"{doctor.full_name} ({doctor.speciality_id.name})"
            else:
                doctor.display_name = doctor.full_name

    # Rating validation
    @api.constrains('rating')
    def _check_rating(self):
        for record in self:
            if record.rating < 0.0 or record.rating > 5.0:
                raise ValidationError('Rating must be between 0.00 and 5.00.')

    # Mentor validation
    @api.constrains('is_intern', 'mentor_id')
    def _check_mentor(self):
        for record in self:
            if record.is_intern and not record.mentor_id:
                raise ValidationError('An intern must have a mentor.')
            if record.mentor_id and record.mentor_id.is_intern:
                raise ValidationError('An intern cannot be a mentor.')
            if record.mentor_id and record.mentor_id.id == record.id:
                raise ValidationError('A doctor cannot be their own mentor.')

    # Intern onchange
    @api.onchange('is_intern')
    def _onchange_is_intern(self):
        if not self.is_intern:
            self.mentor_id = False
        else:
            # Automatically find a mentor with the same specialty
            domain = [
                ('is_intern', '=', False),
                ('speciality_id', '=', self.speciality_id.id),
                ('id', '!=', self.id._origin.id if isinstance(self.id, models.NewId) else self.id)
            ]
            mentor = self.env['hr.hospital.doctor'].search(domain, limit=1)
            if mentor:
                self.mentor_id = mentor

    # Archiving method
    def toggle_active(self):
        for doctor in self:
            active_visits = doctor.visit_ids.filtered(
                lambda v: v.state in ['planned', 'in_progress']
            )
            if doctor.active and active_visits:  # Check when trying to archive
                raise UserError(
                    'Cannot deactivate a doctor with active visits. '
                    'Please complete or cancel all planned visits first.'
                )
        return super(HrHospitalDoctor, self).toggle_active()