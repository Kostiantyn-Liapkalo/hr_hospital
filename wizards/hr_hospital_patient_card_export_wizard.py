# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json
import csv
from io import StringIO
import base64


class HrHospitalPatientCardExportWizard(models.TransientModel):
    _name = 'hr.hospital.patient.card.export.wizard'
    _description = 'Patient Medical Card Export Wizard'

    # Fields
    patient_id = fields.Many2one(
        'hr.hospital.patient',
        string='Patient',
        required=True
    )

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date', default=fields.Date.today)

    include_diagnoses = fields.Boolean(
        string='Include Diagnoses',
        default=True
    )

    include_recommendations = fields.Boolean(
        string='Include Recommendations',
        default=True
    )

    lang_id = fields.Many2one(
        'res.lang',
        string='Report Language',
        default=lambda self: self.patient_id.lang_id or self.env.user.lang
    )

    export_format = fields.Selection([
        ('json', 'JSON'),
        ('csv', 'CSV')
    ], string='Export Format', default='json', required=True)

    export_data = fields.Binary(string='Export File', readonly=True)
    file_name = fields.Char(string='File Name', compute='_compute_file_name')

    @api.depends('patient_id', 'export_format')
    def _compute_file_name(self):
        for wizard in self:
            if wizard.patient_id and wizard.export_format:
                clean_name = wizard.patient_id.full_name.replace(" ", "_")
                wizard.file_name = f'medical_card_{clean_name}.{wizard.export_format}'
            else:
                wizard.file_name = 'medical_card.unknown'

    # Export method
    def action_export_patient_card(self):
        self.ensure_one()

        # Date validation
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start date cannot be later than end date.')

        # Data gathering
        patient_data = {
            'patient': {
                'full_name': self.patient_id.full_name,
                'birth_date': str(self.patient_id.birth_date) if self.patient_id.birth_date else '',
                'age': self.patient_id.age,
                'gender': dict(self.patient_id._fields['gender'].selection).get(self.patient_id.gender),
                'blood_group': self.patient_id.blood_group,
                'allergies': self.patient_id.allergies,
                'chronic_diseases': self.patient_id.chronic_diseases,
                'personal_doctor': self.patient_id.personal_doctor_id.full_name if self.patient_id.personal_doctor_id else '',
                'insurance_company': self.patient_id.insurance_company_id.name if self.patient_id.insurance_company_id else '',
                'insurance_policy': self.patient_id.insurance_policy_number,
                'passport': self.patient_id.passport,
                'country': self.patient_id.country_id.name if self.patient_id.country_id else '',
                'language': self.patient_id.lang_id.name if self.patient_id.lang_id else ''
            }
        }

        # Diagnoses processing
        if self.include_diagnoses:
            domain = [('patient_id', '=', self.patient_id.id)]
            if self.start_date:
                domain.append(('diagnosis_date', '>=', self.start_date))
            if self.end_date:
                domain.append(('diagnosis_date', '<=', self.end_date))

            diagnoses = self.env['hr.hospital.diagnosis'].search(domain, order='diagnosis_date desc')

            patient_data['diagnoses'] = []
            for diagnosis in diagnoses:
                patient_data['diagnoses'].append({
                    'date': diagnosis.diagnosis_date.strftime('%Y-%m-%d %H:%M'),
                    'disease': diagnosis.disease_id.name,
                    'doctor': diagnosis.doctor_id.full_name,
                    'severity': dict(diagnosis._fields['severity'].selection).get(diagnosis.severity),
                    'description': diagnosis.description,
                    'prescribed_treatment': diagnosis.prescribed_treatment,
                    'approved': diagnosis.is_approved,
                    'approved_by': diagnosis.approved_doctor_id.full_name if diagnosis.approved_doctor_id else '',
                    'approval_date': diagnosis.approval_date.strftime(
                        '%Y-%m-%d %H:%M') if diagnosis.approval_date else ''
                })

        # Visits and Recommendations
        if self.include_recommendations:
            domain = [('patient_id', '=', self.patient_id.id)]
            if self.start_date:
                domain.append(('planned_datetime', '>=', self.start_date))
            if self.end_date:
                domain.append(('planned_datetime', '<=', self.end_date))

            visits = self.env['hr.hospital.visit'].search(domain, order='planned_datetime desc')

            patient_data['visits'] = []
            for visit in visits:
                patient_data['visits'].append({
                    'date': visit.planned_datetime.strftime('%Y-%m-%d %H:%M'),
                    'doctor': visit.doctor_id.full_name,
                    'type': dict(visit._fields['visit_type'].selection).get(visit.visit_type),
                    'status': dict(visit._fields['state'].selection).get(visit.state),
                    'cost': visit.cost,
                    'currency': visit.currency_id.name,
                    'recommendations': visit.recommendations
                })

        # Doctor Assignment History
        patient_data['doctor_history'] = []
        for history in self.patient_id.doctor_history_ids:
            patient_data['doctor_history'].append({
                'doctor': history.doctor_id.full_name,
                'assignment_date': history.assignment_date.strftime('%Y-%m-%d'),
                'change_date': history.change_date.strftime('%Y-%m-%d') if history.change_date else '',
                'duration_days': history.assignment_duration,
                'reason': history.reason,
                'active': history.active
            })

        # Export logic
        if self.export_format == 'json':
            export_content = json.dumps(patient_data, indent=2, ensure_ascii=False)
        else:  # CSV Format
            output = StringIO()
            writer = csv.writer(output)

            # Header: Patient Info
            writer.writerow(['Field', 'Value'])
            for key, value in patient_data['patient'].items():
                writer.writerow([key, value])

            # Section: Diagnoses
            if 'diagnoses' in patient_data and patient_data['diagnoses']:
                writer.writerow([])
                writer.writerow(['DIAGNOSES'])
                writer.writerow(['Date', 'Disease', 'Doctor', 'Severity', 'Description', 'Approved'])
                for diag in patient_data['diagnoses']:
                    writer.writerow([
                        diag['date'], diag['disease'], diag['doctor'], diag['severity'],
                        diag['description'][:100], 'Yes' if diag['approved'] else 'No'
                    ])

            # Section: Visits
            if 'visits' in patient_data and patient_data['visits']:
                writer.writerow([])
                writer.writerow(['VISITS'])
                writer.writerow(['Date', 'Doctor', 'Type', 'Status', 'Cost', 'Currency'])
                for visit in patient_data['visits']:
                    writer.writerow([
                        visit['date'], visit['doctor'], visit['type'],
                        visit['status'], visit['cost'], visit['currency']
                    ])

            export_content = output.getvalue()

        # File encoding and return
        self.write({
            'export_data': base64.b64encode(export_content.encode('utf-8'))
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model={self._name}&id={self.id}&filename={self.file_name}&field=export_data&download=true',
            'target': 'self',
        }