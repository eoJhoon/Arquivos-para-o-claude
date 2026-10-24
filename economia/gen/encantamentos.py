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
    """Preço em faixas (formato do plugin): custo no início da faixa + aumento por nível."""
    up = CommentedMap()
    if e in FIXOS:
        for L in range(1, maximo + 1):
            cm, cg = mo.preco(e, L)
            up[Q(f'{L - 1}-{L - 1}')] = mapa(custo=mapa(gemas=cg, money=cm), aumento=mapa(gemas=0, money=0),
                                          requisitos=mapa(), **{'aumento-requisitos': mapa()})
        return up
    for a, b, cm, am, cg, ag in mo.faixas_preco(e):
        up[Q(f'{a}-{b}')] = mapa(custo=mapa(gemas=cg, money=cm), aumento=mapa(gemas=ag, money=am),
                                 requisitos=mapa(), **{'aumento-requisitos': mapa()})
    return up


def level_necessario(mo, e, mensagem):
    """Libera o encantamento só a partir do nível u da picareta."""
    ln = CommentedMap()
    u = mo.libera(e)
    if u > 0:
        ln[Q(f'0-{u - 1}')] = mapa(requisitos=mapa(), **{'aumento-requisitos': mapa(), 'nivel-máximo': 0,
                                                          'mensagem': f'&f[&c&l!&f] &cLibera no nível {u} da picareta'})
    ln[Q(f'{u}-1000')] = mapa(requisitos=mapa(), **{'aumento-requisitos': mapa(), 'nivel-máximo': 1000,
                                                     'mensagem': mensagem})
    return ln


def chance_area(mo, e):
    """Chance no formato do plugin (1 faixa): chance(L) = aumento x L. Igual ao formato que vocês já usam."""
    por_nivel = mo.chance_pct(e, 1000, 1.0) / 1000
    return round(por_nivel, 10)


def gerar(mo, pasta=None):
    d = ler(ARQ)
    enc = d['encantamentos']
    for e in AREA:
        v = enc[e]
        faixa0 = next(iter(v['efeito'].values()))
        pn = chance_area(mo, e)
        campos = {'chance': pn, 'aumento-por-nivel': pn}
        dims = mo.area[e]['radios']          # medida original de vocês (params)
        if dims:
            campos['radios'] = 'x'.join(str(x) for x in dims) if len(dims) > 1 else str(dims[0])
        for k in ('mob', 'tempo'):
            if k in faixa0:
                campos[k] = faixa0[k]
        ef = CommentedMap()
        ef[Q('1-1000')] = mapa(**campos)
        v['efeito'] = ef
    for e in BOOST:
        v = enc[CHAVE_PLUGIN[e]]
        pct = mo.P[BONUS_PCT[e]]
        bo = CommentedMap()
        bo[Q('1-1000')] = mapa(quantidade=pct, **{'aumento-por-nivel': pct})
        v['booster'] = bo
    for e in AREA + BOOST + FIXOS:
        chave = CHAVE_PLUGIN.get(e, e)
        v = enc[chave]
        maximo = mo.P['picareta.niveis_maximos'][e]
        v['upgrade'] = upgrade(mo, e, maximo)
        if e not in FIXOS:
            msg = next(iter(v['level-necessario'].values())).get('mensagem', '&f[&c&l!&f] &cNível máximo')
            v['level-necessario'] = level_necessario(mo, e, msg)
    return escrever(ARQ, d, pasta)
