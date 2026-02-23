# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields
from odoo.exceptions import ValidationError


class HrHospitalDiseaseReportWizard(models.TransientModel):
    _name = 'hr.hospital.disease.report.wizard'
    _description = 'Disease Report Wizard'

    # Filter fields
    doctor_ids = fields.Many2many(
        'hr.hospital.doctor'
    )

    disease_ids = fields.Many2many(
        'hr.hospital.disease'
    )

    country_ids = fields.Many2many(
        'res.country'
    )

    start_date = fields.Date(
        required=True,
        default=lambda self: fields.Date.today() - timedelta(days=30)
    )

    end_date = fields.Date(
        required=True,
        default=fields.Date.today
    )

    report_type = fields.Selection([
        ('detailed', 'Detailed Report'),
        ('summary', 'Summary Report')
    ], default='detailed', required=True)

    group_by = fields.Selection([
        ('doctor', 'By Doctor'),
        ('disease', 'By Disease'),
        ('month', 'By Month'),
        ('country', 'By Country')
    ], default='disease')

    def _get_base_domain(self):
        """Get base domain for diagnoses"""
        return [
            ('diagnosis_date', '>=', self.start_date),
            ('diagnosis_date', '<=', self.end_date),
            ('is_approved', '=', True)
        ]

    def _apply_filters(self, domain):
        """Apply additional filters to domain"""
        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))

        if self.disease_ids:
            domain.append(('disease_id', 'in', self.disease_ids.ids))

        if self.country_ids:
            domain.append(('patient_id.country_id', 'in', self.country_ids.ids))

        return domain

    def _group_by_doctor(self, diagnoses):
        """Group diagnoses by doctor"""
        doctors = {}
        for diagnosis in diagnoses:
            doctor_name = diagnosis.doctor_id.full_name
            if doctor_name not in doctors:
                doctors[doctor_name] = {
                    'doctor': doctor_name,
                    'count': 0,
                    'diseases': {}
                }
            doctors[doctor_name]['count'] += 1

            disease_name = diagnosis.disease_id.name
            if disease_name not in doctors[doctor_name]['diseases']:
                doctors[doctor_name]['diseases'][disease_name] = 0
            doctors[doctor_name]['diseases'][disease_name] += 1

        return list(doctors.values())

    def _group_by_disease(self, diagnoses):
        """Group diagnoses by disease"""
        diseases = {}
        for diagnosis in diagnoses:
            disease_name = diagnosis.disease_id.name
            if disease_name not in diseases:
                diseases[disease_name] = {
                    'disease': disease_name,
                    'count': 0,
                    'doctors': {}
                }
            diseases[disease_name]['count'] += 1

            doctor_name = diagnosis.doctor_id.full_name
            if doctor_name not in diseases[disease_name]['doctors']:
                diseases[disease_name]['doctors'][doctor_name] = 0
            diseases[disease_name]['doctors'][doctor_name] += 1

        return list(diseases.values())

    def _group_by_month(self, diagnoses):
        """Group diagnoses by month"""
        months = {}
        for diagnosis in diagnoses:
            month_key = diagnosis.diagnosis_date.strftime('%Y-%m')
            if month_key not in months:
                months[month_key] = {
                    'month': month_key,
                    'count': 0,
                    'diseases': {}
                }
            months[month_key]['count'] += 1

            disease_name = diagnosis.disease_id.name
            if disease_name not in months[month_key]['diseases']:
                months[month_key]['diseases'][disease_name] = 0
            months[month_key]['diseases'][disease_name] += 1

        return list(months.values())

    def _get_grouped_data(self, diagnoses):
        """Get data grouped according to selected grouping"""
        if self.group_by == 'doctor':
            return self._group_by_doctor(diagnoses)
        if self.group_by == 'disease':
            return self._group_by_disease(diagnoses)
        if self.group_by == 'month':
            return self._group_by_month(diagnoses)
        return []

    # Report generation method
    def action_generate_report(self):
        self.ensure_one()

        # Date validation
        if self.start_date > self.end_date:
            raise ValidationError(_('Start date cannot be later than end date.'))

        # Domain formation
        domain = self._get_base_domain()
        domain = self._apply_filters(domain)

        # Data retrieval
        diagnoses = self.env['hr.hospital.diagnosis'].search(domain)

        # Result structure
        result = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_diagnoses': len(diagnoses),
            'data': self._get_grouped_data(diagnoses)
        }

        # Action return
        return {
            'name': 'Disease Report',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.hospital.disease.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'report_data': result
            }
        }

