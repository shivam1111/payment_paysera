# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (c) 2011-2012 OpenERP S.A. <http://openerp.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import osv, fields

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def _edi_paypal_data(self, cr, uid, ids, field, arg, context=None):
        res = {}
        acquirer_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, "payment_paysera", 'payment_acquirer_paysera')[1]        
        acquirer_obj = self.pool.get('payment.acquirer')
        for invoice in self.browse(cr,uid,ids,context):
            partner_id = invoice.partner_id
            name = partner_id.name.split(" ",1)
            partner_values = {'lang':partner_id.lang, 'city': partner_id.city, 'first_name': name[0], 'last_name': len(name) > 1 and name[1] or '', 'name': partner_id.name, 
                              'zip': partner_id.zip, 'country': partner_id.country_id, 'country_id': partner_id.country_id.id, 'phone': partner_id.phone, 
                              'state': partner_id.state_id, 'address': (partner_id.street or '') + (partner_id.street2 or '') ,'email': partner_id.email}
            

            tx_values = {
                     'currency_id':invoice.currency_id.id,
                     'currency':invoice.currency_id,
                     'amount':invoice.amount_total,
                     'reference':invoice.reference,
                     'partner':invoice.partner_id,
                     }
            data = acquirer_obj.paysera_form_generate_values(cr,uid,acquirer_id, partner_values,
                                     tx_values, context=None)
            
            res.update({
                        invoice.id:{
                                     "paysera_data":data[1].get('data',False),
                                     "paysera_sign": data[1].get('sign',False)
                                    }
                        })
        return res
    
    
    _columns = {
                'paysera_data':fields.function(_edi_paypal_data, type='char', string='Paysera Data',multi="paysera"),
                'paysera_sign':fields.function(_edi_paypal_data,type="char",string = "Paysera sign",multi="paysera")
                }