# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrHospitalContactPerson(models.Model):
    _name = 'hr.hospital.contact.person'
    _description = 'Contact Person'
    _inherit = ['abstract.person']

    # Relationship field
    relationship = fields.Selection([
        ('parent', 'Parent'),
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('sibling', 'Sibling'),
        ('relative', 'Relative'),
        ('friend', 'Friend'),
        ('other', 'Other')
    ], string='Relationship', required=True)

    patient_ids = fields.One2many(
        'hr.hospital.patient',
        'contact_person_id',
        string='Patients'
    )

    # Field for selecting patients when creating contact person
    patient_selection_ids = fields.Many2many(
        'hr.hospital.patient',
        string='Patients',
        domain="[('allergies', '!=', False)]"
    )

    emergency_contact = fields.Boolean(
        string='Emergency Contact',
        default=True
    )

    can_make_decisions = fields.Boolean(
        string='Can Make Medical Decisions',
        default=False,
        help='Authorized to make medical decisions on behalf of the patient'
    )

    # Computed fields
    related_patients_count = fields.Integer(
        string='Related Patients Count',
        compute='_compute_related_patients_count',
        store=True
    )

    @api.depends('patient_ids')
    def _compute_related_patients_count(self):
        for contact in self:
            contact.related_patients_count = len(contact.patient_ids)