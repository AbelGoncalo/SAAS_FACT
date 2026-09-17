import uuid

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class SerieFiscal(models.Model):
    _name= 'serie.fiscal'
    _description='Série Fiscal'
    _order= 'ano desc, id desc'

    empresa_id = fields.Many2one( 
        comodel_name = 'res.company',
        string = 'Empresa',
        required= True,
        default=lambda self: self.env.company,
        index= True,
    )

    ano = fields.Integer( 
        string = 'ano',
        required=True,
        default = lambda self: fields.Date.today().year, 
    )

    tipo_documento = fields.Selection( 
        selection=[
           ('FA', 'FA - Factura de Adiantamento'),
            ('FT', 'FT - Factura'),
            ('FR', 'FR - Factura/Recibo'),
            ('FG', 'FG - Factura Global'),
            ('GF', 'GF - Factura Genérica'),
            ('AC', 'AC - Aviso de Cobrança'),
            ('AR', 'AR - Aviso de Cobrança/Recibo'),
            ('TV', 'TV - Talão de Venda'),
            ('RC', 'RC - Recibo em Numerário'),
            ('RG', 'RG - Recibo Geral'),
            ('RE', 'RE - Recibo de Estorno'),
            ('ND', 'ND - Nota de Débito'),
            ('NC', 'NC - Nota de Crédito'),
            ('AF', 'AF - Factura/Recibo de Autofacturação'),
            ('RP', 'RP - Recibo de Prémio'),
            ('RA', 'RA - Resseguro Aceite'),
            ('CS', 'CS - Imputação a Co-seguradoras'),
            ('LD', 'LD - Imputação a Co-seguradora Líder'),
        ],
        string='Tipo de Documento',
        required=True,
    )

    estabelecimento_codigo = fields.Char( 
        string='Código do Establecimento',
        required=True,
        default='SEDE',
    )

    indicador_contingencia = fields.Selection( 
        selection=[
            ('N', 'Normal'),
            ('C', 'Contingência'),
        ],
        string='Tipo de Série',
        required=True,
        default='N',
    )

    identificador_solicitacao = fields.Char(
        string='Identificador da Solicitação',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: str(uuid.uuid4()),
    )

    codigo_serie_agt= fields.Char( 
        string= 'Código da Série da AGT', 
        readonly=True, 
        copy=False, 
    )

    quantidade_autorizada = fields.Integer( 
        string= 'Quantidade Autorizada',
        readonly=True, 
        copy=False, 
    )

    primeiro_numero_documento = fields.Integer( 
        string='Primeiro Número Autorizado', 
        readonly=True, 
        copy=False
    )

    ultimo_numero_documento = fields.Integer( 
        string =' Último Número Autorizado', 
        readonly=True, 
        copy=False,
    )

    estado = fields.Selection(
        selection=[
            ('rascunho', 'Rascunho'),
            ('pendente_agt', 'Pendente AGT'),
            ('autorizada', 'Autorizada'),
            ('rejeitada', 'Rejeitada'),
            ('inactiva', 'Inactiva'),
        ],
        string='Estado',
        required=True,
        default='rascunho',
        copy=False,
        readonly=True,
    )

    observacao = fields.Text(
        string='Observação',
    )

    comunicacao_agt_ids = fields.One2many(
        comodel_name='comunicacao.fiscal.agt',
        inverse_name='serie_fiscal_id',
        string='Comunicações AGT',
    )

    quantidade_comunicacoes_agt = fields.Integer(
        string='Comunicações AGT',
        compute='_calcular_quantidade_comunicacoes_agt',
    )

    def _calcular_quantidade_comunicacoes_agt(self):
        for registo in self:
            registo.quantidade_comunicacoes_agt = len(
                registo.comunicacao_agt_ids
            )

    @api.constrains( 
        'primeiro_numero_documento', 
        'ultimo_numero_documento',
    )
    def _validar_intervalo_numeracao(self):
        for registo in self:
            if( 
                registo.primeiro_numero_documento
                and registo.ultimo_numero_documento
                and registo.ultimo_numero_documento
                < registo.primeiro_numero_documento
            ):

                raise ValidationError( 
                    'O último número autorizado não pode ser inferior '
                    'ao primeiro número autorizado.'
                )


    @api.constrains('quantidade_autorizada')
    def _validadar_quantidade_autorizada(self):
        for registo in self:
            if registo.quantidade_autorizada < 0:
                raise ValidationError(
                    'A quantidade autorizada não pode ser negativa.'
                )

    @api.constrains('ano')
    def _validar_ano(self):
        for registo in self:
            if registo.ano < 2000 or registo.ano > 9999:
                raise ValidationError(
                    'O ano da série fiscal deve ser igual ou superior a 2000.'
                )


    def action_solicitar_serie(self):
        for registo in self:
            if registo.estado != 'rascunho':
                raise ValidationError(
                    'Apenas séries em estado Rascunho podem ser solicitadas à AGT.'
                )

            comunicacao_existente = self.env['comunicacao.fiscal.agt'].search([
                ('serie_fiscal_id', '=', registo.id),
                ('tipo_operacao', '=', 'solicitar_serie'),
                ('estado', 'in', [
                    'pendente',
                    'em_processamento',
                    'sucesso',
                ]),
            ], limit=1)

            if comunicacao_existente:
                raise ValidationError(
                    'Já existe uma comunicação activa para solicitar esta série à AGT.'
                )

            self.env['comunicacao.fiscal.agt'].create({
                'empresa_id': registo.empresa_id.id,
                'serie_fiscal_id': registo.id,
                'tipo_operacao': 'solicitar_serie',
            })

            registo.estado = 'pendente_agt'


    def action_marcar_autorizada(self):
        for registo in self:
            if registo.estado != 'pendente_agt':
                raise ValidationError(
                    'A série só pode ser autorizada quando estiver Pendente AGT.'
                )

            if not registo.codigo_serie_agt:
                raise ValidationError(
                    'Não é possível autorizar a série sem o código devolvido pela AGT.'
                )

            registo.estado = 'autorizada'


    def action_marcar_rejeitada(self):
        for registo in self:
            if registo.estado != 'pendente_agt':
                raise ValidationError(
                    'A série só pode ser rejeitada quando estiver Pendente AGT.'
                )

            registo.estado = 'rejeitada'


    def action_inactivar(self):
        for registo in self:
            if registo.estado != 'autorizada':
                raise ValidationError(
                    'Apenas séries autorizadas podem ser inactivadas.'
                )

            registo.estado = 'inactiva'


    # Define o nome amigável utilizado pelo Odoo para apresentar
    # a Série Fiscal em campos relacionais, títulos e pesquisas.
    @api.depends(
        'tipo_documento',
        'ano',
        'estabelecimento_codigo',
    )
    def _compute_display_name(self):
        for registo in self:
            partes = [
                registo.tipo_documento or 'Série',
                str(registo.ano) if registo.ano else None,
                registo.estabelecimento_codigo,
            ]

            registo.display_name = ' · '.join(
                parte for parte in partes if parte
            )