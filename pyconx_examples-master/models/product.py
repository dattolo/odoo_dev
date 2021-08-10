from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    dummy_field = fields.Char('Dummy Field')
