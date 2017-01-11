# -*- coding: utf-8 -*-

import time
from datetime import datetime

from openerp import models, fields, api
from openerp.exceptions import Warning


class AccountAtsDoc(models.Model):
    _name = 'account.ats.doc'
    _description = 'Tipos Comprobantes Autorizados'

    code = fields.Char('Código', size=2, required=True)
    name = fields.Char('Tipo Comprobante', size=64, required=True)


class AccountAtsSustento(models.Model):
    _name = 'account.ats.sustento'
    _description = 'Sustento del Comprobante'

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        reads = self.browse(cr, uid, ids, context=context)
        for record in reads:
            name = '%s - %s' % (record.code, record.type)
            res.append((record.id, name))
        return res

    _rec_name = 'type'
    
    code = fields.Char('Código', size=2, required=True)
    type = fields.Char('Tipo de Sustento', size=64, required=True)


class AccountAuthorisation(models.Model):

    _name = 'account.authorisation'
    _description = 'Authorisation for Accounting Documents'
    _order = 'expiration_date desc'

    def name_get(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not ids:
            return []
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = '%s (%s-%s)' % (record.type_id.name, record.num_start, record.num_end)
            res.append((record.id, name))
        return res

    @api.one
    def _check_active(self):
        """
        Check the due_date to give the value active field
        """
        now = datetime.strptime(time.strftime("%Y-%m-%d"),'%Y-%m-%d')
        due_date = datetime.strptime(self.expiration_date, '%Y-%m-%d')
        self.active = now<due_date

    def _get_type(self):
        return self._context.get('type', 'in_invoice')

    def _get_in_type(self):
        return self._context.get('in_type', 'externo')

    def _get_partner(self):
        user_id = self.env.user.id
        if self._context.get('partner_id'):
            user_id = context.get('partner_id')
        return user_id

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, values):
        partner_id = self.env.user.company_id.partner_id.id
        if values.get('partner_id', False) and values['partner_id'] == partner_id:
            ats_obj = self.env['account.ats.doc']
            name_type = '{0}_{1}'.format(values['name'], values['type_id'])
            code_obj = self.env['ir.sequence.type']
            seq_obj = self.env['ir.sequence']
            code_data = {
                'code': '%s.%s.%s' % (name_type,values['serie_entidad'],values['serie_emision']),
                'name': name_type,
                }
            code = code_obj.create(code_data)
            sequence_data = {
                'name': name_type,
                'padding': 9,
                'number_next': values['num_start'],
                'code': code.code
                }
            seq = seq_obj.create(sequence_data)
            values.update({'sequence_id': seq.id})
        return super(AccountAuthorisation, self).create(values)

    @api.multi
    def unlink(self):
        journal = self.env['account.journal']
        res = journal.search(['|',('auth_id','=',self.id),('auth_ret_id', '=', self.id)])
        if res:
            raise Warning('Alerta', 'Esta autorización esta relacionada a un diario.')
        return super(AccountAuthorisation, self).unlink()

    name = fields.Char('Num. de Autorizacion', size=128, required=True)
    serie_entidad = fields.Char('Serie Entidad', size=3, required=True)
    serie_emision = fields.Char('Serie Emision', size=3, required=True)
    num_start = fields.Integer('Desde', required=True)
    num_end = fields.Integer('Hasta', required=True)
    is_electronic = fields.Boolean('Documento Electrónico ?')
    expiration_date = fields.Date('Vence', required=True)
    active = fields.Boolean(
        compute='_check_active',
        string='Activo',
        store=True,
        default=True
        )
    in_type = fields.Selection(
        [('interno', 'Internas'),
         ('externo', 'Externas')],
        string='Tipo Interno',
        readonly=True,
        change_default=True,
        default=_get_in_type
        )
    type_id = fields.Many2one(
        'account.ats.doc',
        'Tipo de Comprobante',
        required=True
        )
    partner_id = fields.Many2one(
        'res.partner',
        'Empresa',
        required=True,
        default=_get_partner
        )
    sequence_id = fields.Many2one(
        'ir.sequence',
        'Secuencia',
        help='Secuencia Alfanumerica para el documento, se debe registrar cuando pertenece a la compañia',
        ondelete='cascade'
        )

    def set_authorisation(cr, uid, ids, context):
        return True

    _sql_constraints = [
        ('number_unique',
         'unique(name,partner_id,serie_entidad,serie_emision,type_id)',
         u'La relación de autorización, serie entidad, serie emisor y tipo, debe ser única.'),
        ]

    def is_valid_number(self, cr, uid, id, number):
        """
        Metodo que verifica si @number esta en el rango
        de [@num_start,@num_end]
        """
        obj = self.browse(cr, uid, id)
        if obj.num_start <= number <= obj.num_end:
            return True
        return False


class ResParter(models.Model):
    _inherit = 'res.partner'

    authorisation_ids = fields.One2many(
        'account.authorisation',
        'partner_id',
        'Autorizaciones'
        )


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    auth_id = fields.Many2one(
        'account.authorisation',
        help='Autorización utilizada para Facturas y Liquidaciones de Compra',
        string='Autorización',
        domain=[('in_type','=','interno')]
        )
    auth_ret_id = fields.Many2one(
        'account.authorisation',
        domain=[('in_type','=','interno')],
        string='Autorización de Ret.',
        help='Autorizacion utilizada para Retenciones, facturas y liquidaciones'
        )



