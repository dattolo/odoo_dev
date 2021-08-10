from odoo import api, models, fields

class LibraryBook(models.Model):
    # structural attributes
    _name = 'library.book.copy'
    _description = 'Library Book\'s copy'
    _inherit = 'library.book'
