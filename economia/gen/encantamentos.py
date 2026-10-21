"""Encantamentos/encantamentos.yml: chance, área, bônus e preço de cada nível da picareta.

Para não depender de como o plugin lê 'aumento-por-nivel' (que não deu para confirmar), cada
nível tem a sua própria faixa com aumento 0. Assim o valor do nível L é exatamente o que está
escrito na faixa 'L-L', qualquer que seja a fórmula do plugin.
"""
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.scalarstring import SingleQuotedScalarString as Q

from sim.modelo import AREA, BOOST, FIXOS, CHAVE_PLUGIN
from .comum import ler, escrever, mapa

ARQ = 'Encantamentos/encantamentos.yml'
BONUS_PCT = {'fortuna': 'picareta.fortuna_pct_por_nivel', 'gemado': 'picareta.gemado_pct_por_nivel',
             'chaveiro': 'design.chaveiro_pct_por_nivel'}


def escala_da_faixa(mo, L):
    for faixa, esc in mo.P['escala_area_por_faixa'].items():
        a, b = (int(x) for x in faixa.split('-'))
        if a <= L <= b:
            return esc
    return 1.0


def radios(mo, e, esc):
    dims = mo.area[e]['radios']
    if not dims:
        return None
    return 'x'.join(str(d) for d in dims_faixa(dims, esc))


def dims_faixa(dims, esc):
    return [max(1, round(d * esc)) for d in dims]


def upgrade(mo, e, maximo):
    up = CommentedMap()
    for L in range(1, maximo + 1):
        cm, cg = mo.preco(e, L)
        up[Q(f'{L - 1}-{L - 1}')] = mapa(custo=mapa(gemas=cg, money=cm), aumento=mapa(gemas=0, money=0),
                                      requisitos=mapa(), **{'aumento-requisitos': mapa()})
    return up


def level_necessario(mo, e, mensagem):
    ln = CommentedMap()
    u = mo.libera(e)
    for a in range(0, 1001, 10):
        b = min(1000, a + 9)
        teto = mo.teto_por_picareta(e, a)
        msg = mensagem if teto >= 1000 else (
            f'&f[&c&l!&f] &cLibera no nível {u} da picareta' if teto == 0 else
            '&f[&c&l!&f] &cSuba o nível da picareta para liberar mais níveis')
        ln[Q(f'{a}-{b}')] = mapa(requisitos=mapa(), **{'aumento-requisitos': mapa(), 'nivel-máximo': teto,
                                                     'mensagem': msg})
    return ln


def gerar(mo, pasta=None):
    d = ler(ARQ)
    enc = d['encantamentos']
    for e in AREA:
        v = enc[e]
        faixa0 = next(iter(v['efeito'].values()))
        extras = {k: faixa0[k] for k in ('mob', 'tempo') if k in faixa0}
        ef = CommentedMap()
        for L in range(1, 1001):
            esc = escala_da_faixa(mo, L)
            campos = {'chance': round(mo.chance_pct(e, L, esc), 9), 'aumento-por-nivel': 0}
            r = radios(mo, e, esc)
            if r:
                campos['radios'] = r
            campos.update(extras)
            ef[Q(f'{L}-{L}')] = mapa(**campos)
        v['efeito'] = ef
    for e in BOOST:
        v = enc[CHAVE_PLUGIN[e]]
        pct = mo.P[BONUS_PCT[e]]
        bo = CommentedMap()
        for L in range(1, 1001):
            bo[Q(f'{L}-{L}')] = mapa(quantidade=round(pct * L, 4), **{'aumento-por-nivel': 0})
        v['booster'] = bo
    for e in FIXOS:
        v = enc[e]
        for faixa in v['efeito'].values():
            faixa['chance'] = 100   # efeito contínuo enquanto minera (a descrição promete isso)
    for e in AREA + BOOST + FIXOS:
        chave = CHAVE_PLUGIN.get(e, e)
        v = enc[chave]
        maximo = mo.P['picareta.niveis_maximos'][e]
        v['upgrade'] = upgrade(mo, e, maximo)
        if e not in FIXOS:
            msg = next(iter(v['level-necessario'].values())).get('mensagem', '&f[&c&l!&f] &cNível máximo')
            v['level-necessario'] = level_necessario(mo, e, msg)
    return escrever(ARQ, d, pasta)
