# -*- coding: utf-8 -*-

{
    'name': 'Paysera Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Paysera Implementation',
    'version': '0.1',
    'description': """Paysera Payment Acquirer""",
    'author': 'Naglis Jonaitis',
    'depends': ['payment','account'],
    'data': [
        'views/paysera.xml',
        'views/payment_acquirer.xml',
        'data/paysera.xml',
        'edi/invoice_action_data.xml'
    ],
    'installable': True,
}
