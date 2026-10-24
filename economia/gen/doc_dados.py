"""Junta todos os números para o documento de preços (economia/saida/doc_dados.json).

Tudo vem do mesmo modelo que o simulador usou. No fim confere as contas (soma das caixas,
faixas de preço contra o simulador, preços sempre subindo).
"""
import json
import re
import sys
from pathlib import Path

ECON = Path(__file__).resolve().parents[1]
if str(ECON) not in sys.path:
    sys.path.insert(0, str(ECON))

from sim.modelo import Modelo, AREA, BOOST, FIXOS, CHAVE_PLUGIN   # noqa: E402
from sim import sistemas as S                                     # noqa: E402
from gen.planilha import NOME_ENC, nome_pos                       # noqa: E402
from gen.comum import ler                                         # noqa: E402

BS = '\\'


def nome_item(txt):
    t = re.sub(r'\[L\].*?\[L\]|\[URL\].*?\[URL\]|\[VALUE\].*?\[VALUE\]|\[KEY\].*?\[KEY\]|\[P\].*?\[P\]', '', str(txt))
    m = re.search(r'\[N\]\{(.*?)\}\[N\]', t)
    nome = re.sub(r'&.', '', m.group(1)) if m else ''
    partes = t.split(BS)
    ident, qtd = partes[0], partes[1] if len(partes) > 1 else '1'
    ench = re.search(r'\[E\]\{(.*?)\}\[E\]', t)
    if not nome:
        nome = {'3:0': 'Azar (nada)', '384:0': 'Frasco de XP', '264:0': 'Diamante', '322:1': 'Maçã dourada encantada',
                '373:8233': 'Poção de força', '373:8226': 'Poção de velocidade', '81:0': 'Cacto', '372:0': 'Fungo',
                '12:0': 'Areia', '88:0': 'Areia das almas', '287:0': 'Linha', '338:0': 'Cana', '362:0': 'Semente de melancia',
                '310:0': 'Capacete de diamante', '311:0': 'Peitoral de diamante', '312:0': 'Calça de diamante',
                '313:0': 'Bota de diamante', '278:0': 'Picareta de diamante', '277:0': 'Pá de diamante',
                '279:0': 'Machado de diamante', '293:0': 'Enxada de diamante', '276:0': 'Espada de diamante'}.get(ident, ident)
    if 'cheque' in str(txt):
        import base64
        try:
            b = re.search(r'cheque☢([A-Za-z0-9+/=]+)', str(txt)).group(1)
            j = json.loads(base64.b64decode(b))
            nome = f"Cheque {j['tipo']} {j['quantidade']:g}"
        except Exception:
            nome = 'Cheque'
    if ench:
        nome += f' (encant. {ench.group(1)})'
    if qtd not in ('1', '@qnt') and not qtd.startswith('['):
        nome = f'{qtd}x {nome}'
    return nome


