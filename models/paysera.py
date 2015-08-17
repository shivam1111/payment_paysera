# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
import urllib
import urlparse

from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.addons.payment_paysera.controllers.main import PayseraController

from openerp import models, fields
from openerp.tools import float_round

_logger = logging.getLogger(__name__)

API_VERSION = '1.6'

HAS_M2CRYPTO = True
try:
    from M2Crypto import X509
except ImportError:
    HAS_M2CRYPTO = False
    _logger.info('M2Crypto is not installed. '
                 'Will use a lower security level MD5 signature only.')

# ISO-639-1 -> ISO-639-2/B
LANG_MAP = {
    'lt': 'LIT',
    'lv': 'LAV',
    'et': 'EST',
    'ru': 'RUS',
    'en': 'ENG',
    'de': 'GER',
    'pl': 'POL',
}

# Paysera's Public Key certificate.
# Refer to: https://www.webtopay.com/download/public.key
PAYSERA_CERT = """-----BEGIN CERTIFICATE-----
MIIECTCCA3KgAwIBAgIBADANBgkqhkiG9w0BAQUFADCBujELMAkGA1UEBhMCTFQx
EDAOBgNVBAgTB1ZpbG5pdXMxEDAOBgNVBAcTB1ZpbG5pdXMxHjAcBgNVBAoTFVVB
QiBFVlAgSW50ZXJuYXRpb25hbDEtMCsGA1UECxMkaHR0cDovL3d3dy5tb2tlamlt
YWkubHQvYmFua2xpbmsucGhwMRkwFwYDVQQDExB3d3cubW9rZWppbWFpLmx0MR0w
GwYJKoZIhvcNAQkBFg5wYWdhbGJhQGV2cC5sdDAeFw0wOTA3MjQxMjMxMTVaFw0x
NzEwMTAxMjMxMTVaMIG6MQswCQYDVQQGEwJMVDEQMA4GA1UECBMHVmlsbml1czEQ
MA4GA1UEBxMHVmlsbml1czEeMBwGA1UEChMVVUFCIEVWUCBJbnRlcm5hdGlvbmFs
MS0wKwYDVQQLEyRodHRwOi8vd3d3Lm1va2VqaW1haS5sdC9iYW5rbGluay5waHAx
GTAXBgNVBAMTEHd3dy5tb2tlamltYWkubHQxHTAbBgkqhkiG9w0BCQEWDnBhZ2Fs
YmFAZXZwLmx0MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDeT23V/kNtf/hr
Nae/ZsLfRZd8E+os6HZ9CbgvB+X659kBDBq5vjMDCVkY6sicn1fcFfuotEcbhKSK
DrDAQ+DmCMm96C7A4gqCC5OqmINauxYDdbie7V9GJWnbRXDs/5Mu722f5TuOUG3H
hN/vTg8uCxIrGIYv9idhvTbDyieVCwIDAQABo4IBGzCCARcwHQYDVR0OBBYEFI1V
hRQeacLkR4OekokkQq0dFDAHMIHnBgNVHSMEgd8wgdyAFI1VhRQeacLkR4Oekokk
Qq0dFDAHoYHApIG9MIG6MQswCQYDVQQGEwJMVDEQMA4GA1UECBMHVmlsbml1czEQ
MA4GA1UEBxMHVmlsbml1czEeMBwGA1UEChMVVUFCIEVWUCBJbnRlcm5hdGlvbmFs
MS0wKwYDVQQLEyRodHRwOi8vd3d3Lm1va2VqaW1haS5sdC9iYW5rbGluay5waHAx
GTAXBgNVBAMTEHd3dy5tb2tlamltYWkubHQxHTAbBgkqhkiG9w0BCQEWDnBhZ2Fs
YmFAZXZwLmx0ggEAMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADgYEAwIZw
Rb2E//fmXrcO2hnUYaG9spg1xCvRVrlfasLRURzcwwyUpJian7+HTdTNhrMa0rHp
NlS0iC8hx1Xfltql//lc7EoyyIRXrom4mijCFUHmAMvR5AmnBvEYAUYkLnd/QFm5
/utEm5JsVM8LidCtXUppCehy1bqp/uwtD4b4F3c=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE REQUEST-----
MIIB+zCCAWQCAQAwgboxCzAJBgNVBAYTAkxUMRAwDgYDVQQIEwdWaWxuaXVzMRAw
DgYDVQQHEwdWaWxuaXVzMR4wHAYDVQQKExVVQUIgRVZQIEludGVybmF0aW9uYWwx
LTArBgNVBAsTJGh0dHA6Ly93d3cubW9rZWppbWFpLmx0L2JhbmtsaW5rLnBocDEZ
MBcGA1UEAxMQd3d3Lm1va2VqaW1haS5sdDEdMBsGCSqGSIb3DQEJARYOcGFnYWxi
YUBldnAubHQwgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAN5PbdX+Q21/+Gs1
p79mwt9Fl3wT6izodn0JuC8H5frn2QEMGrm+MwMJWRjqyJyfV9wV+6i0RxuEpIoO
sMBD4OYIyb3oLsDiCoILk6qYg1q7FgN1uJ7tX0YladtFcOz/ky7vbZ/lO45QbceE
3+9ODy4LEisYhi/2J2G9NsPKJ5ULAgMBAAGgADANBgkqhkiG9w0BAQUFAAOBgQAr
GZJzT9Tzvo6t6/mOHr4NsdyVopQm0Ym0mwcrs+4qC4yfz0kj7STjcUnPlz1OP+Vp
aPoe4aREKf58SAZGfZqeiYhl2IL7i3PoeN/DThSwcFcb3YFpMG9EkRDfC/c2H0x7
GFYXlI9ODyfBPa02o44sQdqmdhCQCqvS5/5vhflJ9A==
-----END CERTIFICATE REQUEST-----
"""


