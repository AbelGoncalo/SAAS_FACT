from odoo.exceptions import ValidationError

import base64
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class ServicoAssinaturaAGT:

    # Constrói o conteúdo que será assinado com a chave privada
    # do produtor do software para gerar jwsSoftwareSignature.
    #
    # A AGT determina que os dados de softwareInfoDetail
    # participem da assinatura do software.
    @staticmethod
    def construir_payload_assinatura_software(configuracao):
        if not configuracao:
            raise ValidationError(
                'É necessário informar a configuração da integração AGT.'
            )

        if not configuracao.product_id:
            raise ValidationError(
                'O identificador do software não está configurado.'
            )

        if not configuracao.product_version:
            raise ValidationError(
                'A versão do software não está configurada.'
            )

        if not configuracao.software_validation_number:
            raise ValidationError(
                'O número de validação do software não está configurado.'
            )

        return {
            'productId': configuracao.product_id,
            'productVersion': configuracao.product_version,
            'softwareValidationNumber':
                configuracao.software_validation_number,
        }

    # Constrói o conteúdo fiscal da operação solicitarSerie
    # que será utilizado para gerar jwsSignature.
    #
    # Esta assinatura utilizará a chave privada do contribuinte/emissor,
    # e não a chave privada do produtor do software.
    @staticmethod
    def construir_payload_assinatura_solicitar_serie(serie):
        if not serie:
            raise ValidationError(
                'É necessário informar uma Série Fiscal.'
            )

        if not serie.empresa_id:
            raise ValidationError(
                'A Série Fiscal deve possuir uma empresa.'
            )

        if not serie.empresa_id.vat:
            raise ValidationError(
                'A empresa deve possuir um NIF configurado.'
            )

        if not serie.ano:
            raise ValidationError(
                'A Série Fiscal deve possuir um ano.'
            )

        if not serie.tipo_documento:
            raise ValidationError(
                'A Série Fiscal deve possuir um tipo de documento.'
            )

        if not serie.estabelecimento_codigo:
            raise ValidationError(
                'A Série Fiscal deve possuir um estabelecimento.'
            )

        if not serie.indicador_contingencia:
            raise ValidationError(
                'A Série Fiscal deve possuir um indicador de contingência.'
            )

        return {
            'taxRegistrationNumber':
                serie.empresa_id.vat,

            'seriesYear':
                serie.ano,

            'documentType':
                serie.tipo_documento,

            'establishmentNumber':
                serie.estabelecimento_codigo,

            'seriesContingencyIndicator':
                serie.indicador_contingencia,
        }

    # Converte bytes para Base64 URL-safe sem os caracteres "="
    # no final, conforme utilizado na representação compacta JWS.
    @staticmethod
    def _base64url(dados):
        return (
            base64.urlsafe_b64encode(dados)
            .rstrip(b'=')
            .decode('ascii')
        )

    # Converte um dicionário Python para JSON compacto e depois
    # transforma o resultado em bytes UTF-8 para utilização no JWS.
    @staticmethod
    def _serializar_json(dados):
        return json.dumps(
            dados,
            ensure_ascii=False,
            separators=(',', ':'),
        ).encode('utf-8')

    # Carrega uma chave privada RSA armazenada num ficheiro PEM.
    #
    # A chave privada nunca é guardada directamente no modelo Odoo
    # nem incorporada no código-fonte da aplicação.
    @staticmethod
    def carregar_chave_privada(caminho_chave):
        try:
            with open(caminho_chave, 'rb') as ficheiro:
                return serialization.load_pem_private_key(
                    ficheiro.read(),
                    password=None,
                )

        except (OSError, ValueError, TypeError) as erro:
            raise ValidationError(
                'Não foi possível carregar a chave privada RSA.'
            ) from erro

    # Carrega uma chave pública RSA armazenada num ficheiro PEM.
    #
    # A chave pública será utilizada principalmente para verificar
    # localmente as assinaturas durante o desenvolvimento.
    @staticmethod
    def carregar_chave_publica(caminho_chave):
        try:
            with open(caminho_chave, 'rb') as ficheiro:
                return serialization.load_pem_public_key(
                    ficheiro.read()
                )

        except (OSError, ValueError, TypeError) as erro:
            raise ValidationError(
                'Não foi possível carregar a chave pública RSA.'
            ) from erro

    # Gera uma assinatura JWS compacta utilizando o algoritmo RS256.
    #
    # RS256 corresponde a RSA PKCS#1 v1.5 com SHA-256.
    #
    # O resultado possui a estrutura:
    # BASE64URL(header).BASE64URL(payload).BASE64URL(signature)
    @staticmethod
    def gerar_jws(payload, caminho_chave_privada):
        chave_privada = (
            ServicoAssinaturaAGT.carregar_chave_privada(
                caminho_chave_privada
            )
        )

        header = {
            'typ': 'JOSE',
            'alg': 'RS256',
        }

        header_bytes = (
            ServicoAssinaturaAGT._serializar_json(
                header
            )
        )

        payload_bytes = (
            ServicoAssinaturaAGT._serializar_json(
                payload
            )
        )

        header_base64 = (
            ServicoAssinaturaAGT._base64url(
                header_bytes
            )
        )

        payload_base64 = (
            ServicoAssinaturaAGT._base64url(
                payload_bytes
            )
        )

        dados_assinados = (
            f'{header_base64}.{payload_base64}'
        ).encode('ascii')

        assinatura = chave_privada.sign(
            dados_assinados,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

        assinatura_base64 = (
            ServicoAssinaturaAGT._base64url(
                assinatura
            )
        )

        return (
            f'{header_base64}.'
            f'{payload_base64}.'
            f'{assinatura_base64}'
        )

    # Verifica localmente uma assinatura JWS utilizando
    # a chave pública correspondente à chave privada usada na assinatura.
    #
    # Retorna True quando a assinatura é válida e False quando
    # a assinatura ou os dados assinados não são válidos.
    @staticmethod
    def verificar_jws(jws, caminho_chave_publica):
        try:
            partes = jws.split('.')

            if len(partes) != 3:
                return False

            header_base64 = partes[0]
            payload_base64 = partes[1]
            assinatura_base64 = partes[2]

            dados_assinados = (
                f'{header_base64}.{payload_base64}'
            ).encode('ascii')

            padding_base64 = (
                '=' * (-len(assinatura_base64) % 4)
            )

            assinatura = base64.urlsafe_b64decode(
                assinatura_base64 + padding_base64
            )

            chave_publica = (
                ServicoAssinaturaAGT.carregar_chave_publica(
                    caminho_chave_publica
                )
            )

            chave_publica.verify(
                assinatura,
                dados_assinados,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )

            return True

        except (
            InvalidSignature,
            ValueError,
            TypeError,
        ):
            return False