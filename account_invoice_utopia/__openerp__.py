{
    'name': 'Personalización de Facturas',
    'version': '1.0',
    'author': 'Chistian Torres',
    'category': 'Custom',
    'description': """
    Personalización de Facturas.
    """,
    'depends': ['base', 'account'],
    'data': [
        # security
        'security/ir.model.access.csv',
        # views
        'views/account_invoice_view.xml',
    ],
    'active': False,
    'installable': True
}
