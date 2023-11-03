# -*- coding: utf-8 -*-
# Developed By Hector M. Chavez Cortez, Angelica Langarica Escobedo, Kevin Basilio Moreno

from flectra import models, fields, api, _
import logging
import math

_logger = logging.getLogger(__name__)
class CalculateProductPrice(models.Model):
    _inherit = 'product.product'

    is_configurable = fields.Boolean(string="Establecer medidas de precio")
    tabular_id = fields.One2many('tabular.prices', 'product_id', string="Tabulador")
    width = fields.Float(string="Ancho (CM)")
    height = fields.Float(string="Altura (CM)")
    min_width = fields.Float(string="Ancho Minimo (CM)")
    min_height = fields.Float(string="Altura Minima (CM)")
    configurations = fields.Selection([('is_vinil', 'Configuracion Viniles'),('is_lona','Configuracion Lonas')], string="Configuracion")

    def set_prices_tab(self, width, height, product_id):
        product = self.browse(int(product_id))
        width = float(width)
        height = float(height)
        min_width = product.min_width
        min_height = product.min_height
        count_w = 1
        count_h = 1
        if product.is_configurable:
            if product.configurations == 'is_vinil':    
                while width > min_width:
                    count_w += 1
                    min_width += product.min_width
                    if width > 240:
                        return False

                while height > min_height:
                    count_h += 1
                    min_height += product.min_height
                    if height > 120:
                        return False

                return (count_w * count_h) or 1
            if product.configurations == 'is_lona':
                short_width = (width / 100)
                short_height = (height / 100)
                valor_decimal_w, valor_entero_w = math.modf(short_width)
                valor_decimal_h, valor_entero_h = math.modf(short_height)
                oper_w = short_width
                oper_h = short_height
                if (valor_decimal_w <= 0.5 and valor_decimal_w > 0)and valor_entero_w >= 1:
                    oper_w = valor_entero_w + 0.5
                if (valor_decimal_h <= 0.5 and valor_decimal_h > 0) and valor_entero_h >= 1:
                    oper_h = valor_entero_h + .5
                if valor_decimal_w > 0.5:
                    oper_w = math.ceil(valor_decimal_w) + valor_entero_w
                if valor_decimal_h > 0.5:
                    oper_h = math.ceil(valor_decimal_h) + valor_entero_h
                if valor_decimal_w == .5 and valor_entero_w < 1:
                    oper_w = math.ceil(valor_decimal_w)
                if valor_decimal_h == .5 and valor_entero_h < 1:
                    oper_h = math.ceil(valor_decimal_h)
                return math.ceil(oper_w * oper_h)
            else:
                return 1
        else:
            return 1
    
    # def just_price(self, product_id):
    #     product_obj = self.search([('id', '=', product_id)])
    #     return product_obj.get_prices()
    
    def type_config(self, product_id):
        product_obj = self.search([('id', '=', product_id)])
        if not product_obj.is_configurable:
            return 'normal'
        else:
            return product_obj.configurations

    def _is_add_to_cart_allowed(self):
        self.ensure_one()
        return self.user_has_groups('base.group_system') or (self.active and self.sale_ok and self.website_published)

    # def get_prices(self, partner=None):
    #     if self.env.context.get('website_id'):
    #         actual_website = self.env['website'].get_current_website()
    #         pricelist = actual_website.get_current_pricelist()
    #         order_id = actual_website.sale_get_order()
    #         prod_price = self.with_context(pricelist=pricelist.id).price
    #         return round(prod_price, 2)
    #     else:
    #         _logger.info(f"Price Out ")
    #         if partner:
    #             pricelist = partner.property_product_pricelist
    #             prod_price = self.with_context(pricelist=pricelist.id).price
    #         else:
    #             prod_price = self.lst_price
    #         return round(prod_price, 2)

class ProductTemplatePrice(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False, width_c=1, height_c=1):
        res = super()._get_combination_info(combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist, parent_combination=parent_combination, only_template=only_template)
        res_product_id = res['product_id']
        configurable = self.env['product.product'].browse(res_product_id)
        if configurable:
            cube_qty = self.env['product.product'].set_prices_tab(width_c, height_c, res['product_id'])
            res['configurable_price'] = res['price'] * math.ceil(cube_qty)
            res['is_variant_configurable'] = configurable.is_configurable or False
            res['type_configuration'] = configurable.configurations or 'normal'
            res['min_width'] = configurable.min_width
            res['min_height'] = configurable.min_height
            res['width'] = configurable.width
            res['height'] = configurable.height
            res['cube_qty'] = math.ceil(cube_qty)
        return res

class TabularPrices(models.Model):
    _name = 'tabular.prices'
    _description = 'Prices Tabular'

    product_id = fields.Many2one('product.product', string="Producto")
    width = fields.Float(string="Ancho (CM)", required=True)
    height = fields.Float(string="Altura (CM)", required=True)
    price = fields.Float(string="Precio")
    currency_id = fields.Many2one('res.currency', string="Moneda", related='product_id.currency_id')

