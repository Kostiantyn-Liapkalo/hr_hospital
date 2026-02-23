# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import models, fields
from odoo.exceptions import ValidationError


class HrHospitalRescheduleVisitWizard(models.TransientModel):
    _name = 'hr.hospital.reschedule.visit.wizard'
    _description = 'Reschedule Visit Wizard'

    # Fields
    visit_id = fields.Many2one(
        'hr.hospital.visit',
        required=True,
        readonly=True
    )

    new_doctor_id = fields.Many2one(
        'hr.hospital.doctor'
    )

    new_date = fields.Date(
        required=True,
        default=fields.Date.today
    )

    new_time = fields.Float(
        required=True,
        default=9.0  # 9:00 AM
    )

    reason = fields.Text(
        required=True
    )

    # Reschedule method
    def action_reschedule_visit(self):
        self.ensure_one()

        # Check visit state
        if self.visit_id.state not in ['planned', 'in_progress']:
            raise ValidationError(_('Only planned or in-progress visits can be rescheduled.'))

        # Construct new datetime
        new_datetime = datetime.combine(
            self.new_date,
            datetime.min.time()
        ) + timedelta(hours=self.new_time)

        # Determine doctor
        doctor_id = self.new_doctor_id.id if self.new_doctor_id else self.visit_id.doctor_id.id

        # Check for overlapping visits
        existing_visit = self.env['hr.hospital.visit'].search([
            ('doctor_id', '=', doctor_id),
            ('patient_id', '=', self.visit_id.patient_id.id),
            ('planned_datetime', '>=', self.new_date),
            ('planned_datetime', '<', self.new_date + timedelta(days=1)),
            ('id', '!=', self.visit_id.id),
            ('state', 'in', ['planned', 'in_progress'])
        ], limit=1)

        if existing_visit:
            raise ValidationError(
                _('The patient already has a scheduled visit with this doctor on this day.')
            )

        # Update visit
        update_vals = {
            'planned_datetime': new_datetime,
            'state': 'planned'
        }

        if self.new_doctor_id:
            update_vals['doctor_id'] = self.new_doctor_id.id

        self.visit_id.write(update_vals)

        # Return success notification
        return {
            'type': 'ir.actions.act_window_close',
            'params': {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Visit Rescheduled',
                    'message': f'Visit successfully rescheduled to {new_datetime.strftime("%Y-%m-%d %H:%M")}',
                    'type': 'success',
                    'sticky': False,
                }
            }
        }

