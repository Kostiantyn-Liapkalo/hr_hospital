# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class HrHospitalDoctorScheduleWizard(models.TransientModel):
    _name = 'hr.hospital.doctor.schedule.wizard'
    _description = 'Doctor Schedule Generation Wizard'

    # Fields
    doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Doctor',
        required=True
    )

    start_week = fields.Date(
        string='Start Week',
        required=True,
        default=fields.Date.today
    )

    weeks_count = fields.Integer(
        string='Number of Weeks',
        default=1,
        required=True
    )

    schedule_type = fields.Selection([
        ('standard', 'Standard Week'),
        ('even', 'Even Weeks'),
        ('odd', 'Odd Weeks')
    ], string='Schedule Type', default='standard')

    # Days of the week
    monday = fields.Boolean(string='Monday', default=True)
    tuesday = fields.Boolean(string='Tuesday', default=True)
    wednesday = fields.Boolean(string='Wednesday', default=True)
    thursday = fields.Boolean(string='Thursday', default=True)
    friday = fields.Boolean(string='Friday', default=True)
    saturday = fields.Boolean(string='Saturday', default=False)
    sunday = fields.Boolean(string='Sunday', default=False)

    # Working hours
    start_time = fields.Float(
        string='Start Time',
        required=True,
        default=9.0
    )

    end_time = fields.Float(
        string='End Time',
        required=True,
        default=17.0
    )

    break_start = fields.Float(
        string='Break Start',
        default=13.0
    )

    break_end = fields.Float(
        string='Break End',
        default=14.0
    )

    # Schedule generation method
    def action_generate_schedule(self):
        self.ensure_one()

        # Time validation
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be later than start time.')

        if self.break_start >= self.break_end:
            raise ValidationError('Break end must be later than break start.')

        # Mapping days
        days_map = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6
        }

        selected_days = []
        for day_name, day_num in days_map.items():
            if getattr(self, day_name):
                selected_days.append(day_num)

        if not selected_days:
            raise ValidationError('Please select at least one day of the week.')

        # Generating schedule
        schedule_data = []
        current_date = self.start_week

        for week in range(self.weeks_count):
            # Check week type
            if self.schedule_type == 'even' and week % 2 != 0:
                current_date += timedelta(days=7)
                continue
            if self.schedule_type == 'odd' and week % 2 == 0:
                current_date += timedelta(days=7)
                continue

            for day_offset in range(7):
                current_day = current_date + timedelta(days=day_offset)
                weekday = current_day.weekday()

                if weekday in selected_days:
                    # Morning shift (before break)
                    if self.start_time < self.break_start:
                        schedule_data.append((0, 0, {
                            'doctor_id': self.doctor_id.id,
                            'day_of_week': str(weekday),
                            'specific_date': current_day,
                            'start_time': self.start_time,
                            'end_time': self.break_start,
                            'schedule_type': 'work',
                            'notes': 'Morning Shift'
                        }))

                    # Afternoon shift (after break)
                    if self.break_end < self.end_time:
                        schedule_data.append((0, 0, {
                            'doctor_id': self.doctor_id.id,
                            'day_of_week': str(weekday),
                            'specific_date': current_day,
                            'start_time': self.break_end,
                            'end_time': self.end_time,
                            'schedule_type': 'work',
                            'notes': 'Afternoon Shift'
                        }))

            current_date += timedelta(days=7)

        # Cleanup old work schedule for these dates
        if schedule_data:
            self.env['hr.hospital.doctor.schedule'].search([
                ('doctor_id', '=', self.doctor_id.id),
                ('schedule_type', '=', 'work'),
                ('specific_date', '>=', self.start_week),
                ('specific_date', '<', self.start_week + timedelta(days=7 * self.weeks_count))
            ]).unlink()

            # Write new schedule records
            self.doctor_id.write({
                'schedule_ids': schedule_data
            })

        return {
            'type': 'ir.actions.act_window_close',
            'params': {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Schedule Generated',
                    'message': f'Schedule has been generated for {self.doctor_id.full_name}',
                    'type': 'success',
                    'sticky': False,
                }
            }
        }