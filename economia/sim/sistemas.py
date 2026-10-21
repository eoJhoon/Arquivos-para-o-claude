"""Sistemas fora da mina: agricultura, cacto, armazém, spawners, almas, Matadoras, bosses, fragmentos.

Régua de tudo: renda de referência da mina, I(s) = money por hora que um jogador típico faz
minerando na posição s. Quando um preço é "2 h de renda", quer dizer 2 x I(s) no rank em que o
sistema libera. Assim tudo acompanha a inflação natural do jogo sem número escolhido à mão.
"""
from .modelo import Modelo, arred

NOMES_RANK = None


def nome_posicao(mo: Modelo, s):
    romanos = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
    return f"{mo.P['ranks.nomes'][s // 10]} {romanos[s % 10]}"


def I(mo, s):
    return mo.renda_ref(s)[0]


# ------------------------------------------------------------------ agricultura
def agricultura(mo: Modelo):
    """Preço de venda base por unidade e bônus de lucro por rank (permissão armazem.lucro.money@X).

    Preço base calibrado em Guerreiro V (s=25). Em cada rank a renda da mina cresce, e o lucro
    por permissão sobe junto, mantendo cada plantação na mesma proporção da mina.
    """
    pl = mo.P['plantacoes']
    hora = {'fungo': mo.P['agricultura.fungo_quebras_por_hora'],
            'cenoura': mo.P['servidor.cenoura_quebras_por_hora'],
            'melancia': mo.P['servidor.melancia_quebras_por_hora'],
            'cana': mo.P['servidor.cana_quebras_por_hora']}
    s_ref = 25
    base = {}
    for k, q in hora.items():
        base[k] = {
            'money': arred(pl[k]['money_vs_mina'] * I(mo, s_ref) / q, 3),
            'sementes': pl[k]['sementes_por_unidade'],
            'quebras_h': q,
            'libera_rank': pl[k]['libera_rank'],
        }
    lucro = {}
    for m in range(10):
        fator = I(mo, 10 * m + 5) / I(mo, s_ref)
        lucro[m] = max(0, round(100 * (fator - 1)))
    tabela = []
    for m in range(2, 10):
        f = 1 + lucro[m] / 100
        linha = {'rank': mo.P['ranks.nomes'][m], 'lucro_pct': lucro[m], 'mina_money_h': I(mo, 10 * m + 5)}
        for k, b in base.items():
            liberado = 10 * m + 9 >= b['libera_rank']
            linha[f'{k}_money_h'] = b['money'] * f * b['quebras_h'] if liberado else 0
            linha[f'{k}_sementes_h'] = b['sementes'] * b['quebras_h'] if liberado else 0
        tabela.append(linha)
    # implantação: compra única (decisão do Enzo), em horas de renda no rank em que libera
    horas_impl = {'fungo': 2, 'cenoura': 2, 'melancia': 3, 'cana': 3}
    implantacao = {k: arred(horas_impl[k] * I(mo, base[k]['libera_rank'])) for k in base}
    # loja: vender para o jogador por 3x o maior preço de venda possível (Dragão), sem lucro na revenda
    f_max = 1 + lucro[9] / 100
    loja = {k: arred(3 * base[k]['money'] * f_max) for k in base}
    item_cenoura_h = hora['cenoura'] * pl['cenoura']['chance_item_pct'] / 100
    return {'base': base, 'lucro_pct': lucro, 'tabela': tabela, 'implantacao': implantacao,
            'loja_preco_unidade': loja, 'item_cenoura_por_hora': item_cenoura_h, 's_ref': s_ref}


