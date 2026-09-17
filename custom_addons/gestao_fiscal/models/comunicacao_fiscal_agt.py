import json
import uuid

from ..services.servico_agt import ServicoAGT

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ComunicacaoFiscalAgt(models.Model):
    _name = 'comunicacao.fiscal.agt'
    _description = 'Comunicação Fiscal com a Agt'
    _order = 'create_date desc, id desc'

    empresa_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    serie_fiscal_id = fields.Many2one(
        comodel_name='serie.fiscal',
        string='Série Fiscal',
        ondelete='restrict',
        index=True,
    )

    tentativa_ids = fields.One2many(
        comodel_name='tentativa.comunicacao.agt',
        inverse_name='comunicacao_id',
        string='Tentativas de Comunicação',
    )

    tipo_operacao = fields.Selection( 
        selection=[
            ('solicitar_serie','Solicitar Série'),
            ('registar_factura', 'Registar Factura'), 
            ('obter_estado', 'Obter Estado'), 
            ('listar_faturas', 'Listar Facturas'), 
            ('consultar_factura', 'Consultar Facutra')
        ], 
        string= 'Tipo de operação', 
        required=True, 
        index=True, 
    )

    identificador_operacao = fields.Char( 
        string = 'Identificador da Operação', 
        required=True, 
        readonly=True, 
        copy=False, 
        default=lambda self: str(uuid.uuid4()), 
        index=True, 
    )

    estado = fields.Selection( 
        selection=[
            ('pendente', 'Pendente'), 
            ('em_processamento', 'Em Processamento'), 
            ('sucesso', 'Sucesso'), 
            ('rejeitado', 'Rejeitado'), 
            ('erro_tecnico', 'Erro Técnico'), 
            ('estado_desconhecido', 'Estado Desconhecido')
        ], 
        string = 'Estado', 
        required =True, 
        default='pendente',
        readonly=True, 
        copy=False, 
        index=True 
    )

    data_envio = fields.Datetime( 
        string = 'Data da Envio', 
        readonly= True, 
        copy=False, 
    )

    data_resposta = fields.Datetime( 
        string = 'Data Resposta', 
        readonly=True, 
        copy=False,
    ) 

    pedido = fields.Text( 
        string = 'Pedido', 
        readonly=True, 
        copy=False,
    )

    resposta = fields.Text( 
        string= 'Resposta', 
        readonly= True, 
        copy=False
    )

    codigo_resposta = fields.Char( 
        string = 'Código Resposta', 
        readonly=True, 
        copy=False,
    )

    mensagem_erro = fields.Text( 
        string = 'Mensagem de Erro', 
        readonly=True, 
        copy=False, 
    )

    quantidade_tentativas = fields.Integer(
        string='Quantidade de Tentativas',
        compute='_calcular_quantidade_tentativas',
    )

    @api.constrains('empresa_id','serie_fiscal_id')
    def _validacao_empresa_serie(self):
        for registo in self:
            if(
                registo.serie_fiscal_id
                and registo.empresa_id != registo.serie_fiscal_id.empresa_id
             ):
                raise ValidationError( 
                    'A empresa da comunicação deve ser a mesma empresa '
                    'da Série Fiscal.'
                )

    # @api.depends informa ao Odoo que este campo calculado depende
    # das tentativas associadas à comunicação.
    # Quando tentativa_ids mudar, o Odoo sabe que deve recalcular
    # quantidade_tentativas.
    @api.depends('tentativa_ids')
    def _calcular_quantidade_tentativas(self):
        for registo in self:
            registo.quantidade_tentativas = len(
                registo.tentativa_ids
            )

    
    
    #
    # Antes de criar a tentativa, o método prepara o pedido que será
    # futuramente enviado à AGT.
    #
    # Nesta fase ainda não existe comunicação HTTP real.
    def action_criar_tentativa(self):
        self.ensure_one()

        if self.estado not in (
            'pendente',
            'erro_tecnico',
        ):
            raise ValidationError(
                'Só é possível processar comunicações Pendentes '
                'ou com Erro Técnico.'
            )

        # Constrói o payload correspondente à operação fiscal.
        payload = self._preparar_pedido()

        # Converte o dicionário Python para JSON formatado.
        pedido_json = json.dumps(
            payload,
            ensure_ascii=False,
            indent=4,
            default=str,
        )

        # Procura a última tentativa existente para determinar
        # o número sequencial da próxima tentativa.
        ultima_tentativa = self.env[
            'tentativa.comunicacao.agt'
        ].search(
            [
                ('comunicacao_id', '=', self.id),
            ],
            order='numero_tentativa desc',
            limit=1,
        )

        # Define o próximo número da tentativa.
        proximo_numero = (
            ultima_tentativa.numero_tentativa + 1
            if ultima_tentativa
            else 1
        )

        # Cria a tentativa e guarda uma cópia exacta do pedido
        # preparado para esta execução.
        tentativa = self.env[
            'tentativa.comunicacao.agt'
        ].create({
            'comunicacao_id': self.id,
            'numero_tentativa': proximo_numero,
            'pedido': pedido_json,
        })

        # Guarda também o pedido actual na comunicação lógica.
        self.write({
            'estado': 'em_processamento',
            'data_envio': fields.Datetime.now(),
            'pedido': pedido_json,
        })

        # Abre a tentativa criada para facilitar a inspecção
        # durante o desenvolvimento da integração.
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tentativa de Comunicação',
            'res_model': 'tentativa.comunicacao.agt',
            'res_id': tentativa.id,
            'view_mode': 'form',
            'target': 'current',
        }

    

    # poderá encaminhar cada operação para o serviço correspondente.
    def _preparar_pedido(self):
        self.ensure_one()

        if self.tipo_operacao == 'solicitar_serie':

            if not self.serie_fiscal_id:
                raise ValidationError(
                    'A comunicação de solicitação de série deve possuir '
                    'uma Série Fiscal associada.'
                )

            payload = ServicoAGT.construir_payload_solicitar_serie(
                env=self.env,
                serie=self.serie_fiscal_id,
                ambiente='homologacao',
            )

            return payload

        raise ValidationError(
            'A preparação do pedido ainda não foi implementada '
            'para esta operação AGT.'
        )

    
    # Define um nome amigável para identificar uma comunicação
    # fiscal através da operação e do seu identificador único.
    @api.depends(
        'tipo_operacao',
        'identificador_operacao',
    )
    def _compute_display_name(self):
        for registo in self:
            tipo_operacao = dict(
                registo._fields['tipo_operacao'].selection
            ).get(
                registo.tipo_operacao,
                registo.tipo_operacao or 'Comunicação AGT'
            )

            identificador = (
                registo.identificador_operacao[:8]
                if registo.identificador_operacao
                else ''
            )

            registo.display_name = (
                f'{tipo_operacao} · {identificador}'
            )