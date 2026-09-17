from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ConfiguracaoFiscal(models.Model):
    _name = 'configuracao.fiscal'
    _description = 'Configuração Fiscal'
    _order = 'data_inicio desc, id desc'

    empresa_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    regime_iva = fields.Selection(
        selection=[
            ('geral', 'Regime Geral'),
            ('simplificado', 'Regime Simplificado'),
            ('nao_sujeicao', 'Regime de Não Sujeição'),
        ],
        string='Regime de IVA',
        required=True,
    )

    data_inicio = fields.Date(
        string='Data de Início',
        required=True,
    )

    data_fim = fields.Date(
        string='Data de Fim',
    )

    estado = fields.Selection(
        selection=[
            ('rascunho', 'Rascunho'),
            ('activo', 'Activo'),
            ('inativo', 'Inativo'),
        ],
        string='Estado',
        required=True,
        default='rascunho',
    )

    observacao = fields.Text(
        string='Observação',
    )

    @api.constrains('data_inicio', 'data_fim')
    def _validar_periodo(self):
        for registo in self:
            if (
                registo.data_inicio
                and registo.data_fim
                and registo.data_fim < registo.data_inicio
            ):
                raise ValidationError(
                    'A Data de Fim não pode ser anterior à Data de Início.'
                )

    @api.constrains(
        'empresa_id',
        'data_inicio',
        'data_fim',
        'estado',
    )
    def _validar_sobreposicao_periodos(self):
        for registo in self:

            if (
                not registo.empresa_id
                or not registo.data_inicio
                or registo.estado == 'inativo'
            ):
                continue

            configuracoes = self.search([
                ('id', '!=', registo.id),
                ('empresa_id', '=', registo.empresa_id.id),
                ('estado', '!=', 'inativo'),
            ])

            for configuracao in configuracoes:

                inicio_actual = registo.data_inicio
                fim_actual = registo.data_fim

                inicio_existente = configuracao.data_inicio
                fim_existente = configuracao.data_fim

                sobreposto = (
                    (not fim_actual or inicio_existente <= fim_actual)
                    and
                    (not fim_existente or inicio_actual <= fim_existente)
                )

                if sobreposto:
                    raise ValidationError(
                        'Já existe uma configuração fiscal para esta empresa '
                        'com um período de vigência sobreposto.'
                    )