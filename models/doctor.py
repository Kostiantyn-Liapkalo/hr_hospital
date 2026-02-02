from odoo import models, fields

class HospitalDoctor(models.Model):
    _name = 'hr.hospital.doctor'
    _description = 'Doctor'

    name = fields.Char(string='Name', required=True)
    specialization = fields.Char(string='Specialization')