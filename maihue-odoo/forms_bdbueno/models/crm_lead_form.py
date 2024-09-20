# -*- coding: utf-8 -*-
# Copyright (C) 2022 - TODAY, Jescalante@blueminds.cl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.addons.fleet.models.fleet_vehicle_model import FUEL_TYPES
import base64
import json
import requests
from urllib.request import urlretrieve
from urllib.parse import urlencode
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class CrmLeadForm(models.Model):
    _name = 'crm.lead.form'

    # def api_form_cron(self):
    #     if last_odometer:
    #         self.call_api_form_cron(last_odometer)

    def hide_api_crm_form(self):
        self.api_crm_form = self.company_id.is_form

    api_crm_form = fields.Boolean(computed=hide_api_crm_form)

    def call_api_form_cron(self):
        now = datetime.now()
        config = self.env['ir.config_parameter'].sudo()
        lead = self.env['crm.lead']
        if self.env.company.is_form:
            # url = str(config.get_param('tag_url')) + str(config.get_param('odo_user')) + '?'
            url = 'https://form-qa.maihuechile.cl/api/v1/formularios'
            response = requests.get(url, auth=('test', '3w5q3woq0qww'))
            if response.status_code != 200:
                raise UserError('Por favor contacte con el Administrador: ' + str(response.text))
            dict_list = json.loads(response.text.encode('utf8'))
            if dict_list:
                for res in dict_list:
                    form =  json.loads(res.get('formulario').encode('utf8'))
                    var = 1
                    vat = form.get('RUT') #res.get('formulario'):
                    partner = self.env['res.partner'].sudo().search([('vat', '=', vat)],
                                                                            limit=1)
                    if not partner:
                        partner = partner.sudo().create({
                            'name': form.get('nombre'),
                            #'customer': True,
                            'vat': form.get('RUT'),
                            'street': form.get('direccion'),
                            'phone0': form.get('celular'),
                            # el metodo de pago tiene que ir en un campo referencial
                            # servicio referencial (son no editables en nunca ni en lead )
                            # Direccion servicio referencial
                            # cantidad de equipos
                            # se debe concatenar todos en descripcion de formulario
                            'email': form.get('your-email')
                        })
                        # el check de contrato por default debe ser True
                    self.env['crm.lead'].sudo().create({
                        'partner_id': partner.id,
                        'name': partner.name,
                        'email_from': partner.email,
                        'type': 'lead',
                        'street': partner.street,
                        'phone': partner.phone0,
                        #'description': dict_list.get('your-message'),
                        'api_form': res.get('formulario_uuid'),
                        'api_payment': str(form.get('pago1')) + ' ' + str(form.get('pago2')),
                    })
        return True
        # Odometer = self.env['fleet.vehicle.odometer']
        # now = datetime.now()
        #
        # config = self.env['ir.config_parameter'].sudo()
        # if not config.get_param('api_odometer'):
        #     raise UserError('Operacion no permitida, contacte al Administrador para activar API TAG y Multas.')
        # # fecha1 = datetime.now() - relativedelta(days=1)
        # # fecha2 = datetime.now()
        # url = str(config.get_param('tag_url')) + str(config.get_param('odo_user')) + '?'
        # # url = 'http://api.smartreport.cl/v2/odometro/klugrent?token=c175289b8a2fca7ce92ecf9ba6f3a6c2&patente=PYFV-13&fecha1=2022-08-31%2006:20:00&fecha2=2022-08-31%2018:30:30'
        # license_plate = last_odometer.vehicle_id.license_plate[:-2] + "-" + last_odometer.vehicle_id.license_plate[4:6]
        # params = {
        #     'token': config.get_param('odo_token'),
        #     'patente': license_plate,
        #     'fecha1': str(last_odometer.date.strftime("%Y-%m-%d  %H:%M:%S")),
        #     'fecha2': str(now.strftime("%Y-%m-%d %H:%M:%S"))
        # }
        # metodo = []
        # qstr = urlencode(params)
        # print(json.dumps(params, indent=4, ensure_ascii=False))
        # response = requests.post(url + qstr)
        # if response.status_code != 200:
        #     raise UserError('Por favor contacte con el Administrador: %s', response.text)
        # dict_list = json.loads(response.text.encode('utf8'))
        # if dict_list.get('status') != 0 and dict_list.get('status') != 4:
        #     pass
        #     # jamie = dict_list.get('mensaje')
        #     # raise UserError('Por favor revise el siguiente error: ' + str(dict_list.get('mensaje')))
        # if dict_list.get('tag'):
        #     for tag in dict_list.get('tag'):
        #         vals_tag = {
        #             'vehicle_id': last_odometer.vehicle_id.id,
        #             'date': datetime.strptime(str(tag.get('fecha')), '%d-%m-%Y %H:%M'),
        #             'tag_ids': [1],
        #             'amount': tag.get('tarifa'),
        #             'concession': tag.get('concesion'),
        #             'description': tag.get('description'),
        #             'category': tag.get('categoria'),
        #         }
        #         Odometer.create(vals_tag)
        # if dict_list.get('multa'):
        #     for tag in dict_list.get('multa'):
        #         vals_multa = {
        #             'vehicle_id': last_odometer.vehicle_id.id,
        #             'date': datetime.strptime(str(tag.get('fecha')), '%d-%m-%Y %H:%M'),
        #             'tag_ids': [7],
        #             'amount': tag.get('tarifa'),
        #             'description': tag.get('via'),
        #             'category': tag.get('tipo_multa'),
        #         }
        #         Odometer.create(vals_multa)
        # if dict_list.get('incidencia'):
        #     for tag in dict_list.get('incidencia'):
        #         vals_incidencia = {
        #             'vehicle_id': last_odometer.vehicle_id.id,
        #             'date': datetime.strptime(str(tag.get('fecha')), '%d-%m-%Y'),
        #             'name': tag.get('proveedor'),
        #             'mensaje': tag.get('mensaje'),
        #             'mensaje_consul': dict_list.get('mensaje'),
        #         }
        #         self.env['fleet.vehicle.incidencia'].create(vals_incidencia)