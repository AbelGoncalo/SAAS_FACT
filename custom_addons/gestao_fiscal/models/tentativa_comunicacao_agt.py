from odoo import fields, models


class TentativaComunicacaoAGT(models.Model):
    _name = 'tentativa.comunicacao.agt'
    _description = 'Tentativa de Comunicação com a AGT'
    _order = 'numero_tentativa desc, id desc'

    comunicacao_id = fields.Many2one(
        comodel_name='comunicacao.fiscal.agt',
        string='Comunicação AGT',
        required=True,
        ondelete='cascade',
        index=True,
    )

    numero_tentativa = fields.Integer(
        string='Número da Tentativa',
        required=True,
        readonly=True,
        copy=False,
    )

    data_inicio = fields.Datetime(
        string='Data de Início',
        required=True,
        default=fields.Datetime.now,
        readonly=True,
        copy=False,
    )

    data_fim = fields.Datetime(
        string='Data de Fim',
        readonly=True,
        copy=False,
    )

    estado = fields.Selection(
        selection=[
            ('em_processamento', 'Em Processamento'),
            ('sucesso', 'Sucesso'),
            ('erro_tecnico', 'Erro Técnico'),
            ('estado_desconhecido', 'Estado Desconhecido'),
        ],
        string='Estado',
        required=True,
        default='em_processamento',
        readonly=True,
        copy=False,
        index=True,
    )

    codigo_http = fields.Integer(
        string='Código HTTP',
        readonly=True,
        copy=False,
    )

    pedido = fields.Text(
        string='Pedido',
        readonly=True,
        copy=False,
    )

    resposta = fields.Text(
        string='Resposta',
        readonly=True,
        copy=False,
    )

    mensagem_erro = fields.Text(
        string='Mensagem de Erro',
        readonly=True,
        copy=False,
    )

    duracao_ms = fields.Integer(
        string='Duração (ms)',
        readonly=True,
        copy=False,
    )

     # Verifica se a tentativa ainda está em processamento.
    # Este método centraliza a validação usada pelos métodos
    # que finalizam uma tentativa.
      # Verifica se a tentativa ainda está em processamento.
    # Este método centraliza a validação usada pelos métodos
    # que finalizam uma tentativa.
    def _validar_em_processamento(self):
        for registo in self:
            if registo.estado != 'em_processamento':
                raise ValidationError(
                    'Apenas tentativas em processamento podem ser finalizadas.'
                )


    # Finaliza a tentativa com sucesso.
    # Também actualiza a comunicação pai para "Sucesso"
    # e regista a data em que a resposta foi recebida.
    def action_marcar_sucesso(self):
        self._validar_em_processamento()

        for registo in self:
            agora = fields.Datetime.now()

            registo.write({
                'estado': 'sucesso',
                'data_fim': agora,
                'codigo_http': 200,
            })

            registo.comunicacao_id.write({
                'estado': 'sucesso',
                'data_resposta': agora,
            })


    # Finaliza a tentativa como erro técnico.
    # Este estado representa problemas técnicos, como indisponibilidade,
    # timeout, erro HTTP ou falha de comunicação.
    # A comunicação pai também fica disponível para uma nova tentativa.
    def action_marcar_erro_tecnico(self):
        self._validar_em_processamento()

        for registo in self:
            agora = fields.Datetime.now()

            registo.write({
                'estado': 'erro_tecnico',
                'data_fim': agora,
            })

            registo.comunicacao_id.write({
                'estado': 'erro_tecnico',
                'data_resposta': agora,
            })


    # Finaliza a tentativa quando não conseguimos determinar com segurança
    # se a AGT recebeu/processou a operação.
    # Este estado é diferente de um simples erro técnico porque uma nova
    # tentativa imediata poderia provocar uma operação duplicada.
    def action_marcar_estado_desconhecido(self):
        self._validar_em_processamento()

        for registo in self:
            agora = fields.Datetime.now()

            registo.write({
                'estado': 'estado_desconhecido',
                'data_fim': agora,
            })

            registo.comunicacao_id.write({
                'estado': 'estado_desconhecido',
                'data_resposta': agora,
            })