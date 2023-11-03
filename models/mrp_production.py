# -*- coding: utf-8 -*-
# Developed By Hector M. Chavez Cortez, Angelica Langarica Escobedo, Kevin Basilio Moreno

from flectra import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)
class MrpProductionPrice(models.Model):
    _inherit = 'mrp.production'

    width_measure = fields.Float(string="Ancho (CM)", compute="_compute_measures")
    height_measure = fields.Float(string="Largo (CM)", compute="_compute_measures")

    @api.depends('origin')
    def _compute_measures(self):
        for line in self:
            if line.origin and line.state in ['draft']:
                order_sale = self.env['sale.order'].sudo().search([('name', '=', line.origin)])
                if order_sale:
                    lines = order_sale.order_line.filtered(lambda x: x.product_id == line.product_id)
                    line.width_measure = lines[0].width_measure if lines else 0
                    line.height_measure = lines[0].height_measure if lines else 0
                    for bom_line in line.move_raw_ids:
                        bom_line.write({'product_uom_qty': (bom_line.product_uom_qty * lines[0].cubes_quantity)})
                    _logger.info(f"----------{bom_line}--si entra-----------------------------")
                else:
                    line.width_measure = 0
                    line.height_measure =  0
                _logger.info(f"-------------------------{order_sale}---------------------------------------")
            else:
                line.width_measure = 0
                line.height_measure =  0
        