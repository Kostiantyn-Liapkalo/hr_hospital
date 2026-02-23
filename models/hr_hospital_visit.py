# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo import _


class HrHospitalVisit(models.Model):
    _name = 'hr.hospital.visit'
    _description = 'Patient Visit'
    _order = 'planned_datetime desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Додано для відстеження змін

    # Visit Status
    state = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show')
    ], string='Status', default='planned', required=True, tracking=True)

    # Planned Date/Time
    planned_datetime = fields.Datetime(
        string='Planned Date and Time',
        required=True,
        tracking=True
    )

    # Actual Date/Time
    actual_datetime = fields.Datetime(
        string='Actual Visit Date and Time',
        readonly=True,
        tracking=True
    )

    # Doctor and Patient
    doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Doctor',
        required=True,
        domain="[('license_number', '!=', False)]",
        tracking=True
    )

    patient_id = fields.Many2one(
        'hr.hospital.patient',
        string='Patient',
        required=True,
        tracking=True
    )

    # Visit Type
    visit_type = fields.Selection([
        ('first', 'Initial'),
        ('follow_up', 'Follow-up'),
        ('preventive', 'Preventive'),
        ('emergency', 'Emergency'),
        ('consultation', 'Consultation')
    ], required=True, tracking=True)

    # Diagnoses
    diagnosis_ids = fields.One2many(
        'hr.hospital.diagnosis',
        'visit_id'
    )

    # Recommendations and Cost
    recommendations = fields.Html()

    cost = fields.Monetary(
        currency_field='currency_id',
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    # Technical fields
    duration = fields.Float(
        compute='_compute_duration',
        store=True,
        digits=(4, 2)
    )

    diagnosis_count = fields.Integer(
        compute='_compute_diagnosis_count',
        store=True
    )

    # Patient info fields for search/group by
    patient_age = fields.Integer(
        related='patient_id.age',
        store=True
    )

    doctor_speciality_id = fields.Many2one(
        related='doctor_id.speciality_id',
        store=True
    )

    # SQL Constraints - Odoo 19.0 format
    sql_constraints = [
        ('check_planned_not_past',
         'CHECK(planned_datetime >= CURRENT_DATE)',
         'Planned visit date cannot be in the past!'),
    ]

    # Constraints
    @api.constrains('planned_datetime')
    def _check_planned_datetime(self):
        for visit in self:
            if visit.planned_datetime and visit.planned_datetime < datetime.now():
                raise ValidationError(
                    _('Planned visit date and time cannot be in the past. ') +
                    _('Please select a future date and time.')
                )

    @api.constrains('doctor_id', 'patient_id', 'planned_datetime')
    def _check_duplicate_visit(self):
        for visit in self:
            if visit.planned_datetime and visit.doctor_id and visit.patient_id:
                # Check for duplicate visits on the same day
                existing = self.search([
                    ('id', '!=', visit.id),
                    ('doctor_id', '=', visit.doctor_id.id),
                    ('patient_id', '=', visit.patient_id.id),
                    ('planned_datetime', '>=', visit.planned_datetime.replace(hour=0, minute=0, second=0)),
                    ('planned_datetime', '<=', visit.planned_datetime.replace(hour=23, minute=59, second=59)),
                    ('state', 'not in', ['cancelled'])
                ])
                if existing:
                    raise ValidationError(
                    _('A patient can only have one visit to the same doctor per day.')
                )

    @api.constrains('doctor_id', 'planned_datetime')
    def _check_doctor_schedule(self):
        for visit in self:
            if visit.doctor_id and visit.planned_datetime:
                # Check if doctor has schedule for this date and time
                weekday = str(visit.planned_datetime.weekday())
                schedule = self.env['hr.hospital.doctor.schedule'].search([
                    ('doctor_id', '=', visit.doctor_id.id),
                    '|',
                    ('date', '=', visit.planned_datetime.date()),
                    ('day_of_week', '=', weekday),
                    ('schedule_type', '=', 'work')
                ], limit=1)

                if not schedule:
                    raise ValidationError(
                        _('The selected doctor does not have a work schedule for this date and time.')
                )

                # Check if within working hours
                visit_hour = visit.planned_datetime.hour + visit.planned_datetime.minute / 60.0
                if schedule.start_time and schedule.end_time:
                    if visit_hour < schedule.start_time or visit_hour > schedule.end_time:
                        raise ValidationError(
                            f'The selected time is outside doctor\'s working hours '
                            f'({schedule.start_time:.2f} - {schedule.end_time:.2f}).'
                        )

    # Actions
    def action_start_visit(self):
        for visit in self:
            if visit.state == 'planned':
                visit.write({
                    'state': 'in_progress',
                    'actual_datetime': datetime.now()
                })
                visit.message_post(body=_('Visit started'), subtype_xmlid='mail.mt_note')
        return True

    def action_complete_visit(self):
        for visit in self:
            if visit.state == 'in_progress':
                visit.write({
                    'state': 'completed'
                })
                visit.message_post(body=_('Visit completed'), subtype_xmlid='mail.mt_note')
        return True

    def action_cancel_visit(self):
        for visit in self:
            if visit.state in ['planned', 'in_progress']:
                visit.write({
                    'state': 'cancelled'
                })
                visit.message_post(body=_('Visit cancelled'), subtype_xmlid='mail.mt_note')
        return True

    def action_mark_no_show(self):
        for visit in self:
            if visit.state == 'planned':
                visit.write({
                    'state': 'no_show'
                })
                visit.message_post(body=_('Patient did not show up'), subtype_xmlid='mail.mt_note')
        return True

    # Computation methods
    @api.depends('planned_datetime', 'actual_datetime')
    def _compute_duration(self):
        for visit in self:
            if visit.actual_datetime and visit.planned_datetime:
                duration = visit.actual_datetime - visit.planned_datetime
                visit.duration = abs(duration.total_seconds() / 3600)  # hours, absolute value
            else:
                visit.duration = 0.0

    @api.depends('diagnosis_ids')
    def _compute_diagnosis_count(self):
        for visit in self:
            visit.diagnosis_count = len(visit.diagnosis_ids)

    # Display name computation
    @api.depends('patient_id', 'doctor_id', 'planned_datetime')
    def _compute_display_name(self):
        for visit in self:
            if visit.patient_id and visit.doctor_id and visit.planned_datetime:
                visit.display_name = f"{visit.patient_id.full_name} - {visit.doctor_id.full_name} ({visit.planned_datetime.strftime('%Y-%m-%d %H:%M')})"
            else:
                visit.display_name = f"Visit #{visit.id}"

    # Override write to lock records
    def write(self, vals):
        for visit in self:
            if visit.state in ['completed', 'cancelled', 'no_show']:
                restricted_fields = ['doctor_id', 'patient_id', 'planned_datetime', 'visit_type']
                if any(field in vals for field in restricted_fields):
                    raise UserError(
                        _('Cannot modify core details of a visit that is already completed, cancelled, or marked as no-show.')
                    )
        return super(HrHospitalVisit, self).write(vals)

    # Override unlink
    def unlink(self):
        for visit in self:
            if visit.diagnosis_ids:
                raise UserError(
                    _('Cannot delete a visit that has linked diagnoses. ') +
                    _('Please delete the diagnoses first or cancel the visit.')
                )
        return super(HrHospitalVisit, self).unlink()

    # Override default_get to set default values
    @api.model
    def default_get(self, fields_list):
        res = super(HrHospitalVisit, self).default_get(fields_list)
        if 'planned_datetime' in fields_list and not res.get('planned_datetime'):
            # Set default to tomorrow at 9:00 AM
            tomorrow = datetime.now() + timedelta(days=1)
            res['planned_datetime'] = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        return res

    @api.model
    def get_available_visit_dates(self, doctor_id, start_date=None, end_date=None):
        """Get available visit dates excluding weekends and doctor's holidays"""
        if not start_date:
            start_date = datetime.now().date()
        if not end_date:
            end_date = start_date + timedelta(days=30)
            
        doctor = self.env['hr.hospital.doctor'].browse(doctor_id)
        if not doctor:
            return []
            
        available_dates = []
        current_date = start_date
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday to Friday
                # Check if doctor has schedule for this day
                weekday_str = str(current_date.weekday())
                schedule = self.env['hr.hospital.doctor.schedule'].search([
                    ('doctor_id', '=', doctor_id),
                    ('day_of_week', '=', weekday_str),
                    ('specific_date', '=', False)  # Regular weekly schedule
                ], limit=1)
                
                if schedule:
                    # Check if it's not a holiday
                    is_holiday = self.env['hr.hospital.holiday'].search([
                        ('doctor_id', '=', doctor_id),
                        ('date', '=', current_date)
                    ], limit=1)
                    
                    if not is_holiday:
                        available_dates.append({
                            'date': current_date,
                            'start_time': schedule.start_time,
                            'end_time': schedule.end_time
                        })
            
            current_date += timedelta(days=1)
            
        return available_dates
