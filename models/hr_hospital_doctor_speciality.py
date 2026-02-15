# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrHospitalDoctorSpeciality(models.Model):
    _name = 'hr.hospital.doctor.speciality'
    _description = 'Doctor Specialty'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True
    )

    code = fields.Char(
        string='Specialty Code',
        size=10,
        required=True,
        index=True
    )

    description = fields.Text(string='Description')

    active = fields.Boolean(
        string='Active',
        default=True
    )

    doctor_ids = fields.One2many(
        'hr.hospital.doctor',
        'speciality_id',
        string='Doctors'
    )

    # Computed fields
    doctors_count = fields.Integer(
        string='Doctors Count',
        compute='_compute_doctors_count',
        store=True
    )

    # SQL constraints for code uniqueness
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'The specialty code must be unique!'),
    ]

    @api.depends('doctor_ids')
    def _compute_doctors_count(self):
        for speciality in self:
            speciality.doctors_count = len(speciality.doctor_ids)

    def name_get(self):
        result = []
        for speciality in self:
            name = f"{speciality.name} ({speciality.code})"
            result.append((speciality.id, name))
        return result