from odoo import fields
from odoo.exceptions import ValidationError
from . servico_assinatura_agt import ServicoAssinaturaAGT

class ServicoAGT:

    # Procura a configuração activa da integração AGT
    # para a empresa e o ambiente informados.
    @staticmethod
    def obter_configuracao_activa(
        env,
        empresa,
        ambiente='homologacao',
    ):
        configuracao = env[
            'configuracao.integracao.agt'
        ].search([
            ('empresa_id', '=', empresa.id),
            ('ambiente', '=', ambiente),
            ('activa', '=', True),
        ], limit=1)

        if not configuracao:
            raise ValidationError(
                'Não existe uma configuração activa da integração '
                'AGT para esta empresa e ambiente.'
            )

        return configuracao


    # Constrói os dados fiscais básicos necessários
    # para a operação solicitarSerie.
    @staticmethod
    def construir_dados_solicitacao_serie(serie):
        if not serie:
            raise ValidationError(
                'É necessário informar uma série fiscal.'
            )

        if not serie.empresa_id.vat:
            raise ValidationError(
                'A empresa deve possuir um NIF configurado.'
            )

        if not serie.identificador_solicitacao:
            raise ValidationError(
                'A série deve possuir um identificador de solicitação.'
            )

        return {
            'submissionUUID': serie.identificador_solicitacao,
            'taxRegistrationNumber': serie.empresa_id.vat,
            'seriesYear': serie.ano,
            'documentType': serie.tipo_documento,
            'establishmentNumber':
                serie.estabelecimento_codigo,
            'seriesContingencyIndicator':
                serie.indicador_contingencia,
        }


    # Constrói os dados de identificação do software
    # conforme a estrutura esperada pela integração AGT.
    #
    # A assinatura jwsSoftwareSignature será adicionada
    # posteriormente pelo serviço de assinatura.
    @staticmethod
    def construir_informacao_software(configuracao):
        software_info_detail = (
            ServicoAssinaturaAGT
            .construir_payload_assinatura_software(
                configuracao
            )
        )

        return {
            'softwareInfoDetail': software_info_detail,
        }
        
    # Constrói o payload da operação solicitarSerie.
    #
    # Este método junta os dados da Série Fiscal com os
    # dados da configuração da integração AGT.
    # As assinaturas JWS ainda não são geradas nesta etapa.
    @staticmethod
    def construir_payload_solicitar_serie(
        env,
        serie,
        ambiente='homologacao',
    ):
        configuracao = (
            ServicoAGT.obter_configuracao_activa(
                env=env,
                empresa=serie.empresa_id,
                ambiente=ambiente,
            )
        )

        dados_serie = (
            ServicoAGT.construir_dados_solicitacao_serie(
                serie
            )
        )

        software_info = (
            ServicoAGT.construir_informacao_software(
                configuracao
            )
        )

        return {
            'schemaVersion': configuracao.schema_version,
            **dados_serie,
            'submissionTimeStamp':
                fields.Datetime.now().isoformat(),
            'softwareInfo': software_info,
        }