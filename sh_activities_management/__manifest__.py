# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    'name': "Activities Management-Advance",
    'author' : 'Softhealer Technologies',
    'website': 'https://www.softhealer.com',
    "support": "support@softhealer.com",
    'category': 'Discuss',
    'version': '13.0.37',
    "summary": "Activity Management Odoo, Activity Scheduler, Manage Employee Activity Module, Manage Supervisor Activity,filter Activity,Manage Multi Activities, Schedule Mass Activities, Dynamic Action For Multiple Activities Odoo ",
    "description": """Do you want to show the activities list beautifully? Do you want to show the well-organized structure of activities? Do you want to show completed, uncompleted activities easily to your employees? Do you want to show an activity dashboard to the employee? Do you want to manage activities nicely with odoo? Do you want to show the scheduled activity to the manager, supervisor & employee? This module helps the manager can see everyone's activity, the supervisor can see the assigned user and own activity, the user can see only own activity. Everyone can filter activity by the previous year, previous month, previous week, today, yesterday, tomorrow, weekly, monthly, yearly & custom date. You can see activities like all activities, planned activities, completed activities or overdue activities. Manager, Supervisor & Employee have their own dashboard, that provides a beautiful design on the dashboard. Hurray!
 Activity Management Odoo, Activity Scheduler Odoo,Manage Project Activity, Manage Employee Activity Module, Manage Supervisor Activity, Filter  Completed Activity By Date, Filter Planned Activity By Month, Filter Activity By Year, Filter Activity By Tomorrow, Filter Activity By Yesterday, Filter Over Due Activity By Next Year, Filter Activity By Next Month, Filter  Completed Activity By Last Month, Filter Planned Activity By Last Year, Filter Activity By Last Week, Filter Activity By Next Week Odoo,Manage Project Activity, Manage Employee Activity Module, Manage Supervisor Activity, Filter  Completed Activity By Date, Filter Planned Activity By Month, Filter Activity By Year, Filter Activity By Tomorrow, Filter Activity By Yesterday, Filter Over Due Activity By Next Year, Filter Activity By Next Month, Filter  Completed Activity By Last Month, Filter Planned Activity By Last Year App, Filter Activity By Last Week, Filter Activity By Next Week Odoo
""",
    'depends': [
        'sh_activity_base',
    ],
    'data': [
        'security/activity_security.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'data/data_sales_activity_notification.xml',
        'data/sales_activity_email_template.xml',
        'views/activity_alarm.xml',
        'views/activity_config_setting.xml',
        'wizard/feedback.xml',
        'wizard/mark_as_done.xml',
        'views/activity_views.xml',
        'views/activity_dashboard.xml',
        'wizard/mail_activity_popup.xml',
        'views/dynamic_action_view.xml',
        'views/assets.xml',
        'data/activity_reminder_mail_template.xml',
        'data/activity_reminder_cron.xml',
        'views/recurring_activities.xml',
    ],
    'qweb': [
         'static/src/xml/activity_dashboard.xml',
         'static/src/xml/systray.xml'         
    ],
    'images': ['static/description/background.png', ],
    "price": 100,
    "currency": "EUR",
    'uninstall_hook': 'uninstall_hook',
    'post_init_hook': '_sh_activity_post_init',
}
