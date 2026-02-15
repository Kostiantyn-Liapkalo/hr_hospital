# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class HrHospitalPatientDoctorHistory(models.Model):
    _name = 'hr.hospital.patient.doctor.history'
    _description = 'Patient Personal Doctor History'
    _order = 'assignment_date desc'

    # Main fields
    patient_id = fields.Many2one(
        'hr.hospital.patient',
        string='Patient',
        required=True,
        ondelete='cascade'
    )

    doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Doctor',
        required=True,
        ondelete='restrict'
    )

    assignment_date = fields.Date(
        string='Assignment Date',
        required=True,
        default=fields.Date.today
    )

    change_date = fields.Date(
        string='Change Date'
    )

    reason = fields.Text(
        string='Change Reason'
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    # Computed fields
    assignment_duration = fields.Integer(
        string='Assignment Duration (days)',
        compute='_compute_assignment_duration',
        store=True
    )

    @api.depends('assignment_date', 'change_date')
    def _compute_assignment_duration(self):
        for record in self:
            if record.assignment_date:
                end_date = record.change_date or date.today()
                duration = (end_date - record.assignment_date).days
                record.assignment_duration = max(0, duration)

    # Override create
    @api.model
    def create(self, vals):
        # Deactivate previous active records for this patient
        if vals.get('patient_id') and vals.get('active', True):
            previous_active = self.search([
                ('patient_id', '=', vals['patient_id']),
                ('active', '=', True)
            ])
            previous_active.write({
                'active': False,
                'change_date': date.today()
            })

        return super(HrHospitalPatientDoctorHistory, self).create(vals)