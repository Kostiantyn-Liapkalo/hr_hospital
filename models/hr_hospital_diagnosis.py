# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo import _
class HrHospitalDiagnosis(models.Model):
    """
    Medical Diagnosis model for hospital management.
    
    This model represents medical diagnoses made during patient visits.
    It includes diagnosis information, disease reference, severity level,
    and approval workflow.
    
    Attributes:
        name (Char): Unique diagnosis reference (auto-generated)
        visit_id (Many2one): Related visit
        disease_id (Many2one): Diagnosed disease
        description (Text): Detailed diagnosis description
        prescribed_treatment (Html): Treatment recommendations
        is_approved (Boolean): Approval status
        approved_doctor_id (Many2one): Doctor who approved
        approval_date (Datetime): When approved
        severity (Selection): Severity level (mild, moderate, severe, critical)
        diagnosis_date (Datetime): When examination occurred
        doctor_id (Many2one): Diagnosing doctor (from visit)
        patient_id (Many2one): Patient (from visit)
    """
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
        """
        Approve the diagnosis.
        
        Only non-intern doctors can approve diagnoses.
        Sets is_approved to True and records approving doctor and date.
        
        Raises:
            UserError: If an intern tries to approve.
        """
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
        """
        Reject/revoke diagnosis approval.
        
        Clears approval status, approving doctor, and approval date.
        """
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
        """
        Validate diagnosis date.
        
        Must be:
            - Not in the future
            - Not earlier than the visit date
            
        Raises:
            ValidationError: If date constraints are violated.
        """
        for diagnosis in self:
            if diagnosis.diagnosis_date > fields.Datetime.now():
                raise ValidationError(_('The diagnosis date cannot be in the future.'))
            if diagnosis.diagnosis_date < diagnosis.visit_id.planned_datetime:
                raise ValidationError(_('The examination date cannot be earlier than the visit date.'))
    # Method for automatic approval by mentor
    def _auto_approve_by_mentor(self):
        """
        Automatically approve diagnosis by the intern's mentor.
        
        Called automatically for diagnoses made by interns.
        Assigns approval to the mentor doctor.
        """
        for diagnosis in self:
            if not diagnosis.is_approved and diagnosis.doctor_id.is_intern:
                mentor = diagnosis.doctor_id.mentor_id
                if mentor:
                    diagnosis.write({
                        'is_approved': True,
                        'approved_doctor_id': mentor.id,
                        'approval_date': datetime.now()
                    })
