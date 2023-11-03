# -*- coding: utf-8 -*-
# Developed By Hector M. Chavez Cortez, Angelica Langarica Escobedo, Kevin Basilio Moreno

from flectra.addons.website_sale.controllers.main import WebsiteSale
from flectra.addons.website_sale.controllers.variant import WebsiteSaleVariantController
from flectra.http import request
from flectra import _, http
from flectra.addons.website.controllers.main import QueryURL
import json
import math
import logging

_logger = logging.getLogger(__name__)
class WebsiteSalePrices(WebsiteSale):

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        width_c = float(kw.get('width_c'))
        height_c = float(kw.get('height_c'))

        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            width_c=width_c,
            height_c=height_c,
        )
        if kw.get('express'):
            return request.redirect("/shop/checkout?express=1")

        return request.redirect("/shop/cart")

    def _prepare_product_values(self, product, category, search, **kwargs):
        add_qty = int(kwargs.get('add_qty', 1))

        product_context = dict(request.env.context, quantity=add_qty, active_id=product.id, partner=request.env.user.partner_id)
        ProductCategory = request.env['product.public.category']

        if category:
            category = ProductCategory.browse(int(category)).exists()

        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attrib_set = {v[1] for v in attrib_values}

        keep = QueryURL('/shop', category=category and category.id, search=search, attrib=attrib_list)

        categs = ProductCategory.search([('parent_id', '=', False)])

        pricelist = request.website.get_current_pricelist()

        if not product_context.get('pricelist'):
            product_context['pricelist'] = pricelist.id
            product = product.with_context(product_context)

        # Needed to trigger the recently viewed product rpc
        view_track = request.website.viewref("website_sale.product").track
        return {
            'search': search,
            'category': category,
            'pricelist': pricelist,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'keep': keep,
            'categories': categs,
            'main_object': product,
            'product': product,
            'add_qty': add_qty,
            'view_track': view_track,
        }

class CalculatePriceVariantController(WebsiteSaleVariantController):

    @http.route(['/products/calculate_price'], type="json", methods=['POST'], auth="public", website=True,  csrf_token=False,)
    def calculate_prices(self, **kw):
        if kw:
            product_id = int(kw.get('product_id'))
            width = float(kw.get('width')) or 0
            height = float(kw.get('height')) or 0
            cube_qty = request.env['product.product'].set_prices_tab(width, height, product_id) or 1
            return cube_qty
        return 1
    
    @http.route(['/sale/get_combination_info_website'], type='json', auth="public", methods=['POST'], website=True)
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):
        kw.pop('pricelist_id')

        width_c = float(kw.get('width_c')) if kw.get('width_c') not in ['',False,None] else 1
        height_c = float(kw.get('height_c')) if kw.get('height_c') not in ['',False,None] else 1

        res = self.get_combination_info(product_template_id, product_id, combination, add_qty, request.website.get_current_pricelist(), **kw)
        configurable = request.env['product.product'].browse(res['product_id'])
        cube_qty = request.env['product.product'].set_prices_tab(width_c, height_c, res['product_id'])
        carousel_view = request.env['ir.ui.view']._render_template('website_sale.shop_product_carousel',
            values={
                'product': request.env['product.template'].browse(res['product_template_id']),
                'product_variant': request.env['product.product'].browse(res['product_id']),
            })
        res['carousel'] = carousel_view
        res['price'] = float(res['price']) * add_qty # * float(cube_qty) 
        res['list_price'] = float(res['list_price']) * add_qty # * float(cube_qty)
        res['price_extra'] = float(res['price_extra']) * float(add_qty) # * float(cube_qty)
        res['is_variant_configurable'] = configurable.is_configurable or False
        res['type_configuration'] = configurable.configurations or 'normal'
        res['min_width'] = configurable.min_width
        res['min_height'] = configurable.min_height
        res['width'] = configurable.width
        res['height'] = configurable.height
        res['cube_qty'] = math.ceil(cube_qty)
        res['configurable_price'] = res['price'] * math.ceil(cube_qty)
        if width_c <= 0 or height_c <= 0:
            res['change_combination'] = True
        else:
            res['change_combination'] = False
        return res
