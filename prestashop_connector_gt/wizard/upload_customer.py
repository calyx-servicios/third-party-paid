from odoo import api, fields, models
from odoo import tools
from odoo.tools.translate import _
from odoo.exceptions import UserError

class upload_customer(models.TransientModel):
    _name="prestashop.upload.customer"
    _description = 'Upload Customer'
    
    prestashop_id=fields.Many2one('prestashop.instance','Prestashop Instance')
     
    # @api.one
    def upload_customer(self,context=None,res_ids=None,presta_id=None):
        if context==None:
            context=self._context
        else:
            context=context
        if  res_ids and isinstance(res_ids,list):
            rec_list=res_ids
            presta_inst_id=presta_id
        else:
            active_ids=context.get('active_ids')
            rec_list=active_ids
            presta_inst_id=self.prestashop_id.id
        for rec in rec_list:
            res_obj=self.env['res.partner'].browse(rec)
            prestashop=self.env['sale.shop'].browse(1).presta_connect_json()
            prestashop.debug = True
            customer_search_ids=prestashop.search('customers',options={'filter[email]':res_obj.email})
            if not customer_search_ids:
                customer_schema=prestashop.get('customers',options={'schema': 'blank'})
                try:
                    customer_name=res_obj.name
                    name=customer_name.split(' ',1)
                except Exception,e:
                    raise UserError(_('Error !'),'Please Set a Last Name')
                if not res_obj.date_of_birth:
                    raise UserError(_('Error !'),'Please Set Date of Birth')
                if not res_obj.email:
                    raise UserError(_('Error !'),'Please Set your Email ID')
                if not res_obj.prestashop_paswrd:
                    raise UserError(_('Error !'),'Please Set A Password of Five characters minimum')   
                customer_schema['customer'].update({'firstname':name[0],
                                                    'lastname':name[1],
                                                    'passwd':res_obj.prestashop_paswrd,
                                                    'email':res_obj.email,
                                                    'birthday':res_obj.date_of_birth,
                                                    'active':1
                                                        })
                customer_schema['customer']['associations']['groups'].update({'value':3})
                customer_elem= prestashop.add('customers',customer_schema)
                customer_id=customer_elem['prestashop']['customer']['id']
            else:
                customer_id=customer_search_ids[0]
            address_elem=self.upload_address(prestashop,customer_id,res_obj)
            if address_elem and not isinstance(address_elem,int):
                address_id=address_elem['prestashop']['address']['id']
                return customer_id,address_id
            else:
                address_id=address_elem
                return customer_id, address_id
                       
    def upload_address(self,prestashop,customer_id,res_obj):
        try:
            customer_name=res_obj.name
            name=customer_name.split(' ',1)
        except Exception,e:
            raise UserError(_('Error !'),'Please Set a Last Name')
        address_search_ids=prestashop.search('addresses',options={'filter[id_customer]':customer_id})
        if not address_search_ids:
            address_schema=prestashop.get('addresses',options={'schema':'blank'})
            address_schema['address'].update({ 'id_customer':customer_id,                                           
                                               'lastname':name[1],
                                               'firstname':name[0],
                                               'address1':res_obj.street or False,
                                               'address2':res_obj.street2 or False,
                                               'postcode':res_obj.zip or False,
                                               'city':res_obj.city or False,
                                               'alias':'My address'
                                               })
            if res_obj.phone :
                address_schema['address'].update({'phone':res_obj.phone})
            
            if res_obj.mobile:
                address_schema['address'].update({'phone_mobile':res_obj.mobile})
            
            # To set the state id in the address
            state_obj=res_obj.state_id
            state_id=self.upload_state(prestashop,state_obj)
            if state_id:
                address_schema['address'].update({'id_state':state_id})
            else:
                raise osv.except_osv(_('Error !'),'Please Select A State')
            
            #To set the country_id in the address
            country_name=res_obj.country_id.name
            country_id=self.search_country(prestashop,country_name)
            if country_id:
                address_schema['address'].update({'id_country':country_id})
            else:
                raise osv.except_osv(_('Error !'),'Please Select A Country')
            
            
            addrs = prestashop.add('addresses',address_schema)
        else:
            addrs=address_search_ids[0]
        return addrs
            

    
    def upload_state(self,prestashop,state_obj):
        #To find the state id in prestashop or else create
        state_ids= prestashop.search('states',options={'filter[name]':state_obj.name})
        if state_ids:
            state_id=state_ids[0]
            return state_id
        else:
            stats_schema=prestashop.get('states',options={'schems':'blank'})
            country_elemnt= prestashop.search('countries',options={'filter[name]':state_obj.country_id.name})
            country_id_elemnt=country_elemnt['countries']['country']
            if country_id_elemnt:
                state_country_id=int(country_id_elemnt['attrs']['id'])
                zone_id=int(country_id_elemnt['id_zone'])
                stats_schema['state'].update({
                                             'iso_code':state_obj.code,
                                             'id_country':state_country_id,
                                             'id_zone':zone_id,
                                             'name':state_obj.name
                                             })
                state_elem=prestashop.add('states',stats_schema)
                state_id=state_elem['states']['state']['attrs']['id']
                return state_id

    def search_country(self,prestashop,country_name):
        
        # To find the country id in prestashop
        country_ids= prestashop.search('countries',options={'filter[name]':country_name})
        if country_ids:
            country_id=country_ids[0]
            return country_id

