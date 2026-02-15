# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrHospitalDoctorSchedule(models.Model):
    _name = 'hr.hospital.doctor.schedule'
    _description = 'Doctor Schedule'
    _order = 'doctor_id, day_of_week, start_time'

    doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Doctor',
        required=True,
        ondelete='cascade',
        domain="[('speciality_id', '!=', False)]"
    )

    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='Day of Week', required=True)

    specific_date = fields.Date(
        string='Specific Date',
        help='Used for specific dates instead of a recurring weekly schedule'
    )

    start_time = fields.Float(
        string='Start Time',
        required=True,
        help='Time in hours (e.g., 8.5 for 08:30)'
    )

    end_time = fields.Float(
        string='End Time',
        required=True
    )

    schedule_type = fields.Selection([
        ('work', 'Work Day'),
        ('vacation', 'Vacation'),
        ('sick_leave', 'Sick Leave'),
        ('conference', 'Conference'),
        ('training', 'Training')
    ], string='Type', default='work', required=True)

    notes = fields.Char(string='Notes')

    # Computed fields
    duration = fields.Float(
        string='Duration (hours)',
        compute='_compute_duration',
        store=True
    )

    # SQL Constraints
    _sql_constraints = [
        ('time_check',
         'CHECK(end_time > start_time)',
         'End time must be later than start time!'),
    ]

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                record.duration = record.end_time - record.start_time
            else:
                record.duration = 0.0

    # Time validation
    @api.constrains('start_time', 'end_time')
    def _check_time_range(self):
        for record in self:
            if record.start_time >= record.end_time:
                raise ValidationError('End time must be later than start time.')
            if record.start_time < 0 or record.start_time > 24:
                raise ValidationError('Start time must be between 0 and 24 hours.')
            if record.end_time < 0 or record.end_time > 24:
                raise ValidationError('End time must be between 0 and 24 hours.')