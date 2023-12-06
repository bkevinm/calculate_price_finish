# -*- coding: utf-8 -*-
# Developed By Hector M. Chavez Cortez, Angelica Langarica Escobedo, Kevin Basilio Moreno

from flectra import models, fields, api, _
from flectra.http import request
from flectra.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)
class SaleOrderCalculate(models.Model):
    _inherit = 'sale.order'

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, width_c=0, height_c=0, **kwargs):
        self.ensure_one()
        product_context = dict(self.env.context)
        product_context.setdefault('lang', self.sudo().partner_id.lang)
        SaleOrderLineSudo = self.env['sale.order.line'].sudo().with_context(product_context)
        product_with_context = self.env['product.product'].with_context(product_context)
        product = product_with_context.browse(int(product_id)).exists()
        cube_qty = request.env['product.product'].set_prices_tab(width_c, height_c, product_id)

        if not product or (not line_id and not product._is_add_to_cart_allowed()):
            raise UserError(_("The given product does not exist therefore it cannot be added to cart."))

        try:
            if add_qty:
                add_qty = int(add_qty)
        except ValueError:
            add_qty = 1
        try:
            if set_qty:
                set_qty = int(set_qty)
        except ValueError:
            set_qty = 0
        quantity = 0
        order_line = False
        if self.state != 'draft':
            request.session['sale_order_id'] = None
            raise UserError(_('It is forbidden to modify a sales order which is not in draft status.'))
        if line_id is not False:
            order_line = self._cart_find_product_line(product_id, line_id, **kwargs)[:1]

        # Create line if no line with product_id can be located
        if not order_line:
            no_variant_attribute_values = kwargs.get('no_variant_attribute_values') or []
            received_no_variant_values = product.env['product.template.attribute.value'].browse([int(ptav['value']) for ptav in no_variant_attribute_values])
            received_combination = product.product_template_attribute_value_ids | received_no_variant_values
            product_template = product.product_tmpl_id

            combination = product_template._get_closest_possible_combination(received_combination)

            product = product_template._create_product_variant(combination)

            if not product:
                raise UserError(_("The given combination does not exist therefore it cannot be added to cart."))

            product_id = product.id

            values = self._website_product_id_change(self.id, product_id, qty=1)

            for ptav in combination.filtered(lambda ptav: ptav.attribute_id.create_variant == 'no_variant' and ptav not in received_no_variant_values):
                no_variant_attribute_values.append({
                    'value': ptav.id,
                })

            if no_variant_attribute_values:
                values['product_no_variant_attribute_value_ids'] = [
                    (6, 0, [int(attribute['value']) for attribute in no_variant_attribute_values])
                ]

            custom_values = kwargs.get('product_custom_attribute_values') or []
            received_custom_values = product.env['product.template.attribute.value'].browse([int(ptav['custom_product_template_attribute_value_id']) for ptav in custom_values])

            for ptav in combination.filtered(lambda ptav: ptav.is_custom and ptav not in received_custom_values):
                custom_values.append({
                    'custom_product_template_attribute_value_id': ptav.id,
                    'custom_value': '',
                })

            if custom_values:
                values['product_custom_attribute_value_ids'] = [(0, 0, {
                    'custom_product_template_attribute_value_id': custom_value['custom_product_template_attribute_value_id'],
                    'custom_value': custom_value['custom_value']
                }) for custom_value in custom_values]
            
            values['width_measure'] = width_c
            values['height_measure'] = height_c
            values['cubes_quantity'] = cube_qty

            order_line = SaleOrderLineSudo.create(values)

            try:
                order_line._compute_tax_id()
            except ValidationError as e:
                _logger.debug("ValidationError occurs during tax compute. %s" % (e))
            if add_qty:
                add_qty -= 1

        if set_qty:
            quantity = set_qty
        elif add_qty is not None:
            quantity = order_line.product_uom_qty + (add_qty or 0)

        if quantity <= 0:
            linked_line = order_line.linked_line_id
            order_line.unlink()
            if linked_line:
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
        else:
            no_variant_attributes_price_extra = [ptav.price_extra for ptav in order_line.product_no_variant_attribute_value_ids]
            values = self.with_context(no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra))._website_product_id_change(self.id, product_id, qty=quantity)
            order = self.sudo().browse(self.id)
            if self.pricelist_id.discount_policy == 'with_discount' and not self.env.context.get('fixed_price'):
                product_context.update({
                    'partner': order.partner_id,
                    'quantity': quantity,
                    'date': order.date_order,
                    'pricelist': order.pricelist_id.id,
                })
            product_with_context = self.env['product.product'].with_context(product_context).with_company(order.company_id.id)
            product = product_with_context.browse(product_id)
            
            if set_qty <= 0 and ((order_line.width_measure != float(width_c) and float(width_c) > 0) or (order_line.height_measure != float(height_c) and float(height_c) > 0)):
                values['width_measure'] = width_c
                values['height_measure'] = height_c
                values['product_uom_qty'] = add_qty
                values['cubes_quantity'] = cube_qty
                order_line = SaleOrderLineSudo.create(values)
            else:
                order_line.write(values)

            if kwargs.get('linked_line_id'):
                linked_line = SaleOrderLineSudo.browse(kwargs['linked_line_id'])
                order_line.write({
                    'linked_line_id': linked_line.id,
                })
                linked_product = product_with_context.browse(linked_line.product_id.id)
                linked_line.name = linked_line.get_sale_order_line_multiline_description_sale(linked_product)
            
            order_line.name = order_line.get_sale_order_line_multiline_description_sale(product)
        option_lines = self.order_line.filtered(lambda l: l.linked_line_id.id == order_line.id)
        return {'line_id': order_line.id, 'quantity': quantity, 'option_ids': list(set(option_lines.ids))}

    def action_confirm(self):
        res = super().action_confirm()
        procurement_groups = self.env['procurement.group'].search([('sale_id', 'in', self.ids)])
        mrp_production_ids = procurement_groups.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids | procurement_groups.mrp_production_ids
        mrp_production_ids = mrp_production_ids.filtered(lambda x: x.state in ['draft','confirmed','progress'])
        for sale in self:
            for line in sale.order_line:
                actual_mrp = mrp_production_ids.filtered(lambda x: x.product_id == line.product_id)
                if actual_mrp:
                    for mrp in actual_mrp:
                        for bom_line in mrp.move_raw_ids:
                            bom_line.write({'product_uom_qty': (bom_line.product_uom_qty * line.cubes_quantity)})
        return res

    def is_configurable(self):
        res =  self.order_line.filtered(lambda x: x.product_id.is_configurable)
        if res:
            return True
        return False
     

class SaleLinesCalculate(models.Model):
    _inherit = 'sale.order.line'

    width_measure = fields.Float(string="Ancho (CM)")
    height_measure = fields.Float(string="Largo (CM)")
    cubes_quantity = fields.Float(string="Cant. Material")

    @api.onchange('width_measure', 'height_measure')
    def _change_cubes(self):
        if self.product_id.is_configurable:
            self.width_measure = 0 if self.width_measure <= 0 else self.width_measure
            self.height_measure = 0 if self.height_measure <= 0 else self.height_measure
            cubes = self.product_id.set_prices_tab(self.width_measure, self.height_measure, self.product_id.id) or 1
            self.cubes_quantity = cubes

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'width_measure', 'height_measure')
    def _compute_amount(self):
        for line in self:
            cubes = line.product_id.set_prices_tab(line.width_measure, line.height_measure, line.product_id.id) or 1
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id, width_c = line.width_measure, height_c = line.height_measure, product_id=line.product_id.id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'cubes_quantity': cubes,
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'width_measure': self.width_measure,
            'height_measure': self.height_measure,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id if not self.display_type else False,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res
