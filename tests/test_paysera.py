# -*- coding: utf-8 -*-

from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.addons.payment.tests.common import PaymentAcquirerCommon
from openerp.tools import mute_logger

from lxml import objectify


class PayseraCommon(PaymentAcquirerCommon):

    def setUp(self):
        super(PayseraCommon, self).setUp()

        cr, uid = self.cr, self.uid
        _, self.paysera_id = self.registry('ir.model.data').\
            get_object_reference(cr, uid, 'payment_paysera',
                                 'payment_acquirer_paysera')

        self.project_id = '53203'
        self.sign_password = '7323e13b502b18674c59bb2015818e78'
        self.post_data = {
            'data': u'bGFuZz0mcmVmZXJlbmNlPVNPMDEyJnBfY2l0eT1TaW4rQ2l0eSZwcm' +
                    '9qZWN0aWQ9NTMyMDMmY3VycmVuY3lfaWQ9MSZjdXJyZW5jeT1FVVImc' +
                    'F9lbWFpbD1ub3JiZXJ0LmJ1eWVyJTQwZXhhbXBsZS5jb20mcF9zdHJl' +
                    'ZXQ9SHVnZStTdHJlZXQrMiUyRjU0MyZwYXJ0bmVyPXJlcy5wYXJ0bmV' +
                    'yJTI4MyUyQyUyOSZwX2NvdW50cnljb2RlPUJFJm9yZGVyaWQ9U08wMT' +
                    'ImY291bnRyeT1CRSZwX2ZpcnN0bmFtZT1CdXllciZwX3ppcD0xMDAwJ' +
                    'mFtb3VudD0zMjAwMCZ2ZXJzaW9uPTEuNiZwX2xhc3RuYW1lPU5vcmJl' +
                    'cnQmdGVzdD0xJnJldHVybl91cmw9JTJGc2hvcCUyRnBheW1lbnQlMkZ' +
                    '2YWxpZGF0ZSZwYXltZW50PWRpcmVjdGViYmUmcGF5dGV4dD1VJUM1JU' +
                    'JFc2FreW1hcytuciUzQStTTzAxMitodHRwJTNBJTJGJTJGbG9jYWxob' +
                    '3N0K3Byb2pla3RlLislMjhQYXJkYXYlQzQlOTdqYXMlM0ErTmFnbGlz' +
                    'K0pvbmFpdGlzJTI5JnN0YXR1cz0xJnJlcXVlc3RpZD02MzA1NzE5NCZ' +
                    'wYXlhbW91bnQ9MzIwMDAmcGF5Y3VycmVuY3k9RVVSJm5hbWU9VUFCJn' +
                    'N1cmVuYW1lPU1vayVDNCU5N2ppbWFpLmx0',
            'ss1': u'e899774b6649616cc841113512111120',
            'ss2': u'uRdNt8ugz2JhxiEeS8BNUBrujDwsfMwgY7iugUcFbqQVg-M2VfICrGt' +
                   '3kVyEP9IDx4ywxa-ww85UPFlUlutZnslodkb7cmdNidw9CBJxKdp0NK7' +
                   'ESlRWiSAnVqT8LdgZP42IU2M3OyIs1nM9TMG3GevU04FbCBTCg_NM2EG' +
                   'Uolc=',
        }
        self.tx_values = {
            'reference': 'SO012',
            'currency': self.currency_euro,
            'amount': 320.00,
        }
        self.payment_acquirer.write(
            cr, uid, self.paysera_id, {
                'paysera_project_id': '53203',
                'paysera_sign_password': '7323e13b502b18674c59bb2015818e78',
            }
        )

    def test_form_render(self):
        cr, uid, context = self.cr, self.uid, {}
        # be sure not to do stupid things
        paysera = self.payment_acquirer.browse(self.cr, self.uid,
                                               self.paysera_id, None)
        self.assertEqual(paysera.environment, 'test',
                         'test without test environment')

        res = self.payment_acquirer.render(cr, uid, self.paysera_id,
                                           'SO012', 320.00,
                                           self.currency_euro_id,
                                           partner_id=None,
                                           partner_values=self.buyer_values,
                                           context=context)
        # Check form result.
        tree = objectify.fromstring(res)
        self.assertEqual(tree.get('action'), 'https://www.paysera.com/pay/',
                         'Wrong form POST url')

    def test_form_signature(self):
        cr, uid, ctx = self.cr, self.uid, {}
        paysera = self.payment_acquirer.browse(cr, uid, self.paysera_id, ctx)
        self.assertEqual(paysera.environment, 'test', 'Not a test environment')
        test_data = {
            u'ačiū': u'prašom',
        }
        signature = self.payment_acquirer._paysera_generate_data_signature(
            paysera, test_data)
        self.assertEquals(signature, '4c76c0117e278178889e0c16977c0505',
                          'Wrong signature')

    @mute_logger('openerp.addons.payment_paysera.models.paysera',
                 'ValidationError')
    def test_tx_management(self):
        cr, uid, ctx = self.cr, self.uid, {}
        # be sure not to do stupid things
        paysera = self.payment_acquirer.browse(cr, uid, self.paysera_id, ctx)
        self.assertEqual(paysera.environment, 'test', 'Not a test environment')

        """
        FORM_VALUES = {
            'lang': '',
            'reference': u'SO012',
            'p_city': 'Sin City',
            'projectid': '53203',
            'currency_id': 1,
            'currency': u'EUR',
            'p_email': 'norbert.buyer@example.com',
            'p_street': 'Huge Street 2/543',
            'cancelurl': 'http://localhost:8069/payment/paysera/cancel',
            'partner': res.partner(3,),
            'p_countrycode': u'BE',
            'callbackurl': 'http://localhost:8069/payment/paysera/callback',
            'orderid': 'SO012',
            'country': 'BE',
            'p_firstname': 'Buyer',
            'p_zip': '1000',
            'amount': '32000',
            'version': '1.6',
            'p_lastname': 'Norbert',
            'test': '1',
            'accepturl': 'http://localhost:8069/payment/paysera/accept',
            'return_url': '/shop/payment/validate'
        }
        """

        # Should raise an error about non-existent order ID.
        with self.assertRaises(ValidationError):
            self.payment_transaction.form_feedback(cr, uid, self.post_data,
                                                   'paysera', context=ctx)

        tx_id = self.payment_transaction.create(
            cr, uid, {
                'amount': 32000,
                'acquirer_id': self.paysera_id,
                'currency_id': self.currency_euro_id,
                'reference': 'SO012',
                'partner_id': self.buyer_id,
            }, context=ctx
        )

        # Validate again.
        self.payment_transaction.form_feedback(cr, uid, self.post_data,
                                               'paysera', context=ctx)

        # Check transaction state.
        tx = self.payment_transaction.browse(cr, uid, tx_id, context=ctx)
        self.assertEqual(tx.state, 'done',
                         'paysera: validation did not put tx into done state')
