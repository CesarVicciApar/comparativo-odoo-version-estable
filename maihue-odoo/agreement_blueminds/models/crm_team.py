# -*- coding: utf-8 -*-

from odoo import api, models, fields,_
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

from odoo.fields import Date

class Team(models.Model):
    _inherit = 'crm.team'

    def _compute_template(self):
        res = {}
        templates_all = self.search([])
        arrs = []
        today = datetime.now()
        domain = [('is_template', '=', True), ('fecha_termino_date', '>=', today), ('initemplate_date', '<=', today)]
        templates_ids = self.env['agreement'].sudo().search([
            ('is_template', '=', True),
            ('fecha_termino_date', '>=', today),
            ('initemplate_date', '<=', today),
            ('is_template', '=', True),
            ('type_contrib', '=', 1),
            ('team_id_domain', 'in', self.id)])
        exc_templates_ids = self.env['agreement'].sudo().search([
            ('is_template', '=', True),
            ('fecha_termino_date', '>=', today),
            ('initemplate_date', '<=', today),
            ('type_contrib', '=', 1),
            ('is_template', '=', True),
            ('exception_team_id_domain', 'in', self.id)])
        template_domain_company = []
        if templates_ids:
            for temp in templates_ids:
                template_domain_company.append(temp.id)
        if exc_templates_ids:
            for exc in exc_templates_ids:
                if exc.id not in template_domain_company:
                    template_domain_company.append(exc.id)
        templates_person = self.env['agreement'].sudo().search([
            ('is_template', '=', True),
            ('fecha_termino_date', '>=', today),
            ('initemplate_date', '<=', today),
            ('type_contrib', '=', 2),
            ('is_template', '=', True),
            ('team_id_domain', 'in', self.id)])
        exc_templates_person = self.env['agreement'].sudo().search([
            ('is_template', '=', True),
            ('fecha_termino_date', '>=', today),
            ('initemplate_date', '<=', today),
            ('type_contrib', '=', 2),
            ('is_template', '=', True),
            ('exception_team_id_domain', 'in', self.id)])
        template_domain_person = []
        if templates_person:
            for tempe in templates_person:
                template_domain_person.append(tempe.id)
        if exc_templates_person:
            for excp in exc_templates_person:
                if excp.id not in template_domain_person:
                    template_domain_person.append(excp.id)
        self.template_domain_company = template_domain_company
        self.template_domain_person = template_domain_person

    template_agreement_company = fields.Many2one('agreement', string='Plantilla Juridico')
    template_agreement_person = fields.Many2one('agreement', string='Plantilla Natural')
    exception_agreement_id = fields.Many2one('agreement', string='Template exception', domain=[('is_template', '=', True)])
    template_domain_company = fields.Many2many('agreement', 'template_company_team_rel', 'parent_id',
                                       'team_id', compute='_compute_template',
                                       string='Dominio Juridico')
    template_domain_person = fields.Many2many('agreement', 'template_person_team_rel', 'parent_id',
                                       'team_id', compute='_compute_template',
                                       string='Dominio Natural')
