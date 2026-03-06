# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from odoo import _
class HrHospitalDoctor(models.Model):
    """
    Doctor model for hospital management.
    
    This model represents doctors in the hospital system, including their
    specialties, licenses, intern/mentor relationships, and associated
    patients and visits.
    
    Attributes:
        speciality_id (Many2one): Doctor's medical specialty
        is_intern (Boolean): Whether doctor is an intern
        mentor_id (Many2one): Mentor doctor (for interns only)
        intern_ids (One2many): List of interns (for mentors)
        license_number (Char): Medical license number
        license_date (Date): License issue date
        experience (Float): Years of experience (computed)
        rating (Float): Doctor rating (0-5 scale)
        patient_ids (One2many): Assigned patients
        visit_ids (One2many): Doctor's visits
        diagnosis_ids (One2many): Doctor's diagnoses
    """
    _name = 'hr.hospital.doctor'
    _description = 'Doctor'
    _inherit = ['hr.hospital.abstract.person']
    _order = 'last_name, first_name'
    # System User
    user_id = fields.Many2one(
        'res.users',
        string='System User',
        help='User account for system login'
    )
    # Specialty
    speciality_id = fields.Many2one(
        'hr.hospital.doctor.speciality',
        string='Specialty',
        required=True,
        domain="[('active', '=', True)]"
    )
    # Intern Status
    is_intern = fields.Boolean(string='Is Intern', default=False)
    # Mentor (only for interns)
    mentor_id = fields.Many2one(
        'hr.hospital.doctor',
        string='Mentor Doctor',
        domain="[('is_intern', '=', False), ('id', '!=', id)]"
    )
    # Interns (for mentor doctors)
    intern_ids = fields.One2many(
        'hr.hospital.doctor',
        'mentor_id',
        string='Interns',
        readonly=True
    )
    # License
    license_number = fields.Char(
        string='License Number',
        required=True,
        copy=False,
        index=True,
        readonly=False
    )
    license_date = fields.Date(
        string='License Issue Date',
        required=True
    )
    # Experience
    experience = fields.Integer(
        string='Experience (years)',
        compute='_compute_experience',
        store=True,
        readonly=True
    )
    # Rating
    rating = fields.Float(
        string='Rating',
        digits=(3, 2),
        default=0.0,
        help='Rating from 0.00 to 5.00'
    )
    # Doctor Schedule
    schedule_ids = fields.One2many(
        'hr.hospital.doctor.schedule',
        'doctor_id',
        string='Doctor Schedule'
    )
    # Country of Study
    study_country_id = fields.Many2one(
        'res.country',
        string='Country of Study'
    )
    # Relations with other models
    patient_ids = fields.One2many(
        'hr.hospital.patient',
        'personal_doctor_id',
        string='Patients'
    )
    visit_ids = fields.One2many(
        'hr.hospital.visit',
        'doctor_id',
        string='Visits'
    )
    diagnosis_ids = fields.One2many(
        'hr.hospital.diagnosis',
        'doctor_id',
        string='Diagnoses'
    )
    # Computed fields
    active_patients_count = fields.Integer(
        string='Active Patients Count',
        compute='_compute_active_patients_count',
        store=True
    )
    upcoming_visits_count = fields.Integer(
        string='Upcoming Visits Count',
        compute='_compute_upcoming_visits_count',
        store=True
    )
    # Performance Indexes & Constraints - Odoo 19.0 format
    sql_constraints = [
        ('license_number_unique',
         'UNIQUE(license_number)',
         'The license number must be unique!'),
        ('rating_range_check',
         'CHECK(rating >= 0.00 AND rating <= 5.00)',
         'The rating must be between 0.00 and 5.00'),
    ]
    # Experience computation
    @api.depends('license_date')
    def _compute_experience(self):
        """
        Compute doctor's years of experience based on license issue date.
        
        Calculates the difference between current date and license issue date
        in complete years.
        """
        for record in self:
            if record.license_date:
                today = date.today()
                license_date = record.license_date
                record.experience = today.year - license_date.year - (
                        (today.month, today.day) < (license_date.month, license_date.day)
                )
            else:
                record.experience = 0
    # Active patients computation
    @api.depends('patient_ids')
    def _compute_active_patients_count(self):
        """
        Compute the number of active patients assigned to this doctor.
        """
        for doctor in self:
            doctor.active_patients_count = len(doctor.patient_ids)
    # Upcoming visits computation
    @api.depends('visit_ids', 'visit_ids.planned_datetime', 'visit_ids.state')
    def _compute_upcoming_visits_count(self):
        """
        Compute the number of upcoming (planned or in progress) visits.
        
        Counts visits with planned_datetime in the future and state
        either 'planned' or 'in_progress'.
        """
        for doctor in self:
            today = datetime.now()
            upcoming = doctor.visit_ids.filtered(
                lambda v: v.planned_datetime and v.planned_datetime > today
                          and v.state in ['planned', 'in_progress']
            )
            doctor.upcoming_visits_count = len(upcoming)
    # Display name computation for Odoo 19.0
    @api.depends('full_name', 'speciality_id')
    def _compute_display_name(self):
        """
        Compute display name including full name and specialty.
        
        Format: "Full Name (Specialty)" or just "Full Name" if no specialty.
        """
        for doctor in self:
            if doctor.speciality_id:
                doctor.display_name = f"{doctor.full_name} ({doctor.speciality_id.name})"
            else:
                doctor.display_name = doctor.full_name
    def name_get(self):
        """
        Return list of tuples (id, name) for each record.
        
        Format: "Full Name (Specialty)" or just "Full Name".
        
        Returns:
            list: List of tuples (id, display_name)
        """
        result = []
        for doctor in self:
            if doctor.speciality_id:
                name = f"{doctor.full_name} ({doctor.speciality_id.name})"
            else:
                name = doctor.full_name
            result.append((doctor.id, name))
        return result
    # Rating validation
    @api.constrains('rating')
    def _check_rating(self):
        """
        Validate that rating is within acceptable range (0-5).
        
        Raises:
            ValidationError: If rating is less than 0 or greater than 5.
        """
        for record in self:
            if record.rating < 0.0 or record.rating > 5.0:
                raise ValidationError('Rating must be between 0.00 and 5.00.')
    # Mentor validation
    @api.constrains('is_intern', 'mentor_id')
    def _check_mentor(self):
        """
        Validate mentor relationships for interns.
        
        Checks:
            - Intern must have a mentor
            - Intern cannot be a mentor
            - Doctor cannot be their own mentor
            
        Raises:
            ValidationError: If any mentor constraint is violated.
        """
        for record in self:
            if record.is_intern and not record.mentor_id:
                raise ValidationError('An intern must have a mentor.')
            if record.mentor_id and record.mentor_id.is_intern:
                raise ValidationError('An intern cannot be a mentor.')
            if record.mentor_id and record.mentor_id.id == record.id:
                raise ValidationError('A doctor cannot be their own mentor.')
    # Intern onchange
    @api.onchange('is_intern')
    def _onchange_is_intern(self):
        """
        Handle changes to intern status.
        
        When intern status is removed, clear mentor.
        When intern status is added, auto-assign mentor with same specialty.
        """
        if not self.is_intern:
            self.mentor_id = False
        else:
            # Automatically find a mentor with the same specialty
            domain = [
                ('is_intern', '=', False),
                ('speciality_id', '=', self.speciality_id.id),
                ('id', '!=', self.id._origin.id if isinstance(self.id, models.NewId) else self.id)
            ]
            mentor = self.env['hr.hospital.doctor'].search(domain, limit=1)
            if mentor:
                self.mentor_id = mentor
    # Archiving method
    def toggle_active(self):
        """
        Override toggle_active to prevent archiving doctors with active visits.
        
        Checks for planned or in-progress visits before allowing archive.
        
        Raises:
            UserError: If doctor has active visits and cannot be deactivated.
            
        Returns:
            Result of parent toggle_active method.
        """
        for doctor in self:
            active_visits = doctor.visit_ids.filtered(
                lambda v: v.state in ['planned', 'in_progress']
            )
            if doctor.active and active_visits:  # Check when trying to archive
                raise UserError(_('Cannot deactivate a doctor with active visits. ') +
                    _('Please complete or cancel all planned visits first.'))
        return super(HrHospitalDoctor, self).toggle_active()
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Search for doctors with dynamic domain based on specialty and schedule.
        
        Supports context parameters:
            - specialty_id: Filter by specific specialty
            - check_availability: Filter by today's schedule availability
        
        Args:
            name (str): Search name pattern
            args (list): Additional search domain
            operator (str): Search operator (default: 'ilike')
            limit (int): Maximum number of results
            
        Returns:
            list: List of tuples (id, name) for matching doctors
        """
        if args is None:
            args = []
        # Get doctors with valid license and specialty
        domain = args + [
            ('license_number', '!=', False),
            ('speciality_id', '!=', False),
            ('active', '=', True)
        ]
        if name:
            domain.append(('full_name', operator, name))
        # Filter by specialty if specified in context
        if self.env.context.get('specialty_id'):
            domain.append(('speciality_id', '=', self.env.context['specialty_id']))
        # Filter by working schedule if checking availability
        if self.env.context.get('check_availability'):
            today = datetime.now().date()
            weekday = today.weekday()
            # Find doctors with schedule for today
            doctors_with_schedule = self.env['hr.hospital.doctor.schedule'].search([
                ('day_of_week', '=', str(weekday)),
                ('specific_date', '=', False),  # Regular weekly schedule
                ('doctor_id', 'in', self.search(domain).ids)
            ]).mapped('doctor_id')
            if doctors_with_schedule:
                domain.append(('id', 'in', doctors_with_schedule.ids))
        doctors = self.search(domain, limit=limit)
        return doctors.name_get()
    @api.model
    def get_doctors_by_study_country(self, country_code):
        """
        Get all active doctors who studied in a specific country.
        
        Args:
            country_code (str): ISO country code (e.g., 'UA', 'US')
            
        Returns:
            Recordset: Doctors matching the study country criteria
        """
        return self.search([
            ('study_country_id.code', '=', country_code),
            ('active', '=', True)
        ])
    def action_create_quick_visit_from_doctor(self):
        """
        Open form to create a quick visit for this doctor from kanban view.
        
        Pre-populates the visit form with:
            - This doctor as the default doctor
            - Tomorrow at 9 AM as default datetime
            - Visit type as 'consultation'
            - State as 'planned'
            
        Returns:
            dict: Action dictionary to open visit form
        """
        self.ensure_one()
        # Open wizard or form to select patient and create visit
        return {
            'name': _('Create Visit'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.hospital.visit',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_doctor_id': self.id,
                'default_planned_datetime': fields.Datetime.now() + timedelta(days=1, hours=9),
                'default_visit_type': 'consultation',
                'default_state': 'planned',
            }
        }
