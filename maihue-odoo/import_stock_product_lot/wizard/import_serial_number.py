from odoo import api, fields, models
from odoo.exceptions import ValidationError
import tempfile
import binascii
import logging
import xlrd

_logger = logging.getLogger(__name__)

class ImportSerialNumber(models.TransientModel):
    _name = 'import.serial.number'

    @api.model
    def default_get(self, default_fields):
        res = super(ImportSerialNumber, self).default_get(default_fields)
        active_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
        lines = []
        for line in active_id.move_ids_without_package:
            lines.append(line.id)
        res['picking_id'] = active_id
        res['stock_move_ids'] = lines
        return res

    file = fields.Binary('Archivo')
    picking_id = fields.Many2one('stock.picking', sring='Picking')
    stock_move_ids = fields.Many2many('stock.move', sring='Lineas Operaciones')
    import_serial_line_ids = fields.One2many('import.serial.number.line', 'serial_number_id', sring='Lineas Importadas')
    great_than_demand = fields.Boolean('Mas que la demanda', compute='_compute_quantiry_vs_demand')
    low_than_demand = fields.Boolean('Menos que la demanda', compute='_compute_quantiry_vs_demand')
    message = fields.Char(string='Message', compute='_compute_quantiry_vs_demand')

    @api.depends('file')
    def _compute_quantiry_vs_demand(self):
        for rec in self:
            msg = ''
            great_than_demand = False
            low_than_demand = False
            if rec.import_serial_line_ids:
                for line in rec.import_serial_line_ids:
                    if line.product_uom_qty < line.quantity_file:
                        great_than_demand = True
                        msg += 'En el producto %s se han cargado mas numeros de serie que los solicitados (Demanda: %s, Contados: %s). ' % (line.product_id.display_name, line.product_uom_qty, line.quantity_file)
                    if line.product_uom_qty > line.quantity_file:
                        low_than_demand = True
                        msg += 'En el producto %s se han cargado menos numeros de serie que los solicitados (Demanda: %s, Contados: %s). ' % (line.product_id.display_name, line.product_uom_qty, line.quantity_file)
            rec.great_than_demand = great_than_demand
            rec.low_than_demand = low_than_demand
            rec.message = msg



    def group_by_product_file(self, lines):
        ProductProdcut = self.env['product.product']
        stock_moves = self.env['stock.move'].browse(self.stock_move_ids.ids)
        new_vals = True
        lines_grouped = []
        vals = {}
        contador = 1
        for line in lines:
            contador += 1
            product = ProductProdcut.search([('name', '=', line['Producto'])])
            if not product:
                product = ProductProdcut.search([('default_code', '=', line['Producto'])])
                if not product:
                    raise ValidationError(f"EL codigo del producto {line['Producto']} de la linea {contador} no se encuentra")
            if lines_grouped:
                for lg in lines_grouped:
                    if lg['product_id'] == product.id:
                        lg['quantity_file'] += 1
                        new_vals = False
                        break
                    else:
                        new_vals = True
            quantity_sm = sum(sm.product_uom_qty for sm in stock_moves.filtered(lambda s: s.product_id.id == product.id))
            if new_vals:
                lines_grouped.append({
                    'product_id': product.id,
                    'product_uom_qty': quantity_sm,
                    'quantity_file': 1
                })
        return lines_grouped

    @api.onchange('file')
    def onchange_import_serial_line_import(self):
        if self.file:
            # ImportSerialNumberLine = self.env['import.serial.number.line']
            fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            products_file_vals = []
            file_lines = []
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
            values_header = [sheet.cell_value(0, i) for i in range(sheet.ncols)]

            for row_no in range(1, sheet.nrows):
                line = {}
                for col in range(sheet.ncols):
                    line[values_header[col]] = sheet.cell_value(row_no, col)
                file_lines.append(line)
            products_file = self.group_by_product_file(file_lines)
            for pf in products_file:
                products_file_vals.append((0, 0, pf))
            self.import_serial_line_ids = products_file_vals




    def import_file(self):
        StockMoveLine = self.env['stock.move.line']
        ProductProdcut = self.env['product.product']
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.file))
        fp.seek(0)
        values = []
        vals_validator = {}
        for line in self.stock_move_ids:
            vals_validator.update({
                line.product_id.id: {
                    'id': line.id,
                    'location_id': line.location_id.id,
                    'location_dest_id': line.location_dest_id.id,
                    'qty': line.product_uom_qty,
                    'qty_done': line.quantity_done if line.quantity_done > 0 else 0,
                    'state': 'Pending'

                }
            })
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)
        values_header = [sheet.cell_value(0, i) for i in range(sheet.ncols)]
        contador = 1
        for row_no in range(1, sheet.nrows):
            contador += 1
            line = {}
            for col in range(sheet.ncols):
                line[values_header[col]] = sheet.cell_value(row_no, col)
            sku = line['Producto']
            if isinstance(line['Producto'], float):
                sku = str(line['Producto']).split('.')[0] if '.' in str(line['Producto']) else str(line['Producto'])
            product = ProductProdcut.search([('default_code', '=', sku)])
            if not product:
                raise ValidationError(f"No existe un producto con SKU {line['Producto']} - linea del archivo {contador}")
            sm = vals_validator[product.id]
            active_id = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_id'))
            if sm['qty_done'] < sm['qty']:
                vals = {
                    'picking_id': active_id.id,
                    'move_id': sm['id'],
                    'product_id': product.id,
                    'location_id': sm['location_id'],
                    'location_dest_id': sm['location_dest_id'],
                    'lot_name': line['Serie'],
                    'qty_done': 1,
                    'product_uom_id': product.uom_id.id
                }
                sml = StockMoveLine.create(vals)
                if sml:
                    qty_done = sm['qty_done']
                    sm.update({'qty_done': qty_done + 1})
        return True

class ImportSerialNumberLine(models.TransientModel):
    _name = 'import.serial.number.line'

    serial_number_id = fields.Many2one('import.serial.number', 'Serial Number')
    product_id = fields.Many2one('product.product', 'Producto')
    product_uom_qty = fields.Float('Demanda')
    quantity_file = fields.Float('Cantidad archivo')