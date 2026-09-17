{
    'name': 'Gestão Fiscal',
    'version': '19.0.1.0.0',
    'summary': 'Gestão fiscal para o SaaS de facturação em Angola',
    'description': """
Gestão Fiscal
=============

Módulo base para configurações fiscais específicas de Angola.

Este módulo será responsável por:
- configurações fiscais da empresa;
- séries fiscais;
- extensões de impostos;
- motivos de isenção;
- base para integração futura com a AGT;
- base para geração futura do SAF-T (AO).
    """,

    'author': 'AG Code',
    'website': '',
    'category': 'Accounting/Localizations',

    'depends': [
        'base',
        'account',
    ],

   'data': [
        'security/ir.model.access.csv',

        'views/empresa_views.xml',
        'views/configuracao_fiscal_views.xml',
        'views/serie_fiscal_views.xml',
        'views/comunicacao_fiscal_agt_views.xml',
        'views/tentativa_comunicacao_agt_views.xml',
        'views/configuracao_integracao_agt_views.xml',

        # Os menus ficam por último porque dependem
        # das actions declaradas nas views anteriores.
        'views/gestao_fiscal_menus.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}