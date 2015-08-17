# -*- coding: utf-8 -*-

import logging
import pprint

import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request

_logger = logging.getLogger(__name__)


class PayseraController(http.Controller):
    _accept_url = '/payment/paysera/accept'
    _cancel_url = '/payment/paysera/cancel'
    _callback_url = '/payment/paysera/callback'

    @http.route('/payment/paysera/accept', type='http', auth='none')
    def paysera_payment_accept(self, **post):
        _logger.info('Starting Paysera accept with post data: %s',
                     pprint.pformat(post))
        # We receive payment info when the user is redirected after a
        # successfull payment, too, although the status will most likely be `2`
        # (pending) at this point.
        request.registry['payment.transaction'].form_feedback(request.cr,
                                                              SUPERUSER_ID,
                                                              post, 'paysera',
                                                              context=request.context)
        return_url = '/shop/payment/validate'
        return werkzeug.utils.redirect(return_url)

    @http.route('/payment/paysera/cancel', type='http', auth='none')
    def paysera_payment_cancel(self, **post):
        return_url = '/shop'
        return werkzeug.utils.redirect(return_url)

    @http.route('/payment/paysera/callback', type='http', auth='none')
    def paysera_payment_callback(self, **post):
        _logger.info('Starting Paysera callback with post data: %s',
                     pprint.pformat(post))
        request.registry['payment.transaction'].form_feedback(request.cr,
                                                              SUPERUSER_ID,
                                                              post, 'paysera',
                                                              context=request.context)
        return 'OK'
