"""Roda o simulador, calibra os preços e escreve todos os .yml dos plugins e os relatórios.

Uso (na raiz do repositório):  python -m economia.gen.gerar_tudo
ou, dentro de economia/:        python -m gen.gerar_tudo
"""
import json
import sys
from pathlib import Path

ECON = Path(__file__).resolve().parents[1]
if str(ECON) not in sys.path:
    sys.path.insert(0, str(ECON))

from sim.modelo import Modelo, NIVELADOS, AREA                     # noqa: E402
from sim.calibrar import calibrar, calibrar_prestigio               # noqa: E402
from sim.jogador import Jogador, otimizado                          # noqa: E402
from sim import sistemas as S                                       # noqa: E402
from gen import ranks, encantamentos, outros                       # noqa: E402

SAIDA = ECON / 'saida'


def rodar(pasta=None, verbose=True):
    def log(*a):
        if verbose:
            print(*a, flush=True)

    mo = Modelo()
    log('1/6 calibrando preços dos ranks...')
    custos, hist = calibrar(mo)
    log('2/6 prestígio com os mesmos preços...')
    custos[99] = custos[98]
    f1, mult = 1.0, [1.0] * (mo.P['ranks.prestigios'] + 1)
    log('3/6 simulando estratégias...')
    eq = Jogador(mo, custos, 'equilibrado').rodar(linha=True)
    ing = Jogador(mo, custos, 'ingenuo').rodar()
    ot, tab_ot = otimizado(mo, custos)
    pres = Jogador(mo, custos, 'equilibrado').rodar(horas_max=3000, prestigios=mo.P['ranks.prestigios'],
                                                     mult_prestigio=mult)
    log('4/6 sistemas fora da mina...')
    agro = S.agricultura(mo)
    cac = S.cacto(mo, agro)
    arm = S.armazem(mo, agro, cac)
    spw = S.spawners(mo)
    mats, bos = S.matadoras_e_bosses(mo, spw)
    reqs = S.requisitos_rank(mo, spw, bos)
    log('5/6 escrevendo configs dos plugins...')
    ranks.gerar(custos, mult, pasta)
    encantamentos.gerar(mo, pasta)
    evo = outros.evolutivos(mo, pasta)
    tab_minas = outros.minas(mo, pasta)
    ids = outros.armazem(mo, agro, cac, pasta)
    cx = outros.caixas(mo, pasta)
    tab_bosses = outros.bosses(mo, bos, cx['itens_chave'], pasta)
    log('6/6 relatórios...')
    SAIDA.mkdir(exist_ok=True)
    (SAIDA / 'comandos-luckperms.txt').write_text(outros.comandos_luckperms(mo, agro), encoding='utf-8')
    resultado = {
        'custos_rank': custos, 'multiplicadores_prestigio': mult, 'fator_prestigio_1': f1,
        'calibracao': hist,
        'equilibrado': resumo_jogador(eq), 'ingenuo': resumo_jogador(ing), 'otimizado': resumo_jogador(ot),
        'otimizado_tabela': tab_ot,
        'prestigio_horas': pres.horas_prestigio,
        'linha_do_tempo': eq.linha_do_tempo,
        'alvo_h': mo.alvo_h,
        'minas': tab_minas, 'exp_por_bloco': evo['exp_por_bloco'], 'skins': evo['skins'],
        'agricultura': agro, 'cacto': cac, 'armazem': arm, 'spawners': spw,
        'matadoras': mats, 'bosses': bos, 'requisitos_rank': reqs, 'bosses_config': tab_bosses,
        'caixas': {'tabelas': cx['tabelas'], 'cadeia': cx['cadeia']},
        'precos_amostra': {e: {L: mo.preco(e, L) for L in (1, 2, 10, 50, 100, 250, 500, 750, 1000)} for e in NIVELADOS},
        'chances_amostra': {e: {L: mo.chance_pct(e, L, encantamentos.escala_da_faixa(mo, L))
                                for L in (1, 250, 251, 500, 750, 1000)} for e in AREA},
    }
    (SAIDA / 'resultado.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=1, default=str),
                                          encoding='utf-8')
    log('pronto. ativo (equilibrado):', round(eq.horas_total, 1), 'h | otimizado:', round(ot.horas_total, 1),
        'h | ingênuo:', round(ing.horas_total, 1), 'h')
    return mo, resultado


def resumo_jogador(r):
    return {'horas_total': round(r.horas_total, 2), 'chegou': r.chegou, 'estrategia': r.estrategia,
            'horas_por_posicao': [round(x, 3) for x in r.horas_por_posicao],
            'picareta_final': r.picareta_final, 'niveis_final': r.niveis_final,
            'gasto_picareta': r.gasto_picareta, 'gasto_rank': r.gasto_rank, 'gemas_gastas': r.gemas_gastas,
            'compras': r.compras, 'compras_por_hora': r.compras_por_hora, 'renda_final': r.renda_final}


if __name__ == '__main__':
    rodar()
