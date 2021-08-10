from odoo import models, fields

from odoo import api, models, fields
from odoo.exceptions import ValidationError

from datetime import timedelta

## Reporting errors to the user

from odoo.exceptions import UserError
from odoo.tools.translate import _

# LOGGING
import logging
_logger = logging.getLogger(__name__)


class LibraryBook(models.Model):
    
    #_inherit = ['base.archive']

    # structural attributes
    _name = 'library.book'
    _description = 'Library Book'
    _order = 'date_release desc, name'
    _rec_name = 'short_name'

    name = fields.Char('Title', required=True)
    date_release = fields.Date('Release Date')
    author_ids = fields.Many2many(
        'res.partner',
        string='Authors'
    )

    category_id = fields.Many2one('library.book.category')

    short_name = fields.Char('Short Title', translate=True,
                             index=True, required=True)

    notes = fields.Text('Internal Notes')

    cost_price = fields.Float('Book Cost', digits='Book Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary(
        'Retail Price',
        # optional: currency_field='currency_id',
    )

    publisher_id = fields.Many2one(
        'res.partner', string='Publisher',
        # optional:
        ondelete='set null',
        context={},
        domain=[],
    )
    # related field city of the publisher, so it will can retrived from the client side
    publisher_city = fields.Char(
        'Publisher City',
        related='publisher_id.city',
        readonly=True
    )

    state = fields.Selection(
        [('draft', 'Not Available'),
         ('available', 'Available'),
         ('borrowed', 'Borrowed'),
         ('lost', 'Lost')],
        'State', default='draft')
    description = fields.Html('Description', sanitize=True, strip_style=False)
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated')
    pages = fields.Integer('Number of Pages',
                           groups='base.group_user',
                           states={'lost': [('readonly', True)]},
                           help='Total book page count', company_dependent=False)
    reader_rating = fields.Float(
        'Reader Average Rating',
        digits=(14, 4),  # Optional precision decimals,
    )

        
    age_days = fields.Float(
        string='Days Since Release',
        compute='_compute_age',
        inverse='_inverse_age',
        search='_search_age',
        store=False,  # optional
        compute_sudo=True  # optional
    )

    # database constraint
    _sql_constraints = [
        ('name_uniq',  # label for constraint
         'UNIQUE (name)',  # sql statement
         'Book title must be unique.'),  # message for user
        ('positive_page', 'CHECK(pages>0)',
         'No of pages must be positive')
    ]

    #
    @api.constrains('date_release')
    def _check_release_date(self):

        for record in self:
            if record.date_release and record.date_release > fields.Date.today():
                raise models.ValidationError(
                    'Release date must be in the past')

    @api.depends('date_release')
    def _compute_age(self):
        today = fields.Date.today()
        for book in self:
            if book.date_release:
                delta = today - book.date_release
                book.age_days = delta.days
            else:
                book.age_days = 0

    def _inverse_age(self):
        today = fields.Date.today()
        for book in self.filtered('date_release'):
            d = today - timedelta(days=book.age_days)
            book.date_release = d

    def _search_age(self, operator, value):
        today = fields.Date.today()
        value_days = timedelta(days=value)
        value_date = today - value_days
        # convert the operator:
        # book with age > value have a date < value_date
        operator_map = {
            '>': '<', '>=': '<=',
            '<': '>', '<=': '>=',
        }
        new_op = operator_map.get(operator, operator)
        return [('date_release', new_op, value_date)]

    @api.model
    def _referencable_models(self):

        models = self.env['ir.model'].search(
            [('field_id.name', '=', 'message_ids')])

        return [(x.model, x.name) for x in models]

    ref_doc_id = fields.Reference(
        selection='_referencable_models',
        string='Reference Document')

    def name_get(self):

        result = []

        for record in self:
            rec_name = "%s (%s)" % (record.name, record.date_release)
            result.append((record.id, rec_name))

        return result

    # Chapter 5
    @api.model
    def is_allowed_transition(self, old_state, new_state):

        _logger.info("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@  new_state selected:  " + str(new_state));

        allowed = [('draft', 'available'),
                   ('available', 'borrowed'),
                   ('borrowed', 'available'),
                   ('available', 'lost'),
                   ('borrowed', 'lost'),
                   ('lost', 'available')]

        return (old_state, new_state) in allowed

    def change_state(self, new_state):

        for book in self:
            if book.is_allowed_transition(book.state,
                                          new_state):
                book.state = new_state
            
            else:
                
                msg = _('Moving from % s to % s is not allowed') % (
                    book.state, new_state)
                
                raise UserError(msg)

    def make_available(self):

        self.change_state('available')

    def make_borrowed(self):

        self.change_state('borrowed')

    def make_lost(self):

        self.change_state('lost')


class LibraryMember(models.Model):
    _name = 'library.member'
    #_inherits = {'res.partner': 'partner_id'}
    partner_id = fields.Many2one(
        'res.partner',
        ondelete='cascade',
        delegate=True,
    )

    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()
    date_of_birth = fields.Date('Date of birth')


class BaseArchive(models.AbstractModel):

    _name = 'base.archive'
    active = fields.Boolean(default=True)

    def do_archive(self):
        for record in self:
            record.active = not record.active



class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'

    authored_book_ids = fields.Many2many(
        'library.book', string='Authored Books')

    count_books = fields.Integer('Number of Authored Books',
                                 compute='_compute_count_books')

    @api.depends('authored_book_ids')
    def _compute_count_books(self):
        for r in self:
            r.count_books = len(r.authored_book_ids)
