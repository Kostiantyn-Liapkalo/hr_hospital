# from odoo import models, fields, api


# class hr_hospital(models.Model):
#     _name = 'hr_hospital.hr_hospital'
#     _description = 'hr_hospital.hr_hospital'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

