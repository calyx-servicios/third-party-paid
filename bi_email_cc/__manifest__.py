{
    "name": "Email CC BCC",
    "summary": """
        Email CC BCC With Reply to Option Odoo App helps users to send email to multiple partners 
        in CC and multiple partners in BCC of mail with specific reply to option.
    """,
    "author": "Calyx Servicios S.A.",
    "maintainers": ["PerezGabriela"],
    "website": "https://odoo.calyx-cloud.com.ar/",
    "license": "AGPL-3",
    "category": "Extra Tools",
    "version": "15.0.1.0.0",
    "development_status": "Production/Stable",
    "application": False,
    "installable": True,
    "depends": [
        "sale_management",
        "account"
    ],
    "data": [
        "views/account_invoice_send_views.xml",
        "views/mail_compose_message_views.xml",
        "views/res_config_settings_views.xml",
        "views/mail_views.xml",
    ],
}