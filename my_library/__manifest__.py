{
    'name': "My library",
    'summary': "Manage books easily",
    'description': """
    Manage Library
    Description related to library.
    """,
    'application': True,
    'author': "Francesco Dattolo",
    'website': "https://francescodattolo.it",
    #'category': 'Uncategorized',
    'category': 'drricambi',
    'version': '14.0.1',
    'depends': ['base'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/library_book.xml',
        'views/library_book_copy.xml',
        'views/library_book_categ.xml',
        'views/res_partner.xml',
    ],
    'demo': ['demo.xml'],
}
