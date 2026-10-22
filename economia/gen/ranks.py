"""Rankup/ranks.yml: preço dos 100 ranks e os 10 prestígios.

Posição 0 (default, Cidadão I) até 99 (rank99, Dragão X). O custo de cada entrada é o preço para
sair dela e ir para a próxima. O custo do rank99 é o preço de prestigiar.
Prestígio P usa a chave str(P+1) dentro de 'prestigio' (a '1' é a primeira volta, sem prestígio).
"""
import copy

from .comum import ler, escrever, num

ARQ = 'Rankup/ranks.yml'


def gerar(custos, multiplicadores, pasta=None):
    d = ler(ARQ)
    ranks = d['rankup']
    chaves = list(ranks.keys())
    assert len(chaves) == 100, f'esperava 100 ranks, achei {len(chaves)}'
    for s, k in enumerate(chaves):
        # prestígio usa os mesmos preços (pedido de formato simples); só a 1a volta é escrita
        ranks[k]['prestigio']['1']['custo']['money'] = float(custos[s])
    return escrever(ARQ, d, pasta)
