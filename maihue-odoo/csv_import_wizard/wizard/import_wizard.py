# -*- coding: utf-8 -*-
import io
import csv
import base64
import re
from odoo import models, api, fields, _,SUPERUSER_ID
from datetime import datetime
from datetime import timedelta
from stdnum import get_cc_module
from odoo.exceptions import Warning, UserError
import logging
import pandas as pd
import numpy as np
import math as math
import tempfile
from timeit import default_timer as timer
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    id_factura = fields.Char(string="id factura")


class WizardImportCsvPartner(models.TransientModel):
    _name = 'wizard.import.csv.partner'
    _description = 'wizard import csv partner'

    load_csv_partner = fields.Binary(string="Load csv")

    def action_csv_partner(self):
        start_time = datetime.now()
        account = self.env['account.move']
        keys = ["ID", "Documento", "Folio", "Fecha", "RUT", "Razón social", "Exento", "Neto", "IVA"]
        csv_data = base64.b64decode(self.load_csv_partner)
        data_file = io.StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        list_csv = []
        csv_reader = csv.reader(data_file, delimiter=';')
        list_csv.extend(csv_reader)
        values = {}
        for i in range(len(list_csv)):
            field = list(map(str, list_csv[i]))
            values = dict(zip(keys, field))
            if i == 0:
                continue
            else:
                mod = get_cc_module('cl', 'rut')
                rut = values.get('RUT')
                val_rut = mod.is_valid(rut)
                if val_rut == False:
                    raise UserError("El rut ingresado |{0}| en el archivo .csv no es valido".format(rut))
                if val_rut == True:
                    count_p = 0
                    # res = self.env['res.partner'].search([ ('name', '=', values.get('Razón social')), ('vat', '=', rut) ])
                    res = self.env['res.partner'].search([ ('vat', '=', rut) ])
                    if not res:
                        partner = res.create({
                            'name': values.get('Razón social'),
                            'vat': values.get('RUT')
                        })
                        count_p += i
                        self.env['bus.bus']._sendone(self.env.user.partner_id, 'snailmail_invalid_address', {
                            'title': _("Clientes"),
                            'message': _("Los clientes se han cargado correctamente en el sistema"),
                        })
                end_time = datetime.now()
                _logger.info("\n\n>> ({}) {}: {}  | {}: {} {}: {}\n\n".format('action_csv_partner', 'Hora de Inicio', start_time, 'Tiempo de ejecucion', end_time - start_time,  'Cantidad de clientes', count_p))



