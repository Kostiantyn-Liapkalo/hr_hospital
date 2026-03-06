# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date
class HrHospitalPatient(models.Model):
    """
    Patient model for hospital management.
    
    This model represents patients in the hospital system, storing their
    medical information, personal doctor assignment, visit history, and
    insurance details.
    
    Attributes:
        personal_doctor_id (Many2one): Assigned personal doctor
        passport (Char): Passport number (10 digits)
        contact_person_id (Many2one): Emergency contact person
        blood_group (Selection): Blood type (A+, A-, B+, B-, AB+, AB-, O+, O-)
        allergies (Text): Known allergies
        chronic_diseases (Text): Chronic conditions
        insurance_company_id (Many2one): Insurance provider
        insurance_policy_number (Char): Policy number
        visit_ids (One2many): Patient's visit history
        diagnosis_ids (One2many): Patient's diagnoses
        last_visit_date (Datetime): Date of last completed visit
        total_visits (Integer): Total number of visits
    """
    _name = 'hr.hospital.patient'
    _description = 'Patient'
    _inherit = ['hr.hospital.abstract.person']
    _order = 'last_name, first_name'
    # Personal Doctor
    personal_doctor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Personal Doctor',
        index=True,
        domain="[('license_number', '!=', False)]"
    )
    # Passport data
    passport = fields.Char(
        string='Passport Details',
        size=10,
        help='10-digit passport number'
    )
    # Contact Person
    contact_person_id = fields.Many2one(
        'hr.hospital.contact.person',
        string='Contact Person'
    )
    # Blood Group
    blood_group = fields.Selection([
        ('O+', 'O(I) Rh+'),
        ('O-', 'O(I) Rh-'),
        ('A+', 'A(II) Rh+'),
        ('A-', 'A(II) Rh-'),
        ('B+', 'B(III) Rh+'),
        ('B-', 'B(III) Rh-'),
        ('AB+', 'AB(IV) Rh+'),
        ('AB-', 'AB(IV) Rh-'),
    ], string='Blood Group')
    # Medical Information
    allergies = fields.Text(string='Allergies')
    chronic_diseases = fields.Text(string='Chronic Diseases')
    # Insurance Information
    insurance_company_id = fields.Many2one(
        'res.partner',
        string='Insurance Company',
        domain=[('is_company', '=', True)]
    )
    insurance_policy_number = fields.Char(
        string='Insurance Policy Number'
    )
    # Doctor History
    doctor_history_ids = fields.One2many(
        'hr.hospital.patient.doctor.history',
        'patient_id',
        string='Personal Doctor History'
    )
    # Relations
    visit_ids = fields.One2many(
        'hr.hospital.visit',
        'patient_id',
        string='Visits'
    )
    diagnosis_ids = fields.One2many(
        'hr.hospital.diagnosis',
        'patient_id',
        string='Diagnoses'
    )
    # Computed Fields
    last_visit_date = fields.Datetime(
        string='Last Visit Date',
        compute='_compute_last_visit',
        store=True
    )
    total_visits = fields.Integer(
        string='Total Visits',
        compute='_compute_total_visits',
        store=True
    )
    # SQL Constraints - Odoo 19.0 format
    sql_constraints = [
        ('passport_unique',
         'UNIQUE(passport)',
         'Passport details must be unique!'),
    ]
    # Constraints: Prevent multiple patients assigned to same doctor (if needed)
    # Commented out because one doctor can have many patients
    # @api.constrains('personal_doctor_id')
    # def _check_doctor_assignment(self):
    #     for patient in self:
    #         if patient.personal_doctor_id:
    #             # Check if already assigned to this doctor
    #             existing = self.search([
    #                 ('id', '!=', patient.id),
    #                 ('personal_doctor_id', '=', patient.personal_doctor_id.id)
    #             ])
    #             if existing:
    #                 raise ValidationError(
    #                     'Patient is already assigned to this doctor. '
    #                     'Please choose a different doctor.'
    #                 )
    # Last visit computation
    @api.depends('visit_ids', 'visit_ids.planned_datetime', 'visit_ids.state')
    def _compute_last_visit(self):
        """
        Compute the date of the last completed visit.
        
        Returns:
            Datetime: Date of the most recent completed visit or False.
        """
        for patient in self:
            visits = patient.visit_ids.filtered(
                lambda v: v.state == 'completed'
            ).sorted(key='planned_datetime', reverse=True)
            patient.last_visit_date = visits[0].planned_datetime if visits else False
    # Total visits computation
    @api.depends('visit_ids')
    def _compute_total_visits(self):
        """
        Compute the total number of visits for this patient.
        """
        for patient in self:
            patient.total_visits = len(patient.visit_ids)
    # Display name computation for Odoo 19.0
    @api.depends('full_name', 'passport')
    def _compute_display_name(self):
        """
        Compute display name including full name and passport number.
        
        Format: "Full Name (Passport)" or just "Full Name" if no passport.
        """
        for patient in self:
            if patient.passport:
                patient.display_name = f"{patient.full_name} ({patient.passport})"
            else:
                patient.display_name = patient.full_name
    # Passport validation
    @api.constrains('passport')
    def _check_passport(self):
        """
        Validate passport number format.
        
        Must contain exactly 10 digits.
        
        Raises:
            ValidationError: If passport format is invalid.
        """
        for record in self:
            if record.passport:
                # Remove any non-digit characters
                cleaned = ''.join(filter(str.isdigit, record.passport))
                if len(cleaned) != 10:
                    raise ValidationError('The passport must contain exactly 10 digits.')
                # Store cleaned version
                record.passport = cleaned
    # Age validation
    @api.constrains('birth_date')
    def _check_age(self):
        """
        Validate patient age is reasonable.
        
        Age must be greater than 0 and not more than 120 years.
        
        Raises:
            ValidationError: If age is outside valid range.
        """
        for record in self:
            if record.birth_date:
                today = date.today()
                birth_date = record.birth_date
                age = today.year - birth_date.year - (
                        (today.month, today.day) < (birth_date.month, birth_date.day)
                )
                if age <= 0:
                    raise ValidationError('Patient age must be greater than 0.')
                if age > 120:
                    raise ValidationError('Please verify the birth date - patient age seems unrealistic.')
    # Country onchange
    @api.onchange('country_id')
    def _onchange_country_id(self):
        """
        Suggest language based on country of citizenship.
        
        When country is selected, automatically suggest appropriate
        communication language for the patient.
        """
        if self.country_id:
            # Find language by country code
            lang = self.env['res.lang'].search([
                ('code', 'ilike', self.country_id.code)
            ], limit=1)
            if lang:
                self.lang_id = lang.id
                return {
                    'warning': {
                        'title': 'Language Suggestion',
                        'message': f'Communication language set to {lang.name} based on citizenship.'
                    }
                }
    # Allergies warning onchange
    @api.onchange('allergies')
    def _onchange_allergies(self):
        """
        Display warning when allergies are entered.
        
        Alerts medical staff to be cautious when prescribing medication.
        """
        if self.allergies:
            return {
                'warning': {
                    'title': 'Allergy Alert!',
                    'message': 'This patient has allergies. Please be cautious when prescribing medication.'
                }
            }
    # Personal doctor onchange - show warning about allergies
    @api.onchange('personal_doctor_id')
    def _onchange_personal_doctor(self):
        """
        Warn new doctor about patient allergies.
        
        When assigning a new personal doctor, display allergy information
        to ensure the doctor is aware of patient's conditions.
        """
        if self.personal_doctor_id and self.allergies:
            return {
                'warning': {
                    'title': 'Patient Allergies',
                    'message': f'This patient has allergies: {self.allergies}'
                }
            }
    # Override write to create history
    def write(self, vals):
        """
        Override write to track personal doctor changes.
        
        When personal_doctor_id is changed, creates a history record
        and deactivates the previous active history entry.
        
        Args:
            vals (dict): Values to write
            
        Returns:
            bool: Result of parent write method.
        """
        if 'personal_doctor_id' in vals:
            # Create a history record for each patient in self
            for patient in self:
                old_doctor_id = patient.personal_doctor_id.id if patient.personal_doctor_id else False
                new_doctor_id = vals.get('personal_doctor_id')
                # Convert string to int if needed
                if isinstance(new_doctor_id, str) and new_doctor_id.isdigit():
                    new_doctor_id = int(new_doctor_id)
                if old_doctor_id != new_doctor_id and new_doctor_id:
                    # Deactivate previous active records
                    active_history = self.env['hr.hospital.patient.doctor.history'].search([
                        ('patient_id', '=', patient.id),
                        ('active', '=', True)
                    ])
                    if active_history:
                        active_history.write({
                            'active': False,
                            'change_date': date.today(),
                            'change_reason': 'Automatically deactivated due to doctor change'
                        })
                    # Create new history record
                    self.env['hr.hospital.patient.doctor.history'].create({
                        'patient_id': patient.id,
                        'doctor_id': new_doctor_id,
                        'assignment_date': date.today(),
                        'active': True
                    })
        return super(HrHospitalPatient, self).write(vals)
    # Override unlink to prevent deletion with active visits
    def unlink(self):
        """
        Override unlink to prevent deleting patients with active visits.
        
        Raises:
            UserError: If patient has planned or in-progress visits.
            
        Returns:
            Result of parent unlink method.
        """
        for patient in self:
            active_visits = patient.visit_ids.filtered(
                lambda v: v.state in ['planned', 'in_progress']
            )
            if active_visits:
                raise UserError(
                    'Cannot delete a patient with active visits. '
                    'Please complete or cancel all visits first.'
                )
        return super(HrHospitalPatient, self).unlink()
    @api.model
    def get_patients_by_language_and_country(self, lang_code=None, country_code=None):
        """
        Get patients filtered by language and/or country.
        
        Args:
            lang_code (str): Language code to filter by (e.g., 'uk_UA')
            country_code (str): ISO country code to filter by (e.g., 'UA')
            
        Returns:
            Recordset: Patients matching the filter criteria.
        """
        domain = [('active', '=', True)]
        if lang_code:
            domain.append(('lang_id.code', '=', lang_code))
        if country_code:
            domain.append(('country_id.code', '=', country_code))
        return self.search(domain)
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Search for patients with dynamic domain.
        
        Supports context parameters:
            - lang_code: Filter by language
            - country_code: Filter by country
        
        Args:
            name (str): Search name pattern
            args (list): Additional search domain
            operator (str): Search operator (default: 'ilike')
            limit (int): Maximum number of results
            
        Returns:
            list: List of tuples (id, name) for matching patients.
        """
        if args is None:
            args = []
        domain = args + [('active', '=', True)]
        if name:
            domain.append(('full_name', operator, name))
        # Filter by language if specified in context
        if self.env.context.get('lang_code'):
            domain.append(('lang_id.code', '=', self.env.context['lang_code']))
        # Filter by country if specified in context
        if self.env.context.get('country_code'):
            domain.append(('country_id.code', '=', self.env.context['country_code']))
        patients = self.search(domain, limit=limit)
        return patients.name_get()
    def action_create_quick_visit(self):
        """
        Create a quick visit to patient's personal doctor.
        
        Automatically assigns:
            - Patient's personal doctor as the doctor
            - Visit type: 'first' if no visits, else 'follow_up'
            - Tomorrow at 9 AM as planned datetime
            - State: 'planned'
        
        Raises:
            UserError: If patient has no personal doctor assigned.
            
        Returns:
            dict: Action to open the created visit form.
        """
        self.ensure_one()
        if not self.personal_doctor_id:
            raise UserError(_('Please assign a personal doctor first.'))
        # Create visit with default values
        visit = self.env['hr.hospital.visit'].create({
            'patient_id': self.id,
            'doctor_id': self.personal_doctor_id.id,
            'visit_type': 'first' if not self.visit_ids else 'follow_up',
            'planned_datetime': fields.Datetime.now() + timedelta(days=1, hours=9),
            'state': 'planned',
        })
        # Return action to open the created visit
        return {
            'name': _('Visit'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.hospital.visit',
            'res_id': visit.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }