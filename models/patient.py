from odoo import models, fields

class HospitalPatient(models.Model):
    _name = 'hr.hospital.patient'
    _description = 'Patient'

    name = fields.Char(string='Name', required=True)
    age = fields.Integer(string='Age')
    # Зв'язок з лікарем (лікаря, що спостерігає)
    doctor_id = fields.Many2one('hr.hospital.doctor', string='Attending Doctor')