def decode_form_data(encoded_data):
    """
    Decodes base64 encoded string, parses it and returns a dict of parameters

    :Parameters:
      - `encoded_data`: base64 encoded URL parameters list
    """
    decoded = base64.b64decode(encoded_data.encode('ascii'), altchars='-_')
    parsed = urlparse.parse_qsl(decoded, keep_blank_values=True)
    return {k: v.decode('utf-8') for k, v in parsed}


def encode_strings(dict_):
    """
    Encodes string values in the dict in UTF-8. Other values are untouched.
    """
    for k, v in dict_.iteritems():
        if isinstance(v, unicode):
            dict_[k] = v.encode('utf-8')
    return dict_


class AcquirerPaysera(models.Model):

    _inherit = 'payment.acquirer'

    paysera_project_id = fields.Char(
        'Project ID', size=11, required_if_provider='paysera',
        help='Unique Paysera project number'
    )
    paysera_sign_password = fields.Char(
        'Sign password', size=255, required_if_provider='paysera',
        help='Project password, which can be found by logging in to '
             'Paysera.com system, selecting “Service management” and choosing '
             '“General settings” on a specific project.'
    )

    def _get_providers(self, cr, uid, context=None):
        providers = super(AcquirerPaysera, self)._get_providers(cr, uid,
                                                                context=context)
        providers.append(['paysera', 'Paysera'])
        return providers

    def _get_paysera_urls(self, cr, uid, context=None):
        """Returns Paysera API URLs"""
        return {
            'paysera_standard_api_url': 'https://www.paysera.com/pay/',
        }

    def _paysera_generate_data_signature(self, acquirer, data):
        """Calculates and returns the MD5 hash of signed data.

        MD5 hash is calculated from (data + paysera_sign_password)."""
        assert acquirer.provider == 'paysera'

        key = acquirer.paysera_sign_password.encode('ascii') or ''
        return hashlib.md5(('%s%s' % (data, key)).encode('ascii')).hexdigest()

    def paysera_form_generate_values(self, cr, uid, id, partner_values,
                                     tx_values, context=None):
        """Generates the values used to render the form button template."""
        base_url = self.pool['ir.config_parameter'].get_param(cr, uid,
                                                              'web.base.url')
        acquirer = self.browse(cr, uid, id, context=context)

        full_url = lambda path: urlparse.urljoin(base_url, path).encode('utf-8')

        lang = partner_values['lang'] or ''
        if '_' in lang:
            lang = LANG_MAP.get(partner_values['lang'].split('_')[0], '')
        print "=======================================================",acquirer.paysera_project_id
        paysera_params = {
            'projectid': acquirer.paysera_project_id,
            'orderid': tx_values['reference'],
            'lang': lang,
            'amount': '%d' % int(float_round(tx_values['amount'], 2) * 100),
            'currency': tx_values['currency'] and tx_values['currency'].name or '',
            'accepturl': full_url(PayseraController._accept_url),
            'cancelurl': full_url(PayseraController._cancel_url),
            'callbackurl': full_url(PayseraController._callback_url),
            'country': partner_values['country'] and partner_values['country'].code or '',
            'p_firstname': partner_values['first_name'],
            'p_lastname': partner_values['last_name'],
            'p_email': partner_values['email'],
            'p_street': partner_values['address'],
            'p_city': partner_values['city'],
            'p_zip': partner_values['zip'],
            'p_countrycode': partner_values['country'] and partner_values['country'].code or '',
            'test': acquirer.environment == 'test' and '1' or '0',
            'version': API_VERSION,
        }
        _logger.debug(paysera_params)
        # urlencode needs strings
        paysera_params = encode_strings(paysera_params)

        # Concatenate the parameters into a single line and b64encode it.
        data = base64.b64encode(urllib.urlencode(paysera_params), altchars='-_')
        signature = self._paysera_generate_data_signature(acquirer, data)

        paysera_tx_values = dict(tx_values)
        paysera_tx_values.update({
            'data': data,
            'sign': signature,
        })
        return partner_values, paysera_tx_values

    def paysera_get_form_action_url(self, cr, uid, id, context=None):
        """Returns the form action URL."""

        return self._get_paysera_urls(cr, uid, context=context)['paysera_standard_api_url']


