# -*- coding: utf-8 -*-
# Developed By Hector M. Chavez Cortez, Angelica Langarica Escobedo, Kevin Basilio Moreno

from flectra import models, fields, api, _

class AccountMoveLineCalculate(models.Model):
    _inherit = 'account.move.line'

    width_measure = fields.Float(string="Ancho (CM)")
    height_measure = fields.Float(string="Largo (CM)")
    
    