class WizardImportCsv(models.TransientModel):
    _name = 'wizard.import.csv'
    _description = 'wizard import csv'

    load_csv = fields.Binary(string="Load csv")
    tipo_factura = fields.Selection([('ventas', 'Ventas'), ('compra', 'Compra')], default='ventas')

    
    def to_str(self, n):
     return str(int(n)).strip()
    def stripFrame(self, mainDataframe):
        hasMap = getattr(mainDataframe, "map", None)
        if callable(hasMap):
            mainDataframe = mainDataframe.map(lambda x: x.strip() if type(x)==str else x)
        else:
            mainDataframe = mainDataframe.applymap(lambda x: x.strip() if type(x)==str else x)      
        return mainDataframe

    def action_csv(self):
        log = ""

        xlsx = io.BytesIO(base64.b64decode(self.load_csv))
        mainDataframe = pd.read_excel(xlsx)
        mainDataframe = self.stripFrame(mainDataframe)
        self.valida_cabeceras(mainDataframe)
        ivas = self.get_ivas()
        productos = self.get_productos(mainDataframe)
        etiquetas_analiticas1 = self.get_etiquetas_analiticas1(mainDataframe)
        etiquetas_analiticas2 = self.get_etiquetas_analiticas2(mainDataframe)
        etiquetas_analiticas3 = self.get_etiquetas_analiticas3(mainDataframe)
        etiquetas_analiticas4 = self.get_etiquetas_analiticas4(mainDataframe)
        cuentas_analiticas1 = self.get_cuentas_analiticas1(mainDataframe)
        cuentas_analiticas2 = self.get_cuentas_analiticas2(mainDataframe)
        cuentas_analiticas3 = self.get_cuentas_analiticas3(mainDataframe)
        cuentas_analiticas4 = self.get_cuentas_analiticas4(mainDataframe)
        partners = self.get_partners(mainDataframe)
        document_types = self.get_type_document(mainDataframe)
        journals = self.get_journals()

        self.valida_integridad(productos, etiquetas_analiticas1,etiquetas_analiticas2,etiquetas_analiticas3,etiquetas_analiticas4,
                               cuentas_analiticas1,cuentas_analiticas2,cuentas_analiticas3,cuentas_analiticas4,
                               partners,
                               document_types)
        
        log = "Log de carga de facturas\n\n"

        dataFrame = self.get_dataFrame(mainDataframe, "facturas")
        #Primero procesamos las facturas
        log = self.read_documentos(dataFrame, 
                                   productos,  
                                   etiquetas_analiticas1,
                                   etiquetas_analiticas2,
                                   etiquetas_analiticas3,
                                   etiquetas_analiticas4,
                                   cuentas_analiticas1,
                                   cuentas_analiticas2,
                                   cuentas_analiticas3,
                                   cuentas_analiticas4,
                                   partners,
                                   document_types,
                                   journals,
                                   ivas,
                                   log, 
                                   True)
        dataFrame = self.get_dataFrame(mainDataframe, "ncnd")
        log += "\nLog de carga de Notas de crédito / Notas de débito \n\n"
        #Luego procesamos las notas de crédito y débito
        return self.read_documentos(dataFrame, 
                                    productos,  
                                    etiquetas_analiticas1,
                                    etiquetas_analiticas2,
                                    etiquetas_analiticas3,
                                    etiquetas_analiticas4,
                                    cuentas_analiticas1,
                                    cuentas_analiticas2,
                                    cuentas_analiticas3,
                                    cuentas_analiticas4,
                                    partners,
                                    document_types,
                                    journals,
                                    ivas,
                                    log, 
                                    False)
        
    def to_datetime(self, date):
        """
        Converts a numpy datetime64 object to a python datetime object 
        Input:
        date - a np.datetime64 object
        Output:
        DATE - a python datetime object
        """
        timestamp = ((date - np.datetime64('1970-01-01T00:00:00'))
                    / np.timedelta64(1, 's'))
        return datetime.utcfromtimestamp(timestamp)    
    def get_impuesto(self, ivas, move_type):
        if move_type == "out_invoice" or move_type == "out_refund":
            return  ivas.filtered(lambda i: i.type_tax_use == "sale") 
        elif move_type == "in_invoice" or move_type == "in_refund":
            return  ivas.filtered(lambda i: i.type_tax_use == "purchase") 
    def get_type_document(self, dataFrame):
        hasError = False
        error = "Los siguientes tipos de documento no existen y deben ser creados antes de continuar: \n"
        codes = list(dataFrame["ID"].str.slice(start=1, stop=3).unique()) 
        codes += list(map(self.to_str, self.unique_no_nan(dataFrame["Ref. Documento"]).tolist())) 
        if "801" in codes: codes.remove("801")
        if "802" in codes: codes.remove("802")
        codes = list(set(codes))
        retorno = self.env['l10n_latam.document.type'].with_user(SUPERUSER_ID).search([('code', 'in', codes)])
        if len(retorno) != len(codes):
            hasError = True
            if len(retorno) > 0:
                   names = map(lambda cod: cod.code, retorno)
                   no_existen = list(set(codes)-set(names)) 
                   for ne in no_existen:
                        error+=f"{ne}\n"
            else:            
                   for ne in codes:
                        error+=f"{ne}\n"
            
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }
    def unique_no_nan(self,col):
        return col.dropna().unique()    
    def get_cuentas_analiticas1(self, dataFrame):
        hasError = False
        retorno = None
        error = "Las siguientes cuentas analíticas 1 no existen y deben ser creadas antes de continuar: \n"
        analiticas = list(self.unique_no_nan(dataFrame["CUENTA ANALITICA 1"])) 
        if analiticas is not None and len(analiticas) > 0:
            retorno = self.env['account.analytic.account'].with_user(SUPERUSER_ID).search([('name', 'in', analiticas)])
            if len(retorno) != len(analiticas):
                hasError = True
                if len(retorno) > 0:
                    names = map(lambda analitica: analitica.name, retorno)
                    no_existen = list(set(analiticas)-set(names)) 
                    for ne in no_existen:
                            error+=f"{ne}\n"
                else:            
                    for ne in analiticas:
                            error+=f"{ne}\n"
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }
    def get_cuentas_analiticas2(self, dataFrame):
        hasError = False
        retorno = None
        error = "Las siguientes cuentas analíticas 2 no existen y deben ser creadas antes de continuar: \n"
        analiticas = list(self.unique_no_nan(dataFrame["CUENTA ANALITICA 2"])) 
        if analiticas is not None and len(analiticas) > 0:
            retorno = self.env['account.analytic.account.two'].with_user(SUPERUSER_ID).search([('name', 'in', analiticas)])
            if len(retorno) != len(analiticas):
                hasError = True
                if len(retorno) > 0:
                    names = map(lambda analitica: analitica.name, retorno)
                    no_existen = list(set(analiticas)-set(names)) 
                    for ne in no_existen:
                            error+=f"{ne}\n"
                else:            
                    for ne in analiticas:
                            error+=f"{ne}\n"
            
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }
    def get_cuentas_analiticas3(self, dataFrame):
        hasError = False
        retorno = None
        error = "Las siguientes cuentas analíticas 3 no existen y deben ser creadas antes de continuar: \n"
        analiticas = list(self.unique_no_nan(dataFrame["CUENTA ANALITICA 3"])) 
        if analiticas is not None and len(analiticas) > 0:
            retorno = self.env['account.analytic.account.three'].with_user(SUPERUSER_ID).search([('name', 'in', analiticas)])
            _logger.info(f"CUENTAS 3 RET===> {retorno}")
            if len(retorno) != len(analiticas):
                hasError = True
                if len(retorno) > 0:
                    names = map(lambda analitica: analitica.name, retorno)
                    no_existen = list(set(analiticas)-set(names)) 
                    for ne in no_existen:
                            error+=f"{ne}\n"
                else:            
                    for ne in analiticas:
                            error+=f"{ne}\n"
            
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }       
    def get_cuentas_analiticas4(self, dataFrame):
        hasError = False
        retorno = None
        error = "Las siguientes cuentas analíticas 4 no existen y deben ser creadas antes de continuar: \n"
        analiticas = list(self.unique_no_nan(dataFrame["CUENTA ANALITICA 4"])) 
        if analiticas is not None and len(analiticas) > 0:
            retorno = self.env['account.analytic.account.four'].with_user(SUPERUSER_ID).search([('name', 'in', analiticas)])
            if len(retorno) != len(analiticas):
                hasError = True
                if len(retorno) > 0:
                    names = map(lambda analitica: analitica.name, retorno)
                    no_existen = list(set(analiticas)-set(names)) 
                    for ne in no_existen:
                            error+=f"{ne}\n"
                else:            
                    for ne in analiticas:
                            error+=f"{ne}\n"
            
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }           
    def get_etiquetas_analiticas1(self, dataFrame):
        hasError = False
        retorno = None
        error = "Las siguientes etiquetas analíticas 1 no existen y deben ser creadas antes de continuar: \n"
        analiticas = list(self.unique_no_nan(dataFrame["ETIQUETA ANALITICA 1"])) 
        if analiticas is not None and len(analiticas) > 0:
            retorno = self.env['account.analytic.tag'].with_user(SUPERUSER_ID).search([('name', 'in', analiticas)])
            if len(retorno) != len(analiticas):
                hasError = True
                if len(retorno) > 0:
                    names = map(lambda analitica: analitica.name, retorno)
                    no_existen = list(set(analiticas)-set(names)) 
                    for ne in no_existen:
                            error+=f"{ne}\n"
                else:            
                    for ne in analiticas:
                            error+=f"{ne}\n"
            
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }
    def get_etiquetas_analiticas2(self, dataFrame):
        hasError = False
        retorno = None
        error = "Las siguientes etiquetas analíticas 2 no existen y deben ser creadas antes de continuar: \n"
        analiticas = list(self.unique_no_nan(dataFrame["ETIQUETA ANALITICA 2"])) 
        if analiticas is not None and len(analiticas) > 0:
            retorno = self.env['account.analytic.tag.two'].with_user(SUPERUSER_ID).search([('name', 'in', analiticas)])
            if len(retorno) != len(analiticas):
                hasError = True
                if len(retorno) > 0:
                    names = map(lambda analitica: analitica.name, retorno)
                    no_existen = list(set(analiticas)-set(names)) 
                    for ne in no_existen:
                            error+=f"{ne}\n"
                else:            
                    for ne in analiticas:
                            error+=f"{ne}\n"
            
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }    
    def get_etiquetas_analiticas3(self, dataFrame):
        hasError = False
        retorno = None
        error = "Las siguientes etiquetas analíticas 3 no existen y deben ser creadas antes de continuar: \n"
        analiticas = list(self.unique_no_nan(dataFrame["ETIQUETA ANALITICA 3"])) 
        if analiticas is not None and len(analiticas) > 0:
            retorno = self.env['account.analytic.tag.three'].with_user(SUPERUSER_ID).search([('name', 'in', analiticas)])
            if len(retorno) != len(analiticas):
                hasError = True
                if len(retorno) > 0:
                    names = map(lambda analitica: analitica.name, retorno)
                    no_existen = list(set(analiticas)-set(names)) 
                    for ne in no_existen:
                            error+=f"{ne}\n"
                else:            
                    for ne in analiticas:
                            error+=f"{ne}\n"
            
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }      
    def get_etiquetas_analiticas4(self, dataFrame):
        hasError = False
        retorno = None
        error = "Las siguientes etiquetas analíticas 4 no existen y deben ser creadas antes de continuar: \n"
        analiticas = list(self.unique_no_nan(dataFrame["ETIQUETA ANALITICA 4"])) 
        if analiticas is not None and len(analiticas) > 0:
            retorno = self.env['account.analytic.tag.four'].with_user(SUPERUSER_ID).search([('name', 'in', analiticas)])
            if len(retorno) != len(analiticas):
                hasError = True
                if len(retorno) > 0:
                    names = map(lambda analitica: analitica.name, retorno)
                    no_existen = list(set(analiticas)-set(names)) 
                    for ne in no_existen:
                            error+=f"{ne}\n"
                else:            
                    for ne in analiticas:
                            error+=f"{ne}\n"
            
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }         
    def get_productos(self, dataFrame):
        hasError = False
        error = "Los siguientes productos no existen y deben ser creados antes de continuar: \n"
        productos = list(self.unique_no_nan(dataFrame["PRODUCTO"]))
        retorno = self.env['product.product'].with_user(SUPERUSER_ID).search([('name', 'in', productos)])
        if len(productos) == 0:
             error = ""
        if len(retorno) != len(productos):
            hasError = True
            if len(retorno) > 0:
                   names = map(lambda prod: prod.name, retorno)
                   no_existen = list(set(productos)-set(names)) 
                   for ne in no_existen:
                        error+=f"{ne}\n"
            else:            
                   for ne in productos:
                        error+=f"{ne}\n"
            
        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }
    def get_partners(self, dataFrame):
        hasError = False
        error = ""
        partners = list(dataFrame["RUT"].unique())
        retorno = self.env['res.partner'].with_user(SUPERUSER_ID).search([('vat', 'in', partners), ("l10n_cl_sii_taxpayer_type","in", [1,2,3])])
        retorno_sin_duplicados = list(set( map(lambda part:part.vat, retorno)))
        if len(retorno_sin_duplicados) < len(partners):
            error += "Los siguientes contactos no existen y deben ser creados antes de continuar o debe modificar su categoría de impuestos: \n"
            hasError = True
            if len(retorno) > 0:
                    names = map(lambda part:part , retorno_sin_duplicados)
                    no_existen = list(set(partners)-set(names)) 
                    for ne in no_existen:
                        error+=f"RUT: {ne}\n"
            else:            
                    for ne in partners:
                        error+=f"RUT: {ne}\n"
        if len(retorno_sin_duplicados) < len(retorno):
                hasError = True
                error += "Los siguientes contactos se encuentran duplicados ¿Tienen la misma categoría de impuestos?: \n"
                names = list(map(lambda part:part.vat , retorno))
                res = list(set([ele for ele in names 
                    if names.count(ele) > 1])) 
                for ne in res:
                        error+=f"RUT: {ne}\n" 


        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : retorno
        }
    def get_journals(self):
         return self.env['account.journal'].with_user(SUPERUSER_ID).search([])
    def get_journal(self, journals, move_type):
         
         codes = {
              "out_refund" : "INV",
              "out_invoice" : "INV",
              "in_invoice" : "FACTU",
              "in_refund" : "FACTU"
         }

         return journals.filtered(lambda j: j.code == codes[move_type])
    def get_move_type(self, code):
         move_type = 'out_invoice' if code in ['33', '34','39', '56'] and self.tipo_factura == 'ventas' \
                                   else 'out_refund' if code in ['61'] and self.tipo_factura == 'ventas' \
                                   else 'in_invoice' if code in ['33', '34', '71', '56'] and self.tipo_factura == 'compra' \
                                   else 'in_refund' if code in ['61'] and self.tipo_factura == 'compra' else  'in_refund'
         return move_type
    def add_line(self, lines, exento, product, analytic, quantity, price, tax_ids):

        to_append = {
                'product_id': product.id,
                'name': product.name,
                'analytic_account_id': analytic["analytic_account_one_id"].id if (analytic["analytic_account_one_id"] is not None and analytic["analytic_account_one_id"] is not False) else None,
                'analytic_tag_ids':  [(6, 0, analytic["analytic_account_tag_one_id"].ids)] if (analytic["analytic_account_tag_one_id"] is not None and analytic["analytic_account_tag_one_id"] is not False) else None,
                'analytic_account_two_id':  analytic["analytic_account_two_id"].id if (analytic["analytic_account_two_id"] is not None and analytic["analytic_account_two_id"] is not False) else None,
                'analytic_tag_two_ids':  [(6, 0, analytic["analytic_account_tag_two_id"].ids)] if (analytic["analytic_account_tag_two_id"] is not None and analytic["analytic_account_tag_two_id"] is not False) else None,
                'analytic_account_three_id':  analytic["analytic_account_three_id"].id if (analytic["analytic_account_three_id"] is not None and analytic["analytic_account_three_id"] is not False) else None,
                'analytic_tag_three_ids': [(6, 0, analytic["analytic_account_tag_three_id"].ids)] if (analytic["analytic_account_tag_three_id"] is not None and analytic["analytic_account_tag_three_id"] is not False) else None,
                'analytic_account_four_id': analytic["analytic_account_four_id"].id if (analytic["analytic_account_four_id"] is not None and analytic["analytic_account_four_id"] is not False) else None,
                'analytic_tag_four_ids': [(6, 0, analytic["analytic_account_tag_four_id"].ids)] if (analytic["analytic_account_tag_four_id"] is not None and analytic["analytic_account_tag_four_id"] is not False) else None,
                'quantity': quantity,
                'price_unit': price }

        if not exento: 
            to_append["tax_ids"] = [(6, 0, tax_ids.ids)]
        
        lines.append((0, 0, to_append))

        return lines
    def create_invoice(self, partner, id_factura,  lines, type_document, folio, date, move_type, journal, referencias):
        invoice = {
            'partner_id': partner.id,
            'id_factura': id_factura,
            'move_type': move_type,
            'l10n_latam_document_number': folio,
            'l10n_latam_document_type_id': type_document.id,
            'invoice_date': date,
            'invoice_date_due':  date + timedelta(days=4),
            'invoice_line_ids': lines,
            'journal_id': journal.id,
        }

        if referencias is not None:
             invoice["l10n_cl_reference_ids"] = referencias

        _logger.info(f"INVOICE==>{invoice} TIPO==> {type_document.name}")

        return invoice
    def valida_cabeceras(self, dataFrame):
        error = ""
        errorFinal = ""
        if not "ID" in dataFrame.columns:
                error+= f"ID, "
        if not "RUT" in dataFrame.columns:
                error+= f"RUT, "
        if not "Razón social" in dataFrame.columns:
                error+= f"Razón social, "
        if not "Documento" in dataFrame.columns:
                error+= f"Documento,"
        if not "Folio" in dataFrame.columns:
                error+= f"Folio,"                                        
        if not "Exento" in dataFrame.columns:
                error+= f"Exento,"                                        
        if not "PRODUCTO" in dataFrame.columns:
                error+= f"PRODUCTO,"                                        
        if not "ETIQUETA ANALITICA 1" in dataFrame.columns:
                error+= f"ETIQUETA ANALITICA 1,"                                                        
        if not "ETIQUETA ANALITICA 2" in dataFrame.columns:
                error+= f"ETIQUETA ANALITICA 2,"                                        
        if not "ETIQUETA ANALITICA 3" in dataFrame.columns:
                error+= f"ETIQUETA ANALITICA 3,"                                                                        
        if not "ETIQUETA ANALITICA 4" in dataFrame.columns:
                error+= f"ETIQUETA ANALITICA 4,"                                        
        if not "CUENTA ANALITICA 1" in dataFrame.columns:
                error+= f"CUENTA ANALITICA 1,"
        if not "CUENTA ANALITICA 2" in dataFrame.columns:
                error+= f"CUENTA ANALITICA 2,"
        if not "CUENTA ANALITICA 3" in dataFrame.columns:
                error+= f"CUENTA ANALITICA 3,"
        if not "CUENTA ANALITICA 4" in dataFrame.columns:
                error+= f"CUENTA ANALITICA 4,"
        if not "Cantidad" in dataFrame.columns:
                error+= f"Cantidad,"                                                                
        if not "Subtotal" in dataFrame.columns:
                error+= f"Subtotal,"                                                                
        if not "Fecha" in dataFrame.columns:
                error+= f"Fecha,"                         
        if not "Ref. Folio" in dataFrame.columns:
                error+= f"Ref. Folio,"                         
        if not "Ref. Documento" in dataFrame.columns:
                error+= f"Ref. Documento,"                         
        if not "Ref. Razón" in dataFrame.columns:
                error+= f"Ref. Razón,"                         
        if not "Ref. Código" in dataFrame.columns:
                error+= f"Ref. Código,"                                                                                         

        if error != "":
             errorFinal = f"La(s) columna(s) {error[:-1]} No existe(n) en la planilla que desea cargar\n"

        error = ""

        if "ID" in dataFrame.columns and dataFrame["ID"].isna().any():
              error+= f"ID, "
        if "RUT" in dataFrame.columns and dataFrame["RUT"].isna().any():
              error+= f"RUT, "
        if "Documento" in dataFrame.columns and dataFrame["Documento"].isna().any():
              error+= f"Documento, "
        if "Folio" in dataFrame.columns and dataFrame["Folio"].isna().any():
              error+= f"Folio, "                                          
        if "PRODUCTO" in dataFrame.columns and dataFrame["PRODUCTO"].isna().any():
              error+= f"PRODUCTO, "                                                        
        if "Cantidad" in dataFrame.columns and dataFrame["Cantidad"].isna().any():
              error+= f"Cantidad, "                                                                      
        if "Subtotal" in dataFrame.columns and dataFrame["Subtotal"].isna().any():
              error+= f"Subtotal, "                                                        
        if "Fecha" in dataFrame.columns and dataFrame["Fecha"].isna().any():
              error+= f"Fecha, "           
        if error != "":      
            errorFinal += f"La(s) columna(s) {error[:-1]} tienen celdas vacías, estas celdas son obligatorias"
            raise UserError(errorFinal)
    def valida_integridad(self, productos, 
                          etiquetas_analiticas1, etiquetas_analiticas2,etiquetas_analiticas3,etiquetas_analiticas4,
                          cuentas_analiticas1, cuentas_analiticas2, cuentas_analiticas3, cuentas_analiticas4,
                          partners,
                          document_types):
         
        error = "" 
        if productos["hasError"]:
            error = productos["errorMessage"]
        if etiquetas_analiticas1["hasError"]:
            error += etiquetas_analiticas1["errorMessage"]
        if etiquetas_analiticas2["hasError"]:
            error += etiquetas_analiticas2["errorMessage"]            
        if etiquetas_analiticas3["hasError"]:
            error += etiquetas_analiticas3["errorMessage"]
        if etiquetas_analiticas4["hasError"]:
            error += etiquetas_analiticas4["errorMessage"]                        
        if cuentas_analiticas1["hasError"]:
            error += cuentas_analiticas1["errorMessage"]
        if cuentas_analiticas2["hasError"]:
            error += cuentas_analiticas2["errorMessage"]
        if cuentas_analiticas3["hasError"]:
            error += cuentas_analiticas3["errorMessage"]
        if cuentas_analiticas4["hasError"]:
            error += cuentas_analiticas4["errorMessage"]
        if partners["hasError"]:
            error += partners["errorMessage"]            
        if document_types["hasError"]:
            error += document_types["errorMessage"]                        
        if error != "":
             raise UserError(error)
    def get_ivas(self):
        impuestos = self.env['account.tax'].with_user(SUPERUSER_ID).search([('id', 'in', [1,2]), ('l10n_cl_sii_code', '=', 14)])
        return impuestos
    def valida_referencias(self,account_move, dataFrame, partner, document_types):
        hasError = False
        error = f'  Los siguientes documentos referenciados no existen para la {dataFrame["Documento"].values[0]} folio {dataFrame["Folio"].values[0]} para el cliente {partner.name} y deben ser creados para poder procesar\n'
        subDataFrame = dataFrame.groupby(["Ref. Documento","Ref. Folio"])
        lines = []
        for _, row in subDataFrame:
             

             if self.to_str(row["Ref. Documento"].values[0]) in ["801", ["802"]]:
                  continue

             if np.isnan(row["Ref. Folio"].values[0]):
                  hasError = True
                  error+=f'     - La referencia al tipo de documento {tipo.name} para el cliente  {partner.name} no tiene un folio\n'

             if np.isnan(row["Ref. Documento"].values[0]):
                  hasError = True
                  error+=f'     - La referencia al tipo de documento {tipo.name} folio {row["Ref. Folio"].values[0]} para el cliente  {partner.name} no tiene un tipo de documento\n'

             if not hasError:
                ref = account_move.with_user(SUPERUSER_ID).search(
                            [('sequence_number', '=', int(row["Ref. Folio"].values[0])), ('partner_id', '=', partner.id),
                            ('move_type', '=', self.get_move_type(self.to_str(row["Ref. Documento"].values[0])))])

                if ref is not None and len(ref) > 0:

                    
                    
                    to_append = {
                            'origin_doc_number': int(row["Ref. Folio"].values[0]),
                            'l10n_cl_reference_doc_type_selection': self.to_str(row["Ref. Documento"].values[0]),
                            'reason': row["Ref. Razón"].values[0],
                            'date': self.to_datetime(row["Fecha"].values[0]).date(),
                            'reference_doc_code' :   str(int(row["Ref. Código"].values[0]))
                    }

                    lines.append((0, 0, to_append))
                else:
                    hasError = True
                    tipo = document_types.filtered(lambda d: d.code == self.to_str(row["Ref. Documento"].values[0]))
                    error+=f'       - La referencia al tipo de documento {tipo.name} folio {int(row["Ref. Folio"].values[0])} para el cliente  {partner.name} no existe\n'
            
             

        return {
            "hasError" : hasError,
            "errorMessage" : error,
            "retorno" : lines
        }
    def divide_chunks(self, l, n): 
    # looping till length l 
        for i in range(0, len(l), n):  
            yield l[i:i + n]           
    def get_dataFrame(self, mainDataframe, documentsType):
      dataFrame = None
      if documentsType  == "facturas":
          dataFrame = mainDataframe.loc[mainDataframe["ID"].str[1:3].isin(["33","34","39"])]
      elif documentsType  == "ncnd":    
          dataFrame = mainDataframe.loc[mainDataframe["ID"].str[1:3].isin(["56","61"])]

      return dataFrame
    def read_documentos(self, 
                        dataFrame, 
                        productos,  
                        etiquetas_analiticas1,
                        etiquetas_analiticas2,
                        etiquetas_analiticas3,
                        etiquetas_analiticas4,
                        cuentas_analiticas1,
                        cuentas_analiticas2,
                        cuentas_analiticas3,
                        cuentas_analiticas4,
                        partners,
                        document_types,
                        journals,
                        ivas,
                        log,
                        returnLog):
        start = timer()
        documentos = dataFrame.groupby(["Documento","Folio", "RUT"])

        account_move = self.env['account.move']
        invoices = []
        contador = 0
        for _, group in documentos:
                respuesta = None
                #_logger.info("\n-- Group with {} rows(s)".format(len(group)))
                #_logger.info('CREATE TABLE {}('.format(name))
                id_factura = group["ID"].values[0]
                folio  = group["Folio"].values[0]
                partner = partners["retorno"].filtered(lambda p: p.vat == group["RUT"].values[0])
                document_type = document_types["retorno"].filtered(lambda p: p.code == group["ID"].values[0][1:3])
                move_type =  self.get_move_type(document_type.code)
                account = account_move.with_user(SUPERUSER_ID).search(
                        [('sequence_number', '=', folio), ('partner_id', '=', partner.id),
                         ('move_type', '=', move_type)])
                
                #en caso de que sean notas de débito o crédito hacemos algunas comprobaciones extra, sobre referencias
                if document_type.code in ["56", "61"]:
                    respuesta = self.valida_referencias(account_move, group, partner, document_types["retorno"])
                    if respuesta["hasError"]:
                         log+= respuesta["errorMessage"]
                         continue
                    
                     

                if account and len(account) > 0:
                    log += f"   Ya existe un documento con el Folio: {folio} para el cliente {partner.name}\n"
                    continue

                lines_product  = []
                for _, row in group.iterrows():
                    contador +=1 
                    exento = False if row["Exento"] is None or np.isnan(row["Exento"]) or row["Exento"] == 0 or str(row["Exento"]).strip() == "" or str(row["Exento"]).strip() == "0" else True
                    product  = productos["retorno"].filtered(lambda p: p.name == row["PRODUCTO"])
                    analityc = {
                    "analytic_account_tag_one_id" : etiquetas_analiticas1["retorno"].filtered(lambda p: p.name == row["ETIQUETA ANALITICA 1"]) if etiquetas_analiticas1["retorno"] is not None else None,
                    "analytic_account_tag_two_id" : etiquetas_analiticas2["retorno"].filtered(lambda p: p.name == row["ETIQUETA ANALITICA 2"]) if etiquetas_analiticas2["retorno"] is not None else None,
                    "analytic_account_tag_three_id" : etiquetas_analiticas3["retorno"].filtered(lambda p: p.name == row["ETIQUETA ANALITICA 3"]) if etiquetas_analiticas3["retorno"] is not None else None,
                    "analytic_account_tag_four_id" : etiquetas_analiticas4["retorno"].filtered(lambda p: p.name == row["ETIQUETA ANALITICA 4"]) if etiquetas_analiticas4["retorno"] is not None else None,
                    "analytic_account_one_id" : cuentas_analiticas1["retorno"].filtered(lambda p: p.name == row["CUENTA ANALITICA 1"]) if cuentas_analiticas1["retorno"] is not None else None,
                    "analytic_account_two_id" : cuentas_analiticas2["retorno"].filtered(lambda p: p.name == row["CUENTA ANALITICA 2"]) if cuentas_analiticas2["retorno"] is not None else None,
                    "analytic_account_three_id" : cuentas_analiticas3["retorno"].filtered(lambda p: p.name == row["CUENTA ANALITICA 3"]) if cuentas_analiticas3["retorno"] is not None else None,
                    "analytic_account_four_id" : cuentas_analiticas4["retorno"].filtered(lambda p: p.name == row["CUENTA ANALITICA 4"]) if cuentas_analiticas4["retorno"] is not None else None
                    }

                    
                    cantidad = int(row["Cantidad"])
                    precio = int(row["Subtotal"]) / cantidad
                    impuesto = self.get_impuesto(ivas, move_type)
                    journal = self.get_journal(journals, move_type)

                    if int(row["ID"][1:3]) == 39:
                         precio = math.ceil(precio / ((impuesto.amount / 100) + 1))
                    folio = row["Folio"]

                    lines_product = self.add_line(lines_product, exento, product,  analityc ,cantidad,precio, impuesto)

                if len(lines_product) > 0:
                    invoices.append(self.create_invoice(partner,id_factura, lines_product,document_type, folio, self.to_datetime(row["Fecha"]).date(), move_type,journal, (respuesta["retorno"] if respuesta is not None else None) ))
        creados = 0
        for chunk in self.divide_chunks(invoices, 20):
            account_move.with_user(SUPERUSER_ID).create(chunk)
            creados+=20 
            _logger.info(f"{creados} CREADOS de {len(invoices)}")
        end = timer()
        _logger.info(f"TIEMPO==> {(end - start)}")
        if returnLog:
            return log
        else:
            return self.descarga_log(log)
        
    def descarga_log(self, log):
        with tempfile.TemporaryDirectory() as temp_dir:
            with open(f'{temp_dir}/temp.file', 'w') as f:
                f.write(log)
    
            data = open(f'{temp_dir}/temp.file').read()
            data = base64.b64encode(data.encode("utf-8"))    
        fecha = datetime.now().strftime("%Y%m%d_%H%M")
        attach_vals = {
                    'name': f'log_carga_{fecha}.txt',
                    'type': 'binary',
                    'datas':data,
                    'res_id': self.id,
                    'mimetype': 'text/plain'
        }
        doc_id = self.env['ir.attachment'].with_user(SUPERUSER_ID).create(attach_vals)
        return {
                    'type': 'ir.actions.act_url',
                    'url': '/web/content?model=ir.attachment&field=datas&id=%s&filename=%s&download=true' % (doc_id.id, doc_id.name),
        }


