# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import http
from odoo.http import request, route


class About(http.Controller):
    @http.route('/about', auth='public', website=True)
    def about(self, **kw):
        return http.request.render('theme_jt_construction.about_page')


class Career(http.Controller):
    @http.route('/career', auth='public', website=True)
    def career(self, **kw):
        return http.request.render('theme_jt_construction.career_page')


class History(http.Controller):
    @http.route('/history', auth='public', website=True)
    def history(self, **kw):
        return http.request.render('theme_jt_construction.history_page')


class Partnerships(http.Controller):
    @http.route('/partnerships', auth='public', website=True)
    def partnerships(self, **kw):
        return http.request.render('theme_jt_construction.partnerships_page')


class Leadership(http.Controller):
    @http.route('/leadership', auth='public', website=True)
    def leadership(self, **kw):
        return http.request.render('theme_jt_construction.leadership_page')

class Services(http.Controller):
    @http.route('/services', auth='public', website=True)
    def services(self, **kw):
        return http.request.render('theme_jt_construction.services_page')

class ServicesDetails(http.Controller):
    @http.route('/services-details', auth='public', website=True)
    def services_details(self, **kw):
        return http.request.render('theme_jt_construction.services_details_page')

class Project(http.Controller):
    @http.route('/project', auth='public', website=True)
    def project(self, **kw):
        return http.request.render('theme_jt_construction.project_page')

class ProjectDetails(http.Controller):
    @http.route('/project-details', auth='public', website=True)
    def project_details(self, **kw):
        return http.request.render('theme_jt_construction.project_details_page')

# class BlogDetail(http.Controller):
#     @http.route('/blog-detail', auth='public', website=True)
#     def blog_detail(self, **kw):
#         return http.request.render('theme_jt_construction.blog_detail_page')

class Faq(http.Controller):
    @http.route('/faq', auth='public', website=True)
    def faq(self, **kw):
        return http.request.render('theme_jt_construction.faq_page')

class Testimonial(http.Controller):
    @http.route('/testimonial', auth='public', website=True)
    def testimonial(self, **kw):
        return http.request.render('theme_jt_construction.testimonial_page')

class Contact(http.Controller):
    @http.route('/contact', auth='public', website=True)
    def contact(self, **kw):
        return http.request.render('theme_jt_construction.contact_page')

class Login(http.Controller):
    @http.route('/login', auth='public', website=True)
    def login(self, **kw):
        return http.request.render('theme_jt_construction.login_page')

class Register(http.Controller):
    @http.route('/register', auth='public', website=True)
    def register(self, **kw):
        return http.request.render('theme_jt_construction.register_page')

class ThankYou(http.Controller):
    @http.route('/contact-thank-you', auth='public', website=True)
    def thankyou(self, **kw):
        return http.request.render('theme_jt_construction.contact_thank_you_page')
