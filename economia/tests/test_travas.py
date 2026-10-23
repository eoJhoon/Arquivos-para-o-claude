"""Travas da economia. Se alguma reprovar, a mudança em params/ quebrou alguma regra.

Cada teste diz em português o que deu errado, para o Enzo e o João entenderem sem abrir o código.
Rodar: dentro de economia/, `python -m pytest -q`
"""
import json
import math
import re
import sys
from pathlib import Path

import pytest
import yaml

ECON = Path(__file__).resolve().parents[1]
REPO = ECON.parent
sys.path.insert(0, str(ECON))

from sim.modelo import Modelo, AREA, NIVELADOS   # noqa: E402
from sim.params import Params                     # noqa: E402


@pytest.fixture(scope='session')
def mo():
    return Modelo()


@pytest.fixture(scope='session')
def res():
    arq = ECON / 'saida' / 'resultado.json'
    if not arq.exists():
        pytest.fail('Rode antes: python -m gen.gerar_tudo (dentro de economia/)')
    return json.loads(arq.read_text(encoding='utf-8'))


def carregar_yml(rel):
    return yaml.safe_load((REPO / rel).read_text(encoding='utf-8'))


# ------------------------------------------------------------------ parâmetros
def test_todo_parametro_tem_origem():
    P = Params()
    for k in P:
        m = P.meta(k)
        assert m['tipo'] in ('medido', 'decidido', 'hipotese'), f'{k}: tipo inválido'
        assert len(str(m['fonte'])) > 10, f'{k}: escreva de onde veio o número (fonte)'


# ------------------------------------------------------------------ duração
def test_ativo_termina_na_meta(res, mo):
    h = res['equilibrado']['horas_total']
    assert res['equilibrado']['chegou'], 'O jogador ativo não chegou no Dragão X'
    assert 220 <= h <= 240, f'Jogador ativo levou {h:.0f} h; a meta é 220 a 240 h'


def test_nenhuma_estrategia_muito_melhor(res):
    base = res['equilibrado']['horas_total']
    for nome in ('otimizado', 'ingenuo'):
        h = res[nome]['horas_total']
        assert h >= 0.90 * base, (f'A estratégia "{nome}" terminou em {h:.0f} h, mais de 10% antes do jogador '
                                  f'típico ({base:.0f} h). Alguma coisa ficou barata ou cara demais')


def test_perfis_na_meta(res, mo):
    h = res['equilibrado']['horas_total']
    for nome, p in mo.P['metas.perfis'].items():
        semanas = h / (p['horas_dia'] * 7)
        if nome == 'casual':
            continue  # conhecido: 1,5 h/dia dá ~21 semanas. Decisão pendente com o Enzo (ver relatório)
        assert semanas <= p['semanas_max'] + 0.5, f'Perfil {nome}: {semanas:.1f} semanas, meta até {p["semanas_max"]}'


def test_cada_rank_perto_do_tempo_alvo(res, mo):
    h = res['equilibrado']['horas_por_posicao']
    for m in range(10):
        real = sum(h[10 * m:10 * m + 10])
        alvo = sum(mo.alvo_h[10 * m:min(99, 10 * m + 10)])
        nome = mo.P['ranks.nomes'][m]
        assert abs(real / alvo - 1) < 0.10, f'{nome}: {real:.1f} h no rank, alvo {alvo:.1f} h'


# ------------------------------------------------------------------ picareta
def test_precos_nunca_caem(mo):
    for e in NIVELADOS:
        tab = mo.tabela_precos(e)
        for L in range(2, 1000):
            assert tab[L][0] >= tab[L - 1][0], f'{e}: nível {L + 1} mais barato que o {L}'


def test_chances_validas(mo):
    from gen.encantamentos import escala_da_faixa
    for e in AREA:
        for L in (1, 250, 500, 750, 1000):
            c = mo.chance_pct(e, L, escala_da_faixa(mo, L))
            assert 0 < c < 100, f'{e} nível {L}: chance {c}% fora do possível'


def test_sem_reacao_em_cadeia(mo):
    """Se bloco de área puder ativar encantamento, cada ativação gera chance x blocos ativações novas."""
    soma = sum(mo.area[e]['contribuicao'] for e in AREA)   # = soma de chance x blocos no nível 1000
    if mo.P['mineracao.area_dispara_outro_encantamento']:
        assert soma <= 0.3, f'Reação em cadeia: fator {soma:.2f} > 0,3 (a mina pode cair sozinha)'


