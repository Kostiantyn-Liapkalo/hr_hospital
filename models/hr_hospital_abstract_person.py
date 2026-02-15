# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re
from datetime import date


class AbstractPerson(models.AbstractModel):
    _name = 'abstract.person'
    _description = 'Abstract Person Model'
    _inherit = ['image.mixin']

    # Name fields
    last_name = fields.Char(
        string='Last Name',
        required=True,
        index=True,
        translate=False
    )
    first_name = fields.Char(
        string='First Name',
        required=True,
        index=True,
        translate=False
    )
    middle_name = fields.Char(
        string='Middle Name',
        translate=False
    )

    # Contact information
    phone = fields.Char(
        string='Phone',
        help="Format: +380XXXXXXXXX"
    )
    email = fields.Char(string='Email')

    # Personal information
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Gender', default='male')

    birth_date = fields.Date(string='Date of Birth')
    age = fields.Integer(
        string='Age',
        compute='_compute_age',
        store=True,
        readonly=True
    )

    # Computed fields
    full_name = fields.Char(
        string='Full Name',
        compute='_compute_full_name',
        store=True,
        readonly=True
    )

    # Additional fields
    country_id = fields.Many2one(
        'res.country',
        string='Country of Citizenship',
        ondelete='restrict'
    )

    lang_id = fields.Many2one(
        'res.lang',
        string='Language',
        help='Language of communication'
    )

    # Age computation
    @api.depends('birth_date')
    def _compute_age(self):
        for record in self:
            if record.birth_date:
                today = date.today()
                born = record.birth_date
                record.age = today.year - born.year - (
                        (today.month, today.day) < (born.month, born.day)
                )
            else:
                record.age = 0

    # Full name computation
    @api.depends('last_name', 'first_name', 'middle_name')
    def _compute_full_name(self):
        for record in self:
            parts = [record.last_name, record.first_name]
            if record.middle_name:
                parts.append(record.middle_name)
            record.full_name = ' '.join(filter(None, parts))

    # Phone validation
    @api.constrains('phone')
    def _check_phone(self):
        phone_regex = r'^\+?[1-9]\d{1,14}$'
        for record in self:
            if record.phone and not re.match(phone_regex, record.phone.replace(' ', '')):
                raise ValidationError(
                    'Invalid phone format. Please use the format: +380XXXXXXXXX'
                )

    # Email validation
    @api.constrains('email')
    def _check_email(self):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.email and not re.match(email_regex, record.email):
                raise ValidationError('Invalid email format.')

    # Birth date validation
    @api.constrains('birth_date')
    def _check_birth_date(self):
        for record in self:
            if record.birth_date and record.birth_date > date.today():
                raise ValidationError('Date of birth cannot be in the future.')