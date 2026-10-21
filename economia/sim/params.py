"""Carrega params/*.yaml e devolve um dicionário plano: P['mineracao.blocos_por_hora'] -> valor.

Todo parâmetro precisa ter valor, tipo (medido/decidido/hipotese) e fonte. Se faltar, dá erro.
"""
from pathlib import Path
import yaml

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / 'params'
TIPOS = {'medido', 'decidido', 'hipotese'}


def _achatar(d, prefixo, saida, origem):
    for k, v in d.items():
        chave = f'{prefixo}{k}'
        if isinstance(v, dict) and 'valor' in v:
            faltando = {'valor', 'tipo', 'fonte'} - set(v)
            if faltando:
                raise ValueError(f'{origem}: {chave} sem {faltando}')
            if v['tipo'] not in TIPOS:
                raise ValueError(f'{origem}: {chave} com tipo inválido {v["tipo"]}')
            saida[chave] = {'valor': v['valor'], 'tipo': v['tipo'], 'fonte': v['fonte'], 'arquivo': origem}
        elif isinstance(v, dict):
            _achatar(v, chave + '.', saida, origem)
        else:
            raise ValueError(f'{origem}: {chave} precisa de valor/tipo/fonte')


def carregar(pasta=PASTA):
    tudo = {}
    for arq in sorted(Path(pasta).glob('*.yaml')):
        dados = yaml.safe_load(arq.read_text(encoding='utf-8')) or {}
        parcial = {}
        _achatar(dados, '', parcial, arq.name)
        repetidos = set(parcial) & set(tudo)
        if repetidos:
            raise ValueError(f'parâmetro repetido em mais de um arquivo: {repetidos}')
        tudo.update(parcial)
    return tudo


class Params(dict):
    """Acesso P['x.y'] devolve só o valor; P.meta('x.y') devolve tipo e fonte."""

    def __init__(self, pasta=PASTA):
        self._meta = carregar(pasta)
        super().__init__({k: v['valor'] for k, v in self._meta.items()})

    def meta(self, chave):
        return self._meta[chave]

    def por_tipo(self, tipo):
        return {k: v for k, v in self._meta.items() if v['tipo'] == tipo}