def test_ativacoes_por_hora_razoaveis(mo):
    """Nenhum encantamento grande ativando o tempo todo (desempenho do servidor)."""
    from gen.encantamentos import escala_da_faixa
    for e in ('destruidor', 'nuclear', 'chuvaacida', 'trincheira'):
        por_h = mo.R * mo.chance_pct(e, 1000, escala_da_faixa(mo, 1000)) / 100
        assert por_h <= 30, f'{e} ativa {por_h:.0f} vezes por hora no máximo; pesado para o servidor'


# ------------------------------------------------------------------ ranks
def test_ranks_sobem(res):
    c = res['custos_rank'][:99]
    for s in range(1, 99):
        assert c[s] >= c[s - 1], f'Rank {s} mais barato que o anterior'


def test_ranks_yml_tem_100_ranks_e_prestigios(mo):
    d = carregar_yml('Rankup/ranks.yml')['rankup']
    assert len(d) == 100
    for k, v in d.items():
        assert '1' in v['prestigio'], f'{k}: sem a primeira volta'


# ------------------------------------------------------------------ caixas
def test_caixas_somam_100():
    cx = carregar_yml('Caixas/caixas.yml')['caixa']
    for nome, c in cx.items():
        soma = sum(float(str(x).split('\\')[-3]) for x in c['itens'])
        assert abs(soma - 100) < 0.01, f'Caixa {nome}: chances somam {soma:.2f}%'


def test_cadeia_de_chaves_termina(res):
    for caixa, saidas in res['caixas']['cadeia'].items():
        assert sum(saidas.values()) < 0.5, f'Caixa {caixa} devolve {sum(saidas.values()):.2f} chaves por abertura'


# ------------------------------------------------------------------ agricultura e automação
def test_especialidade_das_plantacoes(res):
    b = res['agricultura']['base']
    money_h = {k: v['money'] * v['quebras_h'] for k, v in b.items()}
    sem_h = {k: v['sementes'] * v['quebras_h'] for k, v in b.items()}
    assert max(money_h, key=money_h.get) == 'fungo', 'Fungo precisa ser a melhor em money'
    assert max(sem_h, key=sem_h.get) == 'melancia', 'Melancia precisa ser a melhor em sementes'
    assert money_h['cana'] < money_h['fungo'] and sem_h['cana'] < sem_h['melancia'], 'Cana não pode ganhar nas duas'


def test_sem_lucro_comprando_e_revendendo(res):
    ag = res['agricultura']
    fator_max = 1 + ag['lucro_pct']['9'] / 100
    for k, preco_loja in ag['loja_preco_unidade'].items():
        venda_max = ag['base'][k]['money'] * fator_max
        assert preco_loja > venda_max, f'{k}: comprar na loja e vender no armazém dá lucro'


def test_afk_nao_passa_o_ativo(res):
    for n in res['cacto']['niveis']:
        assert n['vs_mina_pct'] <= 15, f'Cacto nível {n["nivel"]}: AFK rende {n["vs_mina_pct"]}% da mina'


# ------------------------------------------------------------------ configs coerentes com os parâmetros
def test_minas_no_config(mo):
    b = carregar_yml('MinaReset/blocos.yml')['blocos']
    assert b['STAINED_CLAY']['9']['rank1']['moeda']['money']['quantia'] == mo.mina_money(0)
    assert b['REDSTONE_BLOCK']['0']['rank10']['moeda']['money']['quantia'] == mo.mina_money(9)
    vip = b['EMERALD_BLOCK']['0']['vip']['moeda']['money']['quantia']
    assert vip == mo.mina_money(0) * mo.P['minas.vip_multiplicador_da_mina_cidadao']


def test_encantamentos_no_config(mo):
    e = carregar_yml('Encantamentos/encantamentos.yml')['encantamentos']
    assert len(e['Explosivo']['efeito']) == 1, 'Chance deve ter 1 faixa só (formato do Enzo)'
    assert len(e['booster_money']['upgrade']) == len(mo.P['design.faixas_preco'])
    b = e['booster_money']['booster']['1-1000']
    assert math.isclose(b['quantidade'] + b['aumento-por-nivel'] * 999, 1000 * mo.P['picareta.fortuna_pct_por_nivel'])


def test_faixas_batem_com_o_simulador(mo):
    """O preço de cada nível calculado pelas faixas (como o plugin faz) é o mesmo que o simulador usou."""
    for e in NIVELADOS:
        tab = mo.tabela_precos(e)
        for a, b, cm, am, cg, ag in mo.faixas_preco(e):
            for n in range(a, b + 1):
                assert tab[n] == (cm + am * (n - a), cg + ag * (n - a)), f'{e} nível {n}'
