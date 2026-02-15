# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class HrHospitalDiseaseReportWizard(models.TransientModel):
    _name = 'hr.hospital.disease.report.wizard'
    _description = 'Disease Report Wizard'

    # Filter fields
    doctor_ids = fields.Many2many(
        'hr.hospital.doctor',
        string='Doctors'
    )

    disease_ids = fields.Many2many(
        'hr.hospital.disease',
        string='Diseases'
    )

    country_ids = fields.Many2many(
        'res.country',
        string='Patient Countries'
    )

    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=lambda self: fields.Date.today() - timedelta(days=30)
    )

    end_date = fields.Date(
        string='End Date',
        required=True,
        default=fields.Date.today
    )

    report_type = fields.Selection([
        ('detailed', 'Detailed Report'),
        ('summary', 'Summary Report')
    ], string='Report Type', default='detailed', required=True)

    group_by = fields.Selection([
        ('doctor', 'By Doctor'),
        ('disease', 'By Disease'),
        ('month', 'By Month'),
        ('country', 'By Country')
    ], string='Group By', default='disease')

    # Report generation method
    def action_generate_report(self):
        self.ensure_one()

        # Date validation
        if self.start_date > self.end_date:
            raise ValidationError('Start date cannot be later than end date.')

        # Domain formation
        domain = [
            ('diagnosis_date', '>=', self.start_date),
            ('diagnosis_date', '<=', self.end_date),
            ('is_approved', '=', True)
        ]

        if self.doctor_ids:
            domain.append(('doctor_id', 'in', self.doctor_ids.ids))

        if self.disease_ids:
            domain.append(('disease_id', 'in', self.disease_ids.ids))

        if self.country_ids:
            domain.append(('patient_id.country_id', 'in', self.country_ids.ids))

        # Data retrieval
        diagnoses = self.env['hr.hospital.diagnosis'].search(domain)

        # Result structure
        result = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_diagnoses': len(diagnoses),
            'data': []
        }

        # Data grouping logic
        if self.group_by == 'doctor':
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

            for doctor, data in doctors.items():
                result['data'].append(data)

        elif self.group_by == 'disease':
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

            for disease, data in diseases.items():
                result['data'].append(data)

        elif self.group_by == 'month':
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

            for month, data in months.items():
                result['data'].append(data)

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