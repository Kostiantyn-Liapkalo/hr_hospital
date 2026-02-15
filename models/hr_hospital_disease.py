# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrHospitalDisease(models.Model):
    _name = 'hr.hospital.disease'
    _description = 'Disease'
    _order = 'complete_name'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'

    # Main fields
    name = fields.Char(
        string='Disease Name',
        required=True,
        translate=True
    )
    complete_name = fields.Char(
        string='Full Name',
        compute='_compute_complete_name',
        store=True,
        recursive=True  # IMPORTANT: Required for hierarchical fields in Odoo 19.0
    )
    parent_id = fields.Many2one(
        'hr.hospital.disease',
        string='Parent Disease',
        index=True,
        ondelete='cascade'
    )
    parent_path = fields.Char(
        string='Parent Path',
        index=True,
        unaccent=False
    )
    child_ids = fields.One2many(
        'hr.hospital.disease',
        'parent_id',
        string='Child Diseases'
    )

    # Medical classification
    icd10_code = fields.Char(
        string='ICD-10 Code',
        size=10,
        help='International Statistical Classification of Diseases and Related Health Problems (10th revision)'
    )

    danger_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Danger Level', default='medium', required=True)

    is_infectious = fields.Boolean(
        string='Is Infectious',
        default=False
    )

    symptoms = fields.Text(
        string='Symptoms',
        help='General symptoms of the disease'
    )

    # Spread regions
    region_ids = fields.Many2many(
        'res.country',
        'disease_country_rel',
        'disease_id',
        'country_id',
        string='Distribution Regions'
    )

    # Relations
    diagnosis_ids = fields.One2many(
        'hr.hospital.diagnosis',
        'disease_id',
        string='Diagnoses'
    )

    # Computed fields
    disease_count = fields.Integer(
        string='Diagnoses Count',
        compute='_compute_disease_count',
        store=True
    )

    # Active field for archiving
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck to archive this disease"
    )

    # SQL Constraints - Changed to Odoo 19.0 format
    sql_constraints = [
        ('icd10_code_unique',
         'UNIQUE(icd10_code)',
         'The ICD-10 code must be unique!'),
    ]

    # Full name computation
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for disease in self:
            if disease.parent_id:
                disease.complete_name = f"{disease.parent_id.complete_name} / {disease.name}"
            else:
                disease.complete_name = disease.name

    # Diagnoses count computation
    @api.depends('diagnosis_ids')
    def _compute_disease_count(self):
        for disease in self:
            disease.disease_count = len(disease.diagnosis_ids)

    # Display name computation for Odoo 19.0
    @api.depends('complete_name')
    def _compute_display_name(self):
        for disease in self:
            disease.display_name = disease.complete_name or disease.name

    # Recursion check
    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError('You cannot create recursive disease hierarchies.')

    # Prevent archiving diseases with active diagnoses
    def toggle_active(self):
        for disease in self:
            active_diagnoses = disease.diagnosis_ids.filtered(
                lambda d: not d.is_approved or d.is_approved  # Check all active diagnoses
            )
            if disease.active and active_diagnoses:  # When trying to archive
                raise ValidationError(
                    'Cannot archive a disease that has existing diagnoses. '
                    'Please archive or delete the diagnoses first.'
                )
        return super(HrHospitalDisease, self).toggle_active()