class WizardImportCsv(models.TransientModel):
    _name = 'wizard.import.csv.nc'
    _description = 'wizard import csv nc'

    load_csv = fields.Binary(string="Load csv")
    

    def action_csv_nc(self):
        keys = ["ID", "Documento", "Folio", "Fecha", "RUT", "Razón social", "Exento", "Neto", "IVA", "Total CLP",
                "Nacionalidad", "Moneda", "Total moneda", "Sucursal", "Usuario", "Fecha y hora timbre", "Intercambio", 
                "Evento receptor", "Cedido", "Vendedor", "Ind Traslado", "Cód. Interno", "Ref. Fecha", "Ref. Documento", 
                "Ref. Folio", "Ref. Código", "Ref. Razón", "Observación", "Vencimiento"]
        csv_data = base64.b64decode(self.load_csv)
        data_file = io.StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        list_csv = []
        csv_reader = csv.reader(data_file, delimiter=';')
        list_csv.extend(csv_reader)
        values = {}
        current_nc = None
        current_f = None
        for i in range(len(list_csv)):
            field = list(map(str, list_csv[i]))
            values = dict(zip(keys, field))
            if i == 0:
                continue
            else:
                 try:
                    current_nc = self.env["account.move"].search([("partner_id.vat", "=" , values.get("RUT")), ("move_type", "=" , "out_refund"), ("state" , "=", "posted"), ("payment_state" , "=", "not_paid"), ("sequence_number", "=", int(values.get("Folio")))], limit=1) 
                    current_f = self.env["account.move.line"].search([("move_id.partner_id.vat", "=" , values.get("RUT")), ("move_id.move_type", "=" , "out_invoice"), ("move_id.state" , "=", "posted"), ("move_id.payment_state" , "=", "not_paid"), ("move_id.sequence_number", "=", int(values.get("Ref. Folio"))), ("account_id", "=", 5), ("reconciled", "=", False)], limit=1) 
                    if (current_nc is not None and current_nc.id) and (current_f is not None and current_f.id):
                        current_nc.js_assign_outstanding_line(current_f.id)
                 except Exception as e: print(e)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }