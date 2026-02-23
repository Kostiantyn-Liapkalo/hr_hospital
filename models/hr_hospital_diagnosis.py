# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo import _


class HrHospitalDiagnosis(models.Model):
    _name = 'hr.hospital.diagnosis'
    _description = 'Medical Diagnosis'
    _order = 'diagnosis_date desc'

    # Main fields
    name = fields.Char(
        string='Diagnosis Reference',
        default=lambda self: self.env['ir.sequence'].next_by_code('hr.hospital.diagnosis'),
        readonly=True
    )

    visit_id = fields.Many2one(
        'hr.hospital.visit',
        string='Visit',
        required=True,
        ondelete='cascade',
        domain="[('state', '=', 'completed'), ('planned_datetime', '>=', (context_today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d'))]"
    )

    disease_id = fields.Many2one(
        'hr.hospital.disease',
        string='Disease',
        required=True,
        domain="[('active', '=', True), ('danger_level', 'in', ['high', 'critical'])]"
    )

    description = fields.Text(
        string='Diagnosis Description',
        required=True
    )

    prescribed_treatment = fields.Html(
        string='Prescribed Treatment'
    )

    # Approval Status
    is_approved = fields.Boolean(
        string='Approved',
        default=False
    )

    approved_doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Approving Doctor',
        readonly=True
    )

    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True
    )

    # Medical details
    severity = fields.Selection([
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical')
    ], string='Severity Level', required=True)

    diagnosis_date = fields.Datetime(
        string='Examination Date',
        default=fields.Datetime.now,
        required=True
    )

    # Related fields
    doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Doctor',
        related='visit_id.doctor_id',
        store=True,
        readonly=True
    )

    patient_id = fields.Many2one(
        'hr.hospital.patient',
        string='Patient',
        related='visit_id.patient_id',
        store=True,
        readonly=True
    )

    # Methods
    def action_approve_diagnosis(self):
        for diagnosis in self:
            if not diagnosis.is_approved:
                # Check if doctor can approve (is not an intern)
                if self.env.user.doctor_id and self.env.user.doctor_id.is_intern:
                    raise UserError(_('An intern cannot approve diagnoses.'))

                diagnosis.write({
                    'is_approved': True,
                    'approved_doctor_id': self.env.user.doctor_id.id,
                    'approval_date': datetime.now()
                })

    def action_reject_diagnosis(self):
        for diagnosis in self:
            if diagnosis.is_approved:
                diagnosis.write({
                    'is_approved': False,
                    'approved_doctor_id': False,
                    'approval_date': False
                })

    # Constraints
    @api.constrains('diagnosis_date')
    def _check_diagnosis_date(self):
        for diagnosis in self:
            if diagnosis.diagnosis_date > fields.Datetime.now():
                raise ValidationError(_('The diagnosis date cannot be in the future.'))
            if diagnosis.diagnosis_date < diagnosis.visit_id.planned_datetime:
                raise ValidationError(_('The examination date cannot be earlier than the visit date.'))

    # Method for automatic approval by mentor
    def _auto_approve_by_mentor(self):
        for diagnosis in self:
            if not diagnosis.is_approved and diagnosis.doctor_id.is_intern:
                mentor = diagnosis.doctor_id.mentor_id
                if mentor:
                    diagnosis.write({
                        'is_approved': True,
                        'approved_doctor_id': mentor.id,
                        'approval_date': datetime.now()
                    })
