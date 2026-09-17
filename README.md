 # Facturação SaaS

Plataforma SaaS de facturação desenvolvida sobre **Odoo 19 Community**, com foco na gestão fiscal e integração com os serviços de **Facturação Electrónica da Administração Geral Tributária de Angola (AGT)**.

O projeto procura aproveitar os recursos nativos do Odoo para contabilidade, clientes, produtos, impostos, pagamentos e empresas, adicionando uma camada própria para os requisitos fiscais e de integração com a AGT.

> **Estado:** Em desenvolvimento.

---

## Objetivo

Construir uma solução de facturação SaaS capaz de suportar empresas angolanas e os requisitos técnicos associados à Facturação Electrónica da AGT.

Um dos princípios da arquitetura é:

> Não reconstruir dentro do Odoo aquilo que o Odoo já resolve bem.

Por isso, os modelos padrão do Odoo são reutilizados sempre que possível e as funcionalidades fiscais específicas são implementadas através de módulos próprios.

---

## Tecnologias

- Odoo 19 Community
- Python 3.12
- PostgreSQL 16
- XML
- JSON
- RSA / RS256
- JWS (JSON Web Signature)
- Git

---

## Estrutura do projeto

```text
Facturacao_Saas/
├── custom_addons/
│   └── gestao_fiscal/
│
├── odoo/
│
├── secrets/
│
├── venv_odoo19/
│
├── odoo.conf
├── .gitignore
└── README.md
```

### `custom_addons/`

Contém os módulos desenvolvidos especificamente para a plataforma.

O primeiro módulo é:

```text
gestao_fiscal
```

### `odoo/`

Código-fonte oficial do Odoo 19 Community.

Este diretório não faz parte do código desenvolvido pelo projeto e não é versionado no repositório principal.

### `secrets/`

Utilizado localmente para chaves criptográficas e outros segredos.

**Nunca deve ser versionado no Git.**

### `venv_odoo19/`

Ambiente virtual Python utilizado pelo projeto.

Também não deve ser versionado.

---

## Módulo Gestão Fiscal

O módulo:

```text
custom_addons/gestao_fiscal/
```

é responsável pelo núcleo fiscal da plataforma.

Estrutura atual:

```text
gestao_fiscal/
├── models/
├── security/
├── services/
├── views/
├── __init__.py
└── __manifest__.py
```

Entre os componentes atualmente implementados encontram-se:

- Configuração fiscal por empresa;
- Séries fiscais;
- Configuração da integração AGT;
- Comunicações fiscais com a AGT;
- Tentativas de comunicação;
- Preparação dos pedidos fiscais;
- Serviço de assinatura digital JWS.

---

## Modelos principais

### Empresa

A plataforma reutiliza o modelo padrão:

```text
res.company
```

para representar as entidades empresariais.

Os dados que já pertencem ao Odoo não são duplicados no módulo fiscal.

---

### Configuração Fiscal

Representa o enquadramento fiscal de uma empresa durante determinado período.

Permite gerir, entre outros:

- regime de IVA;
- período de vigência;
- estado da configuração;
- validação de sobreposição de períodos.

---

### Série Fiscal

Representa uma série utilizada na emissão de documentos fiscais.

A série está associada a uma empresa e contém informações como:

- ano;
- tipo de documento;
- estabelecimento;
- indicador de contingência;
- código da série atribuído pela AGT;
- intervalo autorizado;
- estado da série.

---

### Comunicação Fiscal AGT

Representa uma operação fiscal lógica enviada ou destinada à AGT.

Exemplos:

```text
solicitar_serie
registar_factura
obter_estado
listar_facturas
consultar_factura
```

A comunicação mantém o estado funcional da operação e o respetivo histórico.

---

### Tentativa de Comunicação AGT

Representa uma execução técnica de uma comunicação.

Uma comunicação pode possuir várias tentativas.

Esta separação permite controlar:

- novas tentativas;
- erros técnicos;
- respostas da AGT;
- duração da comunicação;
- códigos HTTP;
- operações cujo resultado ficou desconhecido.

Essa abordagem ajuda a evitar a repetição indevida de operações fiscais.

---

## Integração com a AGT

A arquitetura está a ser preparada para integração com os serviços de Facturação Electrónica da AGT.

Entre as operações previstas estão:

```text
solicitarSerie
registarFactura
obterEstado
listarFacturas
consultarFactura
listarSeries
validarDocumento
```

A integração é implementada de forma desacoplada da lógica principal do Odoo.

---

## Assinaturas JWS

A comunicação com a AGT utiliza assinaturas digitais baseadas em:

```text
JWS
RSA
RS256
```

O projeto possui um serviço dedicado:

```text
services/servico_assinatura_agt.py
```

responsável pela preparação e geração das assinaturas.

Durante o desenvolvimento são utilizadas chaves RSA exclusivamente locais.

As chaves privadas **não devem ser armazenadas no código-fonte nem versionadas no Git**.

---

## Testes criptográficos

O mecanismo básico de assinatura JWS foi validado localmente através dos seguintes testes:

```text
JWS dividido em 3 componentes        → OK
Validação com chave pública correta  → True
Validação com chave pública incorreta → False
```

As chaves utilizadas nestes testes são apenas para desenvolvimento.

---

## Executar o projeto

### 1. Criar o ambiente virtual

```bash
python3 -m venv venv_odoo19
```

### 2. Ativar

```bash
source venv_odoo19/bin/activate
```

### 3. Instalar as dependências

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r odoo/requirements.txt
```

### 4. Configurar o Odoo

Crie o ficheiro:

```text
odoo.conf
```

com a configuração local do PostgreSQL, caminhos de addons e demais parâmetros necessários.

Não coloque credenciais reais no repositório.

### 5. Executar

```bash
python odoo/odoo-bin -c odoo.conf
```

A aplicação ficará normalmente disponível em:

```text
http://localhost:8069
```

---

## Base de dados de desenvolvimento

O projeto utiliza PostgreSQL.

Cada desenvolvedor deve configurar a sua própria base de dados e credenciais no ambiente local.

Credenciais, passwords e configurações sensíveis não devem ser adicionadas ao repositório.

---
