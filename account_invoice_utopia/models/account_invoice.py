# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import re
from datetime import datetime, date, time, timedelta
from openerp.exceptions import ValidationError, except_orm, RedirectWarning


class account_invoice(models.Model):
    _inherit = "account.invoice"

    x_con_iva = fields.Monetary(string="Con IVA", compute="_get_total", store=True)

    @api.one
    @api.depends('amount_untaxed', 'tax_line_ids.amount', 'tax_line_ids.x_base')
    def _get_total(self):
        con_iva = 0
        valor_iva = 0
        for line in self.tax_line_ids:
            if line.tax_id.x_tipo_impuesto == 'imp':
                con_iva += line.x_base
                valor_iva += line.amount
        self.x_valor_iva = valor_iva
        self.x_con_iva = con_iva
        self.x_total = self.amount_untaxed + valor_iva