{
    'name': "Upload Large File Widget",

    'summary': """
A new widget for uploading large files without limitation in size.
        """,

    'summary_vi_VN': """
Cung cấp widget cho phép tải lên các tập tin dung lượng lớn không giới hạn kích thước
    	""",

    'description': """
Problem
=======
Existing methods for uploading file in Odoo are not designed for large files.

Solution
========
This module provides a new widget (named `upload_file`) for uploading files without limitation in size. 

Usage
=====

.. code-block:: python

  file_path = field.Char(string='File Path', help="Path on the Odoo server to the uploaded file")

.. code-block:: xml

  <field name="file_path" widget="upload_file" />

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,

    'description_vi_VN': """
Vấn đề
======
Các phương thức tải lên các tập tin của Odoo không cho phép tải lên các tập tin lớn.

Giải pháp
=========
Module này cung cấp thêm một widget có tên `upload_file` cho phép tải lên các tập tin lớn không giới hạn.

Cách dùng
=========
.. code-block:: python
  file_path = field.Char(string='File Path', help="Path on the Odoo server to the uploaded file")

.. code-block:: xml
  <field name="file_path" widget="upload_file" />

Ấn bản được Hỗ trợ
==================
1. Ấn bản Community
2. Ấn bản Enterprise

    """,

    'author': "T.V.T Marine Automation (aka TVTMA),Viindoo",
    'website': "https://viindoo.com",
    'live_test_url': "https://v13demo-int.erponline.vn",
    'support': "apps.support@viindoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/assets.xml'
    ],
    'qweb': [
        'static/src/xml/templates.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'images': [
        # 'static/description/main_screenshot.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 99.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
