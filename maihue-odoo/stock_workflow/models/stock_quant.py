from odoo import _, api, fields, models
from odoo.osv import expression

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # @api.model
    # def default_get(self, fields):
    #     res = super(ResPartner, self).default_get(fields)
    #     quant_lot_ids = self.search([])
    #     return res

    @api.onchange('location_id', 'product_id', 'lot_id', 'package_id', 'owner_id')
    def _onchange_location_or_product_id(self):
        res = super(StockQuant, self)._onchange_location_or_product_id()
        self.lot_domain = False
        lots = []
        if self.product_id:
            quant_lot_ids = self.search([('product_id', '=', self.product_id.id),('id', '!=', self._origin.id),('location_id.usage', 'in', ['internal', 'transit'])])
            if quant_lot_ids:
                for qlot in quant_lot_ids:
                    if qlot.lot_id.id != self.lot_id.id:
                        lots.append(qlot.lot_id.id)
        self.lot_domain = lots
        return res

    validate = fields.Boolean(string='Validado', default=False)
    view_validate = fields.Char(compute='_compute_view_validate', string='View check validate')
    lot_domain = fields.Many2many('stock.production.lot', string='Domain Lot')
    customer_id = fields.Many2one('res.partner', string='Cliente (Propietario)')
    franchisee_id = fields.Many2one('res.users', string='Franquiciado a')

    @api.onchange('validate')
    def _onchange_validate(self):
        self.lot_domain = False
        lots = []
        if self.product_id:
            quant_lot_ids = self.search([('product_id', '=', self.product_id.id),('id', '!=', self._origin.id),('location_id.usage', 'in', ['internal', 'transit'])])
            if quant_lot_ids:
                for qlot in quant_lot_ids:
                    if qlot.lot_id.id != self.lot_id.id:
                        lots.append(qlot.lot_id.id)
        self.lot_domain = lots

    def action_set_inventory_quantity(self):
        self._onchange_location_or_product_id()
        return super(StockQuant, self).action_set_inventory_quantity()

    def _compute_view_validate(self):
        for record in self:
            record.view_validate = False
            if record.env.user.has_group('stock_workflow.validate_number_lot_group'):
                record.view_validate = True

    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`.
        """
        fields = ['inventory_quantity', 'inventory_quantity_auto_apply', 'inventory_diff_quantity',
                  'inventory_date', 'user_id', 'inventory_quantity_set', 'is_outdated', 'validate', 'view_validate', 'accounting_date', 'lot_id', 'lot_domain',
                  'customer_id', 'franchisee_id']
        return fields

    def name_get(self):
        res = []
        name = ''
        for quant in self:
            if quant.lot_id:
                name = '[' + quant.lot_id.name + ']'
            name += quant.product_id.name + '(' + quant.location_id.display_name + ')'
            res.append([quant.id, name])
        return res

    def _select_quant_check_rules(self, quants):
        params = self.env.context.get('params', False)
        picking = None
        quant_selected = self.env['stock.quant']
        if params:
            if params['model'] == 'stock.picking':
                picking = self.env[params['model']].browse([params['id']])
            if picking.picking_type_code in ['internal']:
                location_dest_id = picking.location_dest_id
                stages_allowed = location_dest_id.stage_ids if location_dest_id.stage_ids else location_dest_id.warehouse_id.stage_ids if location_dest_id.warehouse_id.stage_ids else False
                if stages_allowed:
                    for quant in quants:
                        if quant.lot_id:
                            if quant.lot_id.stage_id.id in stages_allowed.ids:
                                quant_selected = quant
            else:
                quant_selected.quants
        return quant_selected

    # def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False):
    #     removal_strategy = self._get_removal_strategy(product_id, location_id)
    #     removal_strategy_order = self._get_removal_strategy_order(removal_strategy)
    #
    #     domain = [('product_id', '=', product_id.id)]
    #     if not strict:
    #         if lot_id:
    #             domain = expression.AND([['|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False)], domain])
    #         if package_id:
    #             domain = expression.AND([[('package_id', '=', package_id.id)], domain])
    #         if owner_id:
    #             domain = expression.AND([[('owner_id', '=', owner_id.id)], domain])
    #         domain = expression.AND([[('location_id', 'child_of', location_id.id)], domain])
    #     else:
    #         domain = expression.AND([['|', ('lot_id', '=', lot_id.id), ('lot_id', '=', False)] if lot_id else [('lot_id', '=', False)], domain])
    #         domain = expression.AND([[('package_id', '=', package_id and package_id.id or False)], domain])
    #         domain = expression.AND([[('owner_id', '=', owner_id and owner_id.id or False)], domain])
    #         domain = expression.AND([[('location_id', '=', location_id.id)], domain])
    #     quants = self.search(domain, order=removal_strategy_order).sorted(lambda q: not q.lot_id)
    #     res_quants = self._select_quant_check_rules(quants)
    #     return res_quants