def gerar():
    res = json.loads((ECON / 'saida' / 'resultado.json').read_text(encoding='utf-8'))
    mo = Modelo()
    P = mo.P
    d = {}
    eq = res['equilibrado']

    d['resumo'] = {'horas_ativo': eq['horas_total'], 'horas_otim': res['otimizado']['horas_total'],
                   'horas_rush': res['ingenuo']['horas_total'],
                   'semanas': {k: round(eq['horas_total'] / (p['horas_dia'] * 7), 1) for k, p in P['metas.perfis'].items()},
                   'prestigio_horas': [round(x, 1) for x in res['prestigio_horas'][1:]],
                   'niveis_fim': {NOME_ENC[e]: v for e, v in eq['niveis_final'].items()}}

    d['ranks'] = []
    acum = 0
    for s in range(100):
        h = eq['horas_por_posicao'][s] if s < len(eq['horas_por_posicao']) else None
        acum += h or 0
        d['ranks'].append({'rank': nome_pos(mo, s), 'chave': 'default' if s == 0 else f'rank{s}',
                           'preco': int(res['custos_rank'][s]), 'horas': h, 'acum': acum if h else None})

    d['minas'] = [{'mina': f'{t["mina"]} (rank{m + 1})' if m < 10 else 'VIP', 'bloco': t['bloco'],
                   'money': t['money'], 'gemas': t['gemas'], 'chave_pct': P['design.chance_chave_pct']}
                  for m, t in enumerate(res['minas'])]
    d['exp'] = res['exp_por_bloco']

    enc = ler('Encantamentos/encantamentos.yml')['encantamentos']
    d['area'] = []
    for e in AREA:
        f = next(iter(enc[e]['efeito'].values()))
        d['area'].append({'nome': NOME_ENC[e], 'chave': e, 'chance': f['chance'], 'aumento': f['aumento-por-nivel'],
                          'radios': str(f.get('radios', '-')), 'libera': mo.libera(e),
                          'chance_1000': round(f['chance'] * 1000, 6),
                          'ativ_h_1000': round(mo.R * f['chance'] * 1000 / 100, 2)})
    d['boost'] = []
    for e in BOOST:
        b = next(iter(enc[CHAVE_PLUGIN[e]]['booster'].values()))
        d['boost'].append({'nome': NOME_ENC[e], 'chave': CHAVE_PLUGIN[e], 'quantidade': b['quantidade'],
                           'aumento': b['aumento-por-nivel'], 'no_1000': round(b['quantidade'] * 1000, 1)})
    d['precos'] = {}
    for e in BOOST + AREA:
        d['precos'][NOME_ENC[e] + f' ({CHAVE_PLUGIN.get(e, e)})'] = [
            {'faixa': f'{a}-{b}', 'money': cm, 'aum_money': am, 'gemas': cg, 'aum_gemas': ag}
            for a, b, cm, am, cg, ag in mo.faixas_preco(e)]
    d['fixos'] = [{'nome': NOME_ENC[e], 'nivel': L, 'faixa': f'{L - 1}-{L - 1}',
                   'money': mo.preco(e, L)[0], 'gemas': mo.preco(e, L)[1]} for e in FIXOS for L in (1, 2)]
    d['skins'] = res['skins']

    ag = res['agricultura']
    d['plantas'] = [{'nome': k.capitalize(), 'libera': nome_pos(mo, b['libera_rank']), 'money': b['money'],
                     'sementes': b['sementes'], 'compra': ag['implantacao'][k], 'loja': ag['loja_preco_unidade'][k],
                     'por_hora': b['quebras_h']} for k, b in ag['base'].items()]
    d['plantas'].append({'nome': 'Cacto', 'libera': nome_pos(mo, P['plantacoes']['cacto']['libera_rank']),
                         'money': res['cacto']['preco_unidade'],
                         'sementes': P['plantacoes']['cacto']['sementes_por_unidade'], 'compra': None, 'loja': None,
                         'por_hora': None})
    d['lucro'] = [{'rank': P['ranks.nomes'][m], 'grupos': f'rank{10 * m}' if m else 'default',
                   'lucro': ag['lucro_pct'][str(m)] if isinstance(next(iter(ag['lucro_pct'])), str) else ag['lucro_pct'][m]}
                  for m in range(2, 10)]
    d['cacto'] = res['cacto']['niveis']
    d['armazem'] = {'inicial': res['armazem']['capacidade_inicial'], 'por_item': res['armazem']['por_item'],
                    'maximo': res['armazem']['maximo'],
                    'chance_item': P['plantacoes']['cenoura']['chance_item_pct'],
                    'itens_h': round(ag['item_cenoura_por_hora'], 1)}
    sp = res['spawners']
    d['spawners'] = [{'nome': t['nome'], 'libera': t['libera'], 'preco': t['preco_money'],
                      'almas_cabeca': t['almas_por_cabeca'], 'almas_h': t['almas_h_por_spawner']} for t in sp['tipos']]
    d['limite_spawners'] = sp['limite_por_rank']
    d['matadoras'] = res['matadoras']
    d['bosses'] = [{**b, 'nome': bc['nome'], 'chave_config': bc['chave'], 'limite': bc['limite_armazem'],
                    'stack': bc['stack_spawner'], 'chave_caixa': bc['chave_caixa']}
                   for b, bc in zip(res['bosses'], res['bosses_config'])]
    cx = ler('Caixas/caixas.yml')['caixa']
    d['caixas'] = {}
    for nome, c in cx.items():
        d['caixas'][nome] = [{'item': nome_item(x), 'chance': float(str(x).split(BS)[-3])} for x in c['itens']]
    d['requisitos'] = res.get('requisitos_rank', [])

    # ------------------------------------------------------------ conferência
    erros = []
    for nome, itens in d['caixas'].items():
        soma = sum(i['chance'] for i in itens)
        if abs(soma - 100) > 0.01:
            erros.append(f'caixa {nome} soma {soma}')
    for e in BOOST + AREA:
        tab = mo.tabela_precos(e)
        for (a, b, cm, am, cg, ag_), in zip(mo.faixas_preco(e)):
            if tab[b] != (cm + am * (b - a), cg + ag_ * (b - a)):
                erros.append(f'{e} faixa {a}-{b}')
        for n in range(2, 1000):
            if tab[n][0] < tab[n - 1][0] or tab[n][1] < tab[n - 1][1]:
                erros.append(f'{e} nível {n} mais barato')
                break
    for i in range(1, 99):
        if d['ranks'][i]['preco'] < d['ranks'][i - 1]['preco']:
            erros.append(f'rank {i} mais barato')
    d['conferencia'] = erros
    (ECON / 'saida' / 'doc_dados.json').write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    return d


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    d = gerar()
    print('conferência:', d['conferencia'] or 'tudo certo')
