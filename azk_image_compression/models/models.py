import base64
from datetime import datetime, timedelta
import glob
import io
import logging
import os
import time
import re
from tempfile import TemporaryFile
from PIL import Image
import PIL
import binascii
from odoo import models, fields, api, exceptions
from zeep.wsdl import attachments

log = logging.getLogger(__name__)

class CompressionRules(models.Model):
    _name = 'rules'
    
    name = fields.Char(string="Name", help ="Name of the rule")
    active = fields.Boolean(string="Active", default=True, help="Set to active for the scheduled action to run it")
    models = fields.Many2many('ir.model', string="Model(s)", help="Compress only attachments to the selected models")
    source_format = fields.Char(string="Source Format", help="Regular expression e.g. image.*/*", default="image/.*bmp.*")
    destination_format = fields.Selection(
            [('jpeg','jpeg'),
            ('png','png'),
            ('bmp','bmp'),
            ('gif','gif'),
            ('ico','ico'),
            ('j2p','j2p'),
            ('jpx','jpx'),
            ('tif','tif'),
            ('webp','webp'),],
            'Destination Format', default='jpeg', required=True)
    min_size = fields.Integer(string="Minimum size (KB)",help="Minimum size to match (KB)")
    replace_all = fields.Boolean(string="Replace all", default=True, help="Compress all instances that have the same image content even if it matches another model")
    newer_than = fields.Integer(string="Newer than (days)", help="Process attachments that where added from newer_than days till now")
    older_than = fields.Integer(string="Older than (days)",help="Process attachments that where added before older_than days till now")
    quality = fields.Integer(string="Quality", help="0 to 100 the lower the value the maximum compression", default=90)
    
    @api.constrains('quality')
    def _validate_quality(self):
        if any(map(lambda r: r.quality and (r.quality > 100 or r.quality <= 0), self)):
            raise exceptions.ValidationError("""Quality should be between ]0 and 100] for: %s""" % (r.name))
    
    def execute_rule(self, res_model=None, res_id=None, limit=50):
        """
        @param res_model: (string) if specified with res_id it selects that model attachment and compresses them
        @param res_id: works with res_model to filter only attachments for that res_model,res_id  
        @param limit: default to 50 in order to prevent timeout if ran from UI
        """
        compressed_attachments = 0
        compressed_fnames = set()
        total_start_size = 0
        total_final_size = 0
        
        for rule in self:
            model_names = list(map(lambda m:m.model, rule.models))
            if res_model and res_id:
                attach_search_domain = [
                                        '|', ('res_field', '!=', False), ('res_field', '=', False),
                                        ('res_model', '=', res_model),
                                        ('res_id', '=', res_id)
                                        ]
            else:  
                attach_search_domain = [('id', '!=', False),
                                        ('compressed_on', '=', False),
                                        ('res_model', 'in', model_names),
                                        ('file_size', '>=', (rule.min_size * 1000)),]
            
                if rule.newer_than and rule.newer_than > 0:
                    attach_search_domain.append(('create_date', '>', datetime.now()-timedelta(days=rule.newer_than)))
             
                if rule.older_than and rule.older_than > 0:
                    attach_search_domain.append(('create_date', '<', datetime.now()-timedelta(days=rule.older_than)))
            
            re_match = re.compile(rule.source_format, re.I)
            attachments = self.env['ir.attachment'].search(attach_search_domain).filtered(lambda r: re_match.search(r.mimetype))
            if limit:
                attachments = attachments[0:limit]
            
            log.info("Matched %s records using rule: %s from source format %s to destination format %s, with minimum size %s , newer than %s days and older than %s days and model/res_id: %s[%s] with search domain: %s with limit: %s", 
                        len(attachments), rule.name,rule.source_format,rule.destination_format,rule.min_size,rule.newer_than,rule.older_than, res_model, res_id, attach_search_domain, limit)
            
            for atc in attachments:
                orig_fname = atc.store_fname
                
                if orig_fname not in compressed_fnames:
                    before = time.time()
                    old_img_deleted = False
                    
                    try:
                        orig_size = atc.file_size
                        
                        is_attachment = True
                        temp_file = None
                        
                        if atc.db_datas:
                            is_attachment = False
                            temp_file = TemporaryFile('wb+')
                            temp_file.write(base64.b64decode(atc.db_datas))
                            im = Image.open(temp_file)
                        else:
                            file_path = atc._full_path(atc.store_fname)
                            im = Image.open(file_path)
                        
                        if im.mode in ("RGBA", "P"):
                            im = im.convert("RGB")
                            
                        compressed_img = io.BytesIO()
                        im.save(compressed_img, format=rule.destination_format, optimize=True, quality=rule.quality)
                        
                        compressed_bytes = compressed_img.getvalue()
                        checksum = atc._compute_checksum(compressed_bytes)
            
                        old_name = atc.name
                        filename, file_extension = os.path.splitext(old_name)
                        new_name = '%s.%s' % (filename, rule.destination_format)
                        
                        #in case im.convert('RGB') is called im.format will become null
                        if im.format and im.format in Image.MIME:
                            mimetype = Image.MIME[im.format]
                        else:
                            mimetype = Image.MIME.get(rule.destination_format.upper(), 'image/%s'% (rule.destination_format) )
                        
                        update_dict = {
                            'name' : new_name,
                            'display_name' : new_name,
                            'mimetype': mimetype,
                            'compressed_on': datetime.now()
                            }
                        
                          
                        new_file_data = atc._get_datas_related_values(compressed_bytes, mimetype)
                        update_dict.update(new_file_data)

                        encoded_bytes = base64.b64encode(compressed_bytes)
                        update_dict.update({'datas': encoded_bytes})
                        
                        atc.write(update_dict)
                        if atc.res_field:
                            self.fix_model_filename(atc,rule)
                            
                        new_size = len(compressed_img.getvalue())
                        destination = rule.destination_format
                        
                        if rule.replace_all and is_attachment:
                            compressed_fnames.add(orig_fname)
                            attachments_copy = self.env['ir.attachment'].search([('id', '!=', atc.id),('store_fname', '=', orig_fname)])
                            
                            for d_act in attachments_copy:
                                update_dict.update({
                                                    'name' : '%s.%s' % (os.path.splitext(d_act.name)[0], destination),
                                                    'mimetype': mimetype,
                                                    'datas': encoded_bytes,
                                                    'compressed_on': datetime.now(),})
                                d_act.write(update_dict)                          
                                    
                                if d_act.res_field:
                                    self.fix_model_filename(d_act,rule)
                                        
                            compressed_fnames.add(update_dict['name'])
                            
                        compressed_attachments += 1
                        total_start_size += orig_size
                        total_final_size += new_size
                        
                        
                            
                        if self.env['ir.attachment'].search_count([('store_fname', '=', orig_fname)]) == 0:
                            self.env.cr.commit()
                            os.remove(file_path)
                            old_img_deleted = True
                            
                        if temp_file:
                            temp_file.close()
                        
                        log.info("Compressing attachment for: %s, %s[%s] %s from size:%s to: %s created: %s new fname: %s  deleted: %s in %0.2fs",
                                  atc.id, atc.res_model, atc.res_id, orig_fname, "{:,}".format(orig_size), "{:,}".format(new_size), atc.create_date, atc.store_fname, old_img_deleted, time.time() - before)

                    except:
                        log.error("Failed to process %s for img: %s and rule: %s", atc, atc.store_fname, rule, exc_info=1)
        res = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Compression Done',
                    'message': 'Compressed %s attachments from total size %s to %s.' % (compressed_attachments,"{:,}".format(total_start_size),"{:,}".format(total_final_size)),
                    'sticky': False,
                    'type': 'success',
                }
            }
            
        return res    
        
    @api.model
    def _execute_rules(self, limit=None):
        ''' called by cron job '''
        active_rules = self.env['rules'].search([('active', '!=', False)])
        
        active_rules.execute_rule(limit=limit)
            
    def fix_model_filename(self, attachment,rule):
        model_rec = self.env[attachment.res_model].search([('id', '=', attachment.res_id)])
        model_fieldname = '%s_filename' % (attachment.res_field, )
        
        if hasattr(model_rec, model_fieldname):
            old_model_filename = getattr(model_rec, model_fieldname)
            filename, file_extension = os.path.splitext(old_model_filename)
            new_model_filename = '%s.%s' % (filename, rule.destination_format)
            setattr(model_rec, model_fieldname, new_model_filename)
        
    
class DebugRule(models.TransientModel):
    _name = "debug.rule"
    
    res_model = fields.Char(string="Model", help="Select the specific model to run the rule on")
    res_id = fields.Char(string="Resource ID", help="Select the ID of the Object to run this rule on")

    def execute_debug_rule(self):
        rule = self.env['rules'].browse(self.env.context.get('active_id'))
        rule.execute_rule(self.res_model, self.res_id)
        
    
class Attachments(models.Model):
    _inherit = 'ir.attachment'
    
    compressed_on = fields.Datetime(string="Compressed On", readonly=True, default = None)
