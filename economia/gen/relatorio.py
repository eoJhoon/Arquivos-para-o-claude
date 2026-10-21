"""Relatórios em texto: o-que-medir.md (lista de testes) e numeros.md (tabelas principais).

Lê economia/saida/resultado.json. O texto explicativo fixo fica em economia/README.md e docs/.
"""
import json
import re
import sys
from pathlib import Path

ECON = Path(__file__).resolve().parents[1]
if str(ECON) not in sys.path:
    sys.path.insert(0, str(ECON))

from sim.modelo import Modelo, AREA, NIVELADOS     # noqa: E402
from sim.params import Params                       # noqa: E402
from gen.planilha import fmt, nome_pos, NOME_ENC     # noqa: E402


def o_que_medir(P):
    linhas = ['# O que medir no servidor', '',
              'Lista gerada a partir de params/hipoteses.yaml. Cada teste troca uma suposição por um número real.',
              'Quando medirem, mudem o valor no params, troquem o tipo para "medido" e escrevam a fonte.', '']
    n = 0
    for k in sorted(P):
        m = P.meta(k)
        if m['tipo'] != 'hipotese':
            continue
        f = str(m['fonte'])
        if 'Validar' not in f:
            continue
        n += 1
        teste = f.split('Validar', 1)[1].lstrip(':').strip()
        linhas.append(f'{n}. **{k}** (hoje: {json.dumps(m["valor"], ensure_ascii=False)[:60]}). Teste: {teste}')
    return '\n'.join(linhas) + '\n'


def numeros(res, mo, P):
    eq = res['equilibrado']
    L = ['# Números principais (gerado pelo simulador)', '',
         f"Jogador ativo típico: **{eq['horas_total']:.0f} h** até o Dragão X. Que otimiza: "
         f"{res['otimizado']['horas_total']:.0f} h. Que só corre para rank: {res['ingenuo']['horas_total']:.0f} h.", '',
         '## Tempo por rank (jogador ativo)', '', '| Rank | Horas | Acumulado | Preço do I | Preço do X |',
         '|---|---|---|---|---|']
    acum = 0
    for m in range(10):
        h = sum(eq['horas_por_posicao'][10 * m:10 * m + 10])
        acum += h
        L.append(f"| {P['ranks.nomes'][m]} | {h:.1f} | {acum:.0f} | {fmt(res['custos_rank'][10 * m])} | "
                 f"{fmt(res['custos_rank'][10 * m + 9])} |")
    L += ['', '## Perfis', '']
    for nome, p in P['metas.perfis'].items():
        sem = eq['horas_total'] / (p['horas_dia'] * 7)
        ok = 'ok' if sem <= p['semanas_max'] + 0.5 else 'FORA DA META'
        L.append(f"- {nome} ({p['horas_dia']} h/dia): {sem:.1f} semanas (meta {p['semanas_min']} a {p['semanas_max']}) {ok}")
    L += ['', '## Minas', '', '| Mina | Money/bloco | Gemas/bloco | Renda típica money/h |', '|---|---|---|---|']
    for m, t in enumerate(res['minas'][:10]):
        L.append(f"| {t['mina']} | {fmt(t['money'])} | {fmt(t['gemas'])} | {fmt(mo.renda_ref(10 * m)[0])} |")
    v = res['minas'][10]
    L.append(f"| VIP | {fmt(v['money'])} | {fmt(v['gemas'])} | |")
    L += ['', '## Picareta no fim da 1a volta (jogador típico)', '',
          f"Picareta nível {eq['picareta_final']}. Compras de upgrade: {eq['compras']}. "
          f"Gasto na picareta: {fmt(eq['gasto_picareta'])} money; em rank: {fmt(eq['gasto_rank'])}.", '',
          '| Encantamento | Nível | Preço do nível 1 | Preço do nível 500 | Preço do nível 1000 |', '|---|---|---|---|---|']
    for e in NIVELADOS:
        p = res['precos_amostra'][e]
        L.append(f"| {NOME_ENC[e]} | {eq['niveis_final'][e]} | {fmt(p['1'][0])} + {fmt(p['1'][1])} gemas | "
                 f"{fmt(p['500'][0])} + {fmt(p['500'][1])} | {fmt(p['1000'][0])} + {fmt(p['1000'][1])} |")
    L += ['', '## Prestígio', '',
          'Fator de preço por prestígio: ' + ', '.join(f'{x:.2f}' for x in res['multiplicadores_prestigio'][1:]),
          'Horas de cada volta: ' + ', '.join(f'{x:.0f}' for x in res['prestigio_horas'][1:])]
    return '\n'.join(L) + '\n'


def gerar():
    res = json.loads((ECON / 'saida' / 'resultado.json').read_text(encoding='utf-8'))
    mo, P = Modelo(), Params()
    (ECON / 'saida' / 'o-que-medir.md').write_text(o_que_medir(P), encoding='utf-8')
    (ECON / 'saida' / 'numeros.md').write_text(numeros(res, mo, P), encoding='utf-8')


if __name__ == '__main__':
    gerar()