def cacto(mo: Modelo, agro):
    """Cacto automático: 10 níveis (quantidade de cactos). No máximo rende 10% da mina por hora."""
    pl = mo.P['plantacoes']['cacto']
    por_cacto_h = mo.P['agricultura.cacto_por_segundo_por_planta'] * 3600
    quantidades = [50, 100, 200, 300, 400, 500, 600, 700, 850, 1000]
    s_ref = agro['s_ref']
    preco_unid = arred(pl['money_vs_mina_por_hora_max'] * I(mo, s_ref) / (por_cacto_h * quantidades[-1]), 3)
    niveis = []
    ant = 0
    for k, q in enumerate(quantidades, 1):
        s = min(99, pl['libera_rank'] + 6 * (k - 1))
        f = 1 + agro['lucro_pct'][s // 10] / 100
        renda_h = q * por_cacto_h * preco_unid * f
        ganho_h = (q - ant) * por_cacto_h * preco_unid * f
        payback = 12 + 2 * k   # horas de AFK para o nível se pagar (14 a 32 h)
        niveis.append({'nivel': k, 'cactos': q, 'libera': nome_posicao(mo, s), 'money_h': renda_h,
                       'sementes_h': q * por_cacto_h * pl['sementes_por_unidade'],
                       'custo_money': arred(ganho_h * payback),
                       'custo_sementes': arred(2 * k * agro['base']['melancia']['quebras_h'] * 1.0),
                       'retorno_horas': payback,
                       'vs_mina_pct': round(100 * renda_h / I(mo, s), 1)})
        ant = q
    horas_afk = mo.P['armazem']['horas_afk_maximas']
    return {'por_cacto_h': por_cacto_h, 'preco_unidade': preco_unid, 'niveis': niveis,
            'capacidade_para_afk_max': int(quantidades[-1] * por_cacto_h * horas_afk)}


def armazem(mo: Modelo, agro, cac):
    a = mo.P['armazem']
    cap = a['capacidade_inicial']
    marcos = []
    for alvo_cactos in [n['cactos'] for n in cac['niveis']]:
        precisa = alvo_cactos * cac['por_cacto_h'] * a['horas_afk_maximas']
        itens = max(0, (precisa - cap) // a['item_cenoura_capacidade'] + 1)
        marcos.append({'cactos': alvo_cactos, 'capacidade_para_8h': int(precisa),
                       'itens_cenoura': int(itens),
                       'horas_de_cenoura': round(itens / agro['item_cenoura_por_hora'], 1)})
    return {'capacidade_inicial': cap, 'por_item': a['item_cenoura_capacidade'],
            'maximo': a['capacidade_maxima'],
            'itens_ate_o_maximo': (a['capacidade_maxima'] - cap) // a['item_cenoura_capacidade'],
            'marcos': marcos}


# ------------------------------------------------------------------ combate
SPAWNER_LIBERA = {'COW': 30, 'PIG': 40, 'ZOMBIE': 50, 'SKELETON': 60, 'IRON_GOLEM': 70}
SPAWNER_NOME = {'COW': 'Vaca', 'PIG': 'Porco', 'ZOMBIE': 'Zumbi', 'SKELETON': 'Esqueleto', 'IRON_GOLEM': 'Golem'}
ALMAS_POR_CABECA = {'COW': 1, 'PIG': 2.5, 'ZOMBIE': 6, 'SKELETON': 15, 'IRON_GOLEM': 40}


def spawners(mo: Modelo):
    por_spawner_h = 3600 / mo.P['spawners.tempo_spawn_segundos'] * mo.P['servidor.mobs_por_spawn_por_spawner'] \
        * mo.P['spawners.cabecas_por_morte_sem_pilhagem']
    limites = mo.P['combate']['limite_spawners']
    tipos = []
    for t, s in SPAWNER_LIBERA.items():
        tipos.append({'tipo': t, 'nome': SPAWNER_NOME[t], 'libera': nome_posicao(mo, s), 's': s,
                      'preco_money': arred(1.5 * I(mo, s)),
                      'cabecas_h': por_spawner_h, 'almas_por_cabeca': ALMAS_POR_CABECA[t],
                      'almas_h_por_spawner': por_spawner_h * ALMAS_POR_CABECA[t]})
    # limite de spawners por rank (Tritão I em diante), via itens "Stack de Spawners"
    lim_rank = {}
    for m in range(3, 10):
        lim_rank[mo.P['ranks.nomes'][m]] = limites[min(len(limites) - 1, (m - 3) * len(limites) // 7 + 1)]
    return {'cabecas_h_por_spawner': por_spawner_h, 'tipos': tipos, 'limite_por_rank': lim_rank}


def almas_h(mo, s, spw):
    """Almas por hora de um jogador típico na posição s (melhor spawner liberado x limite)."""
    melhor = None
    for t in spw['tipos']:
        if s >= t['s']:
            melhor = t
    if not melhor:
        return 0.0
    m = s // 10
    lim = spw['limite_por_rank'].get(mo.P['ranks.nomes'][m], 1)
    return melhor['almas_h_por_spawner'] * lim


def requisitos_rank(mo: Modelo, spw, bosses):
    """Itens exigidos nos ranks V e X a partir do Tritão (além do money). Impede subir só com money AFK.

    Cabeças: 2 h (V) ou 4 h (X) de produção do melhor spawner liberado, com o limite do rank.
    Cabeça de boss: do boss mais forte liberado, 1 (V) ou 3 (X).
    Fragmento de Mineração (só cai minerando): a partir do Avatar.
    """
    out = []
    for s in range(30, 99):
        if s % 10 not in (4, 9):
            continue
        m = s // 10
        x = s % 10 == 9
        spawner = None
        for t in spw['tipos']:
            if s >= t['s']:
                spawner = t
        lim = spw['limite_por_rank'].get(mo.P['ranks.nomes'][m], 1)
        horas = 4 if x else 2
        req = {'posicao': nome_posicao(mo, s), 's': s}
        if spawner:
            req['cabecas'] = f"{arred(horas * spawner['cabecas_h'] * lim, 2)} Cabeças de {spawner['nome']}"
        b_ok = [b for b in bosses if s >= 35 + 6 * (b['boss'] - 1)]
        if b_ok:
            req['boss'] = f"{3 if x else 1} Cabeça do boss {b_ok[-1]['boss']}"
        if m >= 6:
            req['fragmentos'] = f"{(4 if x else 2) * (m - 5)} Fragmentos de Mineração"
        out.append(req)
    return out


def matadoras_e_bosses(mo: Modelo, spw):
    c = mo.P['combate']
    gps = mo.P['servidor.golpes_por_segundo']
    mats, bosses = [], []
    for k in range(10):
        s = 35 + 6 * k   # Matadora k libera em Tritão V (k=0) até Dragão I
        s = min(98, s)
        a_h = max(1.0, almas_h(mo, s, spw))
        mats.append({'matadora': k + 1, 'dano': c['matadora_dano'][k], 'libera': nome_posicao(mo, s),
                     'preco_money': arred(3 * I(mo, s)),
                     'preco_almas': arred(4 * a_h),
                     'fragmentos_arena': [0, 0, 0, 0, 0, 0, 0, 0, 10, 30][k],
                     'exige_matadora_anterior': k > 0})
        vida = c['matadora_dano'][k] * gps * c['luta_segundos'][k]
        bosses.append({'boss': k + 1, 'vida': int(vida), 'luta_s': c['luta_segundos'][k],
                       'matadora': k + 1, 'cooldown_h': c['boss_cooldown_horas'][k],
                       'invocar_almas': arred(1 * a_h),
                       'libera': nome_posicao(mo, s)})
    return mats, bosses
