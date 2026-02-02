from odoo import models, fields

class HospitalVisit(models.Model):
    _name = 'hr.hospital.visit'
    _description = 'Patient Visit'

    visit_date = fields.Datetime(string='Visit Date', default=fields.Datetime.now)
    doctor_id = fields.Many2one('hr.hospital.doctor', string='Doctor', required=True)
    patient_id = fields.Many2one('hr.hospital.patient', string='Patient', required=True)
    diagnosis_ids = fields.Many2many('hr.hospital.disease', string='Diagnoses')