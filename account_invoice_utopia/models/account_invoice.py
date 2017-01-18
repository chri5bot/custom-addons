# -*- coding: utf-8 -*-
import pytz
from openerp import models, fields, api
from openerp.tools.translate import _
from datetime import datetime
from openerp.exceptions import except_orm


class account_invoice(models.Model):
    _inherit = "account.invoice"

    start_time = fields.Datetime(string='Hora Inicio', required=True, default=lambda self: self._get_current_time())
    end_time = fields.Datetime(string='Hora Fin', required=True, default=lambda self: self._get_current_time())

    date_invoice = fields.Date(string='Invoice Date', default=lambda self: self._get_current_date(),
                               readonly=True, states={'draft': [('readonly', False)]}, index=True,
                               help="Keep empty to use the current date", copy=False, required=True)
    room_number = fields.Integer(string='Número de habitacion', required=True, )

    @api.model
    def _get_current_time(self):
        date_now = pytz.UTC.localize(datetime.now(), is_dst=False)
        return date_now.strftime("%Y-%m-%d %H:%M:%S")

    @api.model
    def _get_current_date(self):
        return fields.Date.context_today(self)

    @api.onchange('start_time', 'end_time')
    def _validate_current_time(self):
        admin_user = self.env['res.users'].browse(1)
        local_tz = pytz.timezone(admin_user.partner_id.tz)
        star_time = pytz.UTC.localize(datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S"), is_dst=False)
        star_time = star_time.astimezone(local_tz)
        end_time = pytz.UTC.localize(datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S"), is_dst=False)
        end_time = end_time.astimezone(local_tz)
        if star_time > end_time:
            raise except_orm(_('Warning'), _('La fecha y hora de inicio, no puede ser mayor a la de fin.'))
