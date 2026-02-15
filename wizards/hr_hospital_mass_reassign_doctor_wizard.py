# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrHospitalMassReassignDoctorWizard(models.TransientModel):
    _name = 'hr.hospital.mass.reassign.doctor.wizard'
    _description = 'Mass Reassign Doctor Wizard'

    # Wizard Fields
    old_doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Current Doctor',
        required=True
    )

    new_doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='New Doctor',
        required=True,
        domain="[('is_intern', '=', False), ('id', '!=', old_doctor_id)]"
    )

    patient_ids = fields.Many2many(
        'hr.hospital.patient',
        string='Patients',
        domain="[('personal_doctor_id', '=', old_doctor_id)]"
    )

    change_date = fields.Date(
        string='Change Date',
        required=True,
        default=fields.Date.today
    )

    reason = fields.Text(
        string='Reason for Change',
        required=True
    )

    # Action method
    def action_reassign_doctor(self):
        self.ensure_one()

        # Validation
        if not self.patient_ids:
            raise ValidationError('Please select at least one patient.')

        if self.old_doctor_id == self.new_doctor_id:
            raise ValidationError('The current and new doctor cannot be the same person.')

        # Mass update logic
        for patient in self.patient_ids:
            # Create history record
            # The history model logic already handles deactivation of old records via override
            self.env['hr.hospital.patient.doctor.history'].create({
                'patient_id': patient.id,
                'doctor_id': self.new_doctor_id.id,
                'assignment_date': self.change_date,
                'reason': self.reason,
                'active': True
            })

            # Update personal doctor on patient record
            patient.write({
                'personal_doctor_id': self.new_doctor_id.id
            })

        # Return success notification
        return {
            'type': 'ir.actions.act_window_close',
            'params': {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Successfully reassigned {len(self.patient_ids)} patients.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        }

    # Onchange to refresh patient domain
    @api.onchange('old_doctor_id')
    def _onchange_old_doctor_id(self):
        if self.old_doctor_id:
            return {
                'domain': {
                    'patient_ids': [('personal_doctor_id', '=', self.old_doctor_id.id)]
                }
            }