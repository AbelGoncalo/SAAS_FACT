from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ConfiguracaoIntegracaoAGT(models.Model):
    _name = 'configuracao.integracao.agt'
    _description = 'Configuração da Integração com a AGT'
    _order = 'empresa_id, id desc'

    empresa_id = fields.Many2one( 
        comodel_name='res.company', 
        string='Empresa', 
        required=True, 
        default=lambda self: self.env.company, 
        index=True, 
        ondelete='cascade', 
    )

    ambiente = fields.Selection( 
        selection=[
            ('homologacao','Homologação'), 
            ('producao','Produção'),
        ], 
        string='Ambiente', 
        required=True, 
        default='homologacao',
    )

    schema_version = fields.Char( 
        string='Versão do Esquema', 
        required=True,
        default='2.0'
    )

    product_id = fields.Char( 
        string='Identificador do Software', 
        required=True,
    )

    product_version = fields.Char( 
        string='Versão do Software', 
        required=True,
    )

    software_validation_number = fields.Char( 
        string='Número de Validação do Software',
    )
    activa = fields.Boolean( 
        string='Activa', 
        default=True
    )

    # Garante que uma empresa não possua mais de uma configuração
    # activa para o mesmo ambiente de integração com a AGT.
    @api.constrains('empresa_id','ambiente', 'activa')
    def _validar_configuracao_activa(self):
        for registo in self:
            if not registo.activa:
                continue

            configuracao_existente = self.search([
                ('id', '!=', registo.id), 
                ('empresa_id', '=', registo.empresa_id.id), 
                ('ambiente', '=', registo.ambiente), 
                ('activa', '=', True)
            ], limit=1)

            if configuracao_existente:
                 raise ValidationError(
                    'Já existe uma configuração activa da integração '
                    'AGT para esta empresa e ambiente.'
                )


    # Define o nome amigável da configuração AGT utilizando
    # a empresa e o ambiente configurado.
    @api.depends(
        'empresa_id',
        'ambiente',
    )
    def _compute_display_name(self):
        for registo in self:
            empresa = (
                registo.empresa_id.name
                if registo.empresa_id
                else 'Empresa'
            )

            ambiente = dict(
                registo._fields['ambiente'].selection
            ).get(
                registo.ambiente,
                registo.ambiente or ''
            )

            registo.display_name = (
                f'{empresa} · {ambiente}'
            )

