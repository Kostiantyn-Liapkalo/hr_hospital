# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
class HrHospitalDisease(models.Model):
    """
    Disease model for hospital management.
    
    This model represents diseases in a hierarchical classification system
    with ICD-10 codes, danger levels, and distribution regions.
    Supports parent-child relationships for disease categorization.
    
    Attributes:
        name (Char): Disease name (translatable)
        complete_name (Char): Full hierarchical name (computed)
        parent_id (Many2one): Parent disease category
        parent_path (Char): Path for hierarchy computation
        child_ids (One2many): Child diseases
        icd10_code (Char): ICD-10 classification code
        danger_level (Selection): Risk level (low, medium, high, critical)
        is_infectious (Boolean): Whether disease is contagious
        symptoms (Text): General symptoms description
        region_ids (Many2many): Countries where disease is found
        diagnosis_ids (One2many): Related diagnoses
        disease_count (Integer): Number of diagnoses (computed)
        active (Boolean): Archive status
    """
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
    ], default='medium', required=True)
    is_infectious = fields.Boolean(
        default=False
    )
    symptoms = fields.Text(
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
        """
        Compute full hierarchical name of disease.
        
        Format: "Parent Name / Disease Name" or just "Disease Name" if no parent.
        """
        for disease in self:
            if disease.parent_id:
                disease.complete_name = f"{disease.parent_id.complete_name} / {disease.name}"
            else:
                disease.complete_name = disease.name
    # Diagnoses count computation
    @api.depends('diagnosis_ids')
    def _compute_disease_count(self):
        """
        Compute the number of diagnoses for this disease.
        """
        for disease in self:
            disease.disease_count = len(disease.diagnosis_ids)
    # Display name computation for Odoo 19.0
    @api.depends('complete_name')
    def _compute_display_name(self):
        """
        Compute display name for disease.
        
        Uses complete_name if available, otherwise falls back to name.
        """
        for disease in self:
            disease.display_name = disease.complete_name or disease.name
    # Recursion check
    @api.constrains('parent_id')
    def _check_parent_id(self):
        """
        Prevent recursive disease hierarchies.
        
        Raises:
            ValidationError: If recursive hierarchy is detected.
        """
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive disease hierarchies.'))
    # Prevent archiving diseases with active diagnoses
    def toggle_active(self):
        """
        Override toggle_active to prevent archiving diseases with diagnoses.
        
        Raises:
            ValidationError: If disease has linked diagnoses.
            
        Returns:
            Result of parent toggle_active method.
        """
        for disease in self:
            active_diagnoses = disease.diagnosis_ids.filtered(
                lambda d: not d.is_approved or d.is_approved  # Check all active diagnoses
            )
            if disease.active and active_diagnoses:  # When trying to archive
                raise ValidationError(
                    _('Cannot archive a disease that has existing diagnoses. ') +
                    _('Please archive or delete the diagnoses first.')
                )
        return super(HrHospitalDisease, self).toggle_active()
