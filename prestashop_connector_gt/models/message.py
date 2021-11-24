# -*- coding: utf-8 -*-
#############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, models, _
import socket
from datetime import timedelta, datetime, date, time
import time
#import mx.DateTime as dt
from odoo import netsvc
from odoo.tools.translate import _
import urllib
import base64
from operator import itemgetter
from itertools import groupby
#
import logging
import cgi
#import ast
import odoo.addons.decimal_precision as dp
import random

class sale_order_messages(models.Model):
    _name='order.message'


    employee_id=fields.Many2one('res.partner','Employee')
    customer_id=fields.Many2one('res.partner', related='thread_id.customer_id')
    thread_id=fields.Many2one('customer.threads','Thread')
    email = fields.Char(related='thread_id.email')
    token = fields.Char(related='thread_id.token')
    status = fields.Char(related='thread_id.status')
    status = fields.Char(related='thread_id.status')
    msg_prest_id=fields.Integer('MSG ID')
    message=fields.Text('Message')
    private=fields.Boolean('Private')
    new_id = fields.Many2one('sale.order','Order')
    shop_ids = fields.Many2many('sale.shop', 'message_shop_rel', 'mess_id', 'shop_id', string="Shop")
    to_be_exported = fields.Boolean(string="To be exported?")


    # @api.onchange('customer_id')
    # def onchange_customer_id(self):
    #     self.env['res.partner'].search([('customer_id','=',)])
    
    # @api.one
    def upload_customer_message(self):
        # prestashop=self.new_id.shop_id.presta_connect_json()
        prestashop=self.new_id.shop_id.presta_connect()
        thread_schema=prestashop.get('customer_threads',options={'schema':'blank'})
        shop_id=prestashop.search('shops',options={'filter[name]':self.new_id.shop_id.name})
        order_id=prestashop.search('orders',options={'filter[reference]':self.new_id.presta_order_ref})
        customr_id=prestashop.search('customers',options={'filter[email]':self.new_id.partner_id.email})
        # print ("thread_schema['customer_thread']]]]]]]",thread_schema['customer_thread'])
        thread_schema['customer_thread'].update({
                                              'status':self.status,
                                              'id_shop':shop_id[0],
                                              'id_order':order_id[0],
                                              'id_customer':customr_id[0],
                                              'id_contact':0,
                                              'id_lang':1,
                                              })

        if self.new_id.token:
            if not self.token:
                token=self.new_id.token
            else:
                token=self.token
            id_customer_thread=prestashop.search('customer_threads',options={'filter[token]':token})
            
        else:
            token=random.randint(100000000000,999999999999)
            thread_schema['customer_thread'].update({'token':token})
            self.write({'token':token})
            id_customer_thread=prestashop.add('customer_threads',thread_schema)
            id_customer_thread=[id_customer_thread['prestashop']['customer_thread']['id']]
            
        msg=self.message
        msg_schema=prestashop.get('customer_messages',options={'schema':'blank'})
        msg_schema['customer_message'].update({
                                               'message':msg,
                                               'id_lang':1,
                                               'id_customer_thread':id_customer_thread[0],
                                               })    
        if self.employee_id:
            empl_email=self.employee_id.email
            empl_id=prestashop.search('employees',options={'filter[email]':empl_email})
            msg_schema['customer_message'].update({
                                                   'id_employee':empl_id
                                                   }) 

        elif self.customer_id:
            cust_email=self.customer_id.email
            cust_id=prestashop.search('customers',options={'filter[email]':cust_email})
            msg_schema['customer_message'].update({
                                                   'id_customer':cust_id[0],
                                                   
                                                   }) 
        cust_msg_id=prestashop.add('customer_messages',msg_schema)
        cust_msg_id=cust_msg_id['prestashop']['customer_message']['id']
        thread_schema['customer_thread']['associations']['customer_messages'].update({'customer_message':[{'id':cust_msg_id}]})
        thread_schema['customer_thread'].update({'id':id_customer_thread[0],'token':token})
        x=prestashop.edit('customer_threads',id_customer_thread[0],thread_schema)
        self.write({'msg_prest_id':cust_msg_id})
        return True
        
sale_order_messages()

class customer_threads(models.Model):
    _name = 'customer.threads'

    presta_id = fields.Char('Presta ID')
    id_shop = fields.Char('Shop ID')
    order_id = fields.Many2one('sale.order')
    customer_id = fields.Many2one('res.partner', 'Customer')
    status = fields.Char('Status')
    email = fields.Char('Email')
    employee_id = fields.Many2one('res.partner', 'Employee')
    token = fields.Char('Token')