# -*- coding: utf-8 -*-
# Developed By Hector M. Chavez Cortez, Angelica Langarica Escobedo, Kevin Basilio Moreno

{
    'name': "Calculate Price",
    'summary': "Calculate Price in E-commerce",
    'description': "Make page in products to configure and calculate the sale price in E-commerce",
    'author': "Lucion",
    'website': "http://lucion.mx",
    'category': 'Tools',
    'version': '1.0',
    'depends': ['theme_prime','sale_mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/templates.xml',
        'views/sale_order_view.xml',
        'views/account_move_view.xml',
        'views/mrp_production_view.xml',
        'report/sale_order_report.xml',
    ],
    'application': True,
    'installable':True,
}
