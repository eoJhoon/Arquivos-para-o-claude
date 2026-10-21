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
        pres = ranks[k]['prestigio']
        base = pres['1']
        base['custo']['money'] = float(custos[s])
        # apaga prestígios antigos e recria a partir da volta 1
        for p in [x for x in pres.keys() if str(x) != '1']:
            del pres[p]
        for P in range(1, len(multiplicadores)):
            novo = copy.deepcopy(base)
            novo['custo']['money'] = float(round(custos[s] * multiplicadores[P]))
            pres[str(P + 1)] = novo
    return escrever(ARQ, d, pasta)
