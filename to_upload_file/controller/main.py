import json
import os
import uuid
from werkzeug.exceptions import NotFound

from odoo import http, _
from odoo.tools import config


class UploadFileController(http.Controller):
    def _get_storage_dir_path(self):
        return config.filestore(http.request.db) + '/to_upload_file'

    def _create_storage_dir_if_not_exists(self):
        dir_path = self._get_storage_dir_path()
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

    def _get_stored_file_path(self, filename):
        # A trick to avoid hack. The filename can then safely be passed to os.path.join()
        filename = os.path.basename(filename)

        dir_path = self._get_storage_dir_path()
        file_path = os.path.join(dir_path, filename)
        return file_path

    def _get_stored_filename(self, origin_filename):
        # Because all files are stored in a one level directory,
        # we modify the filename to make it unique.
        return '%s_%s' % (uuid.uuid4().hex, origin_filename)

    def _get_origin_filename(self, stored_filename):
        return stored_filename[33:] or stored_filename

    @http.route('/to_upload_file/upload', type='http', auth="user", methods=['POST'])
    def upload(self, file, **kwargs):
        try:
            self._create_storage_dir_if_not_exists()
            filename = self._get_stored_filename(file.filename)
            file_path = self._get_stored_file_path(filename)
            file.save(file_path)
            res = {'file_path': file_path}
        except Exception as e:
            res = {'error': _("An error has occurred!")}
        return json.dumps(res)

    @http.route('/to_upload_file/download/<string:filename>', type='http', auth="user", methods=['GET'])
    def download(self, filename, **kwargs):
        if not filename:
            raise NotFound
        file_path = self._get_stored_file_path(filename)
        if not os.path.exists(file_path):
            raise NotFound
        origin_filename = self._get_origin_filename(filename)
        return http.send_file(file_path, as_attachment=True, filename=origin_filename)