class TxPaysera(models.Model):

    _inherit = 'payment.transaction'

    def _paysera_form_get_tx_from_data(self, cr, uid, data, context=None):
        """Extracts the order ID from received data.

        Returns the corresponding transaction."""
        # Decode the encoded parameters and write them into `data` dict.
        data['params'] = decode_form_data(data.get('data', ''))

        reference = data['params'].get('orderid')
        if not reference:
            msg = 'Paysera: missing order ID in received data'
            _logger.error(msg)
            raise ValidationError(msg)

        tx_ids = self.pool['payment.transaction'].search(cr, uid,
                                                         [('reference', '=', reference)],
                                                         context=context)
        if not tx_ids or len(tx_ids) > 1:
            msg = 'Paysera: received data for reference ID: %s' % reference
            if not tx_ids:
                msg += '; no order found'
            else:
                msg += '; multiple orders found'
            _logger.error(msg)
            raise ValidationError(msg)
        tx = self.pool['payment.transaction'].browse(cr, uid, tx_ids[0],
                                                     context=context)
        return tx

    def _paysera_form_get_invalid_parameters(self, cr, uid, tx, data, context=None):
        """Checks received parameters and returns a list of tuples.

        Tuple format: (parameter_name, received_value, expected_value).

        Errors will be raised for each invalid parameters.
        Transaction will not be validated if there is at least one
        invalid parameter."""
        invalid_parameters = []

        if not data.get('data'):
            invalid_parameters.append(('data', data.get('data', ''),
                                       'SOME_VALUE'))
        if not data.get('ss1'):
            invalid_parameters.append(('ss1', data.get('ss1', ''),
                                       'SOME_VALUE'))
        if not data.get('ss2'):
            invalid_parameters.append(('ss2', data.get('ss2', ''),
                                       'SOME_VALUE'))
        params = data['params']

        signature = self.pool['payment.acquirer']._paysera_generate_data_signature(tx.acquirer_id, data.get('data'))
        if signature != data.get('ss1'):
            invalid_parameters.append(('ss1', data.get('ss1'), signature))

        if HAS_M2CRYPTO:
            signature = base64.b64decode(data.get('ss2').encode('ascii'),
                                         altchars='-_')

            pubkey = X509.load_cert_string(PAYSERA_CERT).get_pubkey()
            pubkey.verify_init()
            pubkey.verify_update(data.get('data', '').encode('ascii'))
            if pubkey.verify_final(signature) != 1:
                invalid_parameters.append(
                    ('ss2', signature, 'VALID_SS2')
                )
            else:
                _logger.debug('SS2 signature verified OK')

        # Check if `projectid` is not missing.
        if not params.get('projectid'):
            invalid_parameters.append(('projectid', params.get('projectid', ''),
                                       'NON_EMPTY'))

        # Check if `projectid`'s match.
        if not params.get('projectid') == tx.acquirer_id.paysera_project_id:
            invalid_parameters.append(('projectid', params.get('projectid', ''),
                                       tx.acquirer_id.paysera_project_id))

        # Check if Paysera's `request_id` is present. Used as
        # `acquirer_reference` for the transaction.
        if not params.get('requestid'):
            invalid_parameters.append(('request_id', params.get('requestid', ''),
                                       'SOME_VALUE'))
        return invalid_parameters

    def _paysera_form_validate(self, cr, uid, tx, data, context=None):
        # Transaction has already been completed or canceled.
        # We should not handle this request.
        if tx.state in ('done', 'cancel'):
            return False

        params = data['params']
        status = params.get('status', '2')

        # 0 - payment has not been executed
        if status == '0':
            # According to Paysera, this status means that the order can be
            # dismissed.
            tx.write({
                'state': 'cancel',
            })
            return True
        # 1 - payment successful
        elif status == '1':
            _logger.info('Order ID %s paid' % params.get('orderid'))
            tx.write({
                'state': 'done',
                'date_validate': fields.datetime.now(),
                'state_message': params.get('paytext', ''),
                'acquirer_reference': params.get('requestid'),
            })
            return True
        # 2 - payment order accepted, but not yet executed
        elif status == '2':
            tx.write({
                'state': 'pending',
                'state_message': params.get('paytext', ''),
                'acquirer_reference': params.get('requestid'),
            })
            return True
        # 3 - additional payment information
        elif status == '3':
            # This is typically additional information about the bank account
            # number or about personal code, if such request was made.
            # We do not store this info, so let's do nothing.
            return True
        else:
            error = 'Paysera: feedback error'
            _logger.info(error)
            tx.write({
                'state': 'error',
                'state_message': error,
            })
            return False
