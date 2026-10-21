"""Geradores dos demais plugins: picareta evolutiva, minas, armazém, spawners, bosses e caixas."""
import re

from sim import sistemas as S
from sim.modelo import arred
from .comum import ler, escrever, mapa

BS = '\\'

# ------------------------------------------------------------------ Encantamentos/evolutivos.yml
BLOCO_DA_MINA = ['STAINED_CLAY', 'STAINED_CLAY', 'COBBLESTONE', 'LAPIS_BLOCK', 'PRISMARINE', 'GOLD_BLOCK',
                 'IRON_BLOCK', 'QUARTZ_BLOCK', 'COAL_BLOCK', 'REDSTONE_BLOCK']


def skins(mo):
    """Bônus de money das skins da picareta (%) e preço pelo retorno em horas."""
    bonus = [0, 3, 6, 9, 12]
    s_skin = [0, 10, 30, 50, 70]
    out = []
    for k, (b, s) in enumerate(zip(bonus, s_skin), 1):
        rm, _ = mo.renda_ref(s)
        preco = arred(b / 100 * rm * mo.payback(mo.tau(s))) if b else 0
        out.append({'skin': k, 'bonus_pct': b, 'preco_money': preco, 'posicao': s})
    return out


def _lore_skin(texto, bonus):
    texto = re.sub(r'Dinheiro: &a\+\d+%', f'Dinheiro: &a+{bonus}%', texto)
    texto = re.sub(r'\|\|&f ✦ Gemas: &a\+\d+%', '', texto)
    texto = re.sub(r'\|\| \|\|&d&lPODER ESPECIAL:.*?\)\.', '', texto)
    return texto


def evolutivos(mo, pasta=None):
    arq = 'Encantamentos/evolutivos.yml'
    d = ler(arq)
    itens = d['itensevolutivos']
    pic = itens['picareta']
    exp = mo.exp_por_bloco()
    novo = {}
    for m, bloco in enumerate(BLOCO_DA_MINA):
        novo.setdefault(bloco, []).append(exp[m])
    ie = pic['exp-base']['itens-exp']
    for k in list(ie.keys()):
        del ie[k]
    for bloco, vals in novo.items():
        ie[bloco] = round(sum(vals) / len(vals), 2)
    ie['EMERALD_BLOCK'] = exp[0]          # mina VIP
    pic['menu-evolutivo']['itens'] = [x for x in pic['menu-evolutivo']['itens'] if '\\booster_prisma\\' not in str(x)]
    for parte in ('bota', 'calça', 'peito', 'capacete'):
        mn = itens[parte]['menu-evolutivo']
        mn['itens'] = [x for x in mn['itens'] if '\\booster_money\\' not in str(x)]
    tab = skins(mo)
    for i, sk in enumerate(tab, 1):
        alvo = pic['skins'][f'skin-{i}']
        alvo['bonus'] = mapa(money=sk['bonus_pct']) if sk['bonus_pct'] else mapa()
        alvo['custo'] = mapa(money=sk['preco_money']) if sk['preco_money'] else mapa()
        alvo['item-menu'] = _lore_skin(str(alvo['item-menu']), sk['bonus_pct'])
    if 'skins' in itens['capacete']:
        for i in range(1, 6):
            sk = itens['capacete']['skins'].get(f'skin-{i}')
            if sk is not None:
                sk['bonus'] = mapa()   # skins do capacete: só visual (booster de money fora, decisão do Enzo)
                sk['item-menu'] = re.sub(r'\|\|&f ✦ Dinheiro: &a\+\d+%', '', _lore_skin(str(sk['item-menu']), 0))
    escrever(arq, d, pasta)
    return {'exp_por_bloco': dict(ie), 'skins': tab}


# ------------------------------------------------------------------ MinaReset/blocos.yml
def _troca_chance(drop, chance):
    p = str(drop).split(BS)
    p[-3] = f'{chance:g}'
    return BS.join(p)


def minas(mo, pasta=None):
    arq = 'MinaReset/blocos.yml'
    d = ler(arq)
    b = d['blocos']
    chave_pct = mo.P['design.chance_chave_pct']
    alvo = [('STAINED_CLAY', '9', 'rank1'), ('STAINED_CLAY', '13', 'rank2'), ('COBBLESTONE', '0', 'rank3'),
            ('LAPIS_BLOCK', '0', 'rank4'), ('PRISMARINE', '0', 'rank5'), ('GOLD_BLOCK', '0', 'rank6'),
            ('IRON_BLOCK', '0', 'rank7'), ('QUARTZ_BLOCK', '0', 'rank8'), ('COAL_BLOCK', '0', 'rank9'),
            ('REDSTONE_BLOCK', '0', 'rank10')]
    modelo_chave = str(b['STAINED_CLAY']['9']['rank1']['drops'][0])
    tabela = []
    for m, (bloco, dado, mina) in enumerate(alvo):
        e = b[bloco][dado][mina]
        e['moeda']['money']['quantia'] = float(mo.mina_money(m))
        e['moeda']['gemas']['quantia'] = float(mo.mina_gemas(m))
        drops = list(e.get('drops') or [])
        drops = [x for x in drops if 'chave' not in str(x)]
        drops.insert(0, _troca_chance(modelo_chave, chave_pct))
        e['drops'] = drops
        tabela.append({'mina': mo.P['ranks.nomes'][m], 'bloco': bloco, 'money': mo.mina_money(m),
                       'gemas': mo.mina_gemas(m), 'chave_pct': chave_pct})
    vip = b['EMERALD_BLOCK']['0']['vip']
    mult = mo.P['minas.vip_multiplicador_da_mina_cidadao']
    vip['moeda'] = {'money': {'quantia': float(mo.mina_money(0) * mult), 'chance': 100.0, 'fortunefunciona': False},
                    'gemas': {'quantia': float(mo.mina_gemas(0) * mult), 'chance': 100.0, 'funcionafortuna': False}}
    vip['moeda-tipo-msg'] = 'actionbar'
    vip['moeda-mensagem'] = '@formatmensagem'
    vip['drops'] = [_troca_chance(x, chave_pct) if 'chave' in str(x) else x for x in vip['drops']]
    tabela.append({'mina': 'VIP', 'bloco': 'EMERALD_BLOCK', 'money': mo.mina_money(0) * mult,
                   'gemas': mo.mina_gemas(0) * mult, 'chave_pct': chave_pct})
    escrever(arq, d, pasta)
    return tabela


# ------------------------------------------------------------------ Armazem/armazem.yml
CABECA = {'vaca': 'COW', 'porco': 'PIG', 'zumbi': 'ZOMBIE', 'esqueleto': 'SKELETON', 'golem': 'IRON_GOLEM'}


def armazem(mo, agro, cac, pasta=None):
    arq = 'Armazem/armazem.yml'
    d = ler(arq)
    pl = d['categorias']['plantações']['itens']['1']
    for k in ('fungo', 'cenoura', 'melancia', 'cana'):
        pl[k]['moedas']['money'] = float(agro['base'][k]['money'])
        pl[k]['moedas']['sementes'] = float(agro['base'][k]['sementes'])
    pl['cacto']['moedas']['money'] = float(cac['preco_unidade'])
    pl['cacto']['moedas']['sementes'] = float(mo.P['plantacoes']['cacto']['sementes_por_unidade'])
    sp = d['categorias']['spawners']['itens']['1']
    for k, mob in CABECA.items():
        sp[k]['moedas']['money'] = 0.0
        sp[k]['moedas']['almas'] = float(S.ALMAS_POR_CABECA[mob])
    escrever(arq, d, pasta)
    return {k: (sp[k]['id'], sp[k]['idautomatizacao']) for k in CABECA}


def comandos_luckperms(mo, agro):
    """Comandos para colar no console: lucro do armazém por rank e liberação das plantações."""
    linhas = ['# Cole no console do servidor. Gerado por economia/gen. Não editar à mão.',
              '# 1) lucro do armazém por rank (preço da plantação acompanha a mina)']
    grupos = ['default'] + [f'rank{i}' for i in range(1, 100)]
    for s, g in enumerate(grupos):
        lucro = agro['lucro_pct'][s // 10]
        if lucro > 0:
            linhas.append(f'lp group {g} permission set armazem.lucro.money@{lucro}.0 true')
    linhas.append('# 2) liberar a colheita de cada plantação no rank certo')
    perm = {'fungo': 'nether_warts.use', 'cenoura': 'carrot.use', 'melancia': 'melon_steam.use',
            'cana': 'sugar_cane_block.use', 'cacto': 'cactus.use'}
    for k, p in perm.items():
        s0 = mo.P['plantacoes'][k]['libera_rank']
        for s in range(s0, 100):
            linhas.append(f'lp group {grupos[s]} permission set {p} true')
    linhas.append('# 3) depois de colar tudo: em Armazem/config.yml troque permissao-para-plantar-e-quebrar para true')
    return '\n'.join(linhas) + '\n'


# ------------------------------------------------------------------ Spawners/mobs.yml
def spawners(mo, ids_cabeca, pasta=None):
    arq = 'Spawners/mobs.yml'
    d = ler(arq)
    mobs = d['mobs']
    for nome, mob in CABECA.items():
        cabeca_id = str(ids_cabeca[nome][1])
        tipo, resto = cabeca_id.split(BS, 1)
        item = f'{tipo}{BS}@qnt{BS}{resto}{BS}100.0{BS}armazem'
        mobs[mob]['itens'] = [item]
        if 'moedas' in mobs[mob]:
            del mobs[mob]['moedas']
    escrever(arq, d, pasta)
    cfg = ler('Spawners/config.yml')
    cfg['stack-por-player'] = True
    cfg['max-stack-spawners'] = float(mo.P['combate']['limite_spawners'][-1])
    escrever('Spawners/config.yml', cfg, pasta)


# ------------------------------------------------------------------ Bosses/bosses.yml
def _troca_qtd(drop, chave, n):
    s = str(drop)
    s = re.sub(r'Quantidade: &a\+\d+', f'Quantidade: &a+{n}', s)
    s = re.sub(rf'\{{{chave}☢\d+\}}', f'{{{chave}☢{n}}}', s)
    return s


def bosses(mo, tab_bosses, chaves_caixa, pasta=None):
    arq = 'Bosses/bosses.yml'
    d = ler(arq)
    bs = d['bosses']
    ordem = sorted(bs.keys(), key=lambda k: int(re.match(r'\d+', k).group()))
    modelo = bs['5vaca']['drops']
    m_limite = next(str(x) for x in modelo if 'limitearmazem' in str(x))
    m_stack = next(str(x) for x in modelo if 'stack-spawner' in str(x))
    lim = [20, 30, 40, 50, 60, 80, 100, 120, 150, 200]
    stk = [1, 1, 1, 1, 2, 2, 2, 4, 4, 4]
    chave_por_boss = [None, None, 'magica', 'magica', 'magica', 'magica', 'magma', 'magma', 'draconica', 'draconica']
    for i, k in enumerate(ordem):
        b = bs[k]
        b['vida'] = float(tab_bosses[i]['vida'])
        drops = [str(x) for x in (b.get('drops') or [])]
        drops = [x for x in drops if 'limitearmazem' not in x and 'stack-spawner' not in x and 'chave' not in x]
        # cabeça do boss (usada no rankup): sempre cai
        drops = [re.sub(r'\\[\d.]+$', r'\\100.0', x) if 'utilizado para várias' in x else x for x in drops]
        drops.append(_troca_qtd(m_limite, 'limitearmazem', lim[i]))
        drops.append(_troca_qtd(m_stack, 'stack-spawner', stk[i]))
        ck = chave_por_boss[i]
        if ck:
            drops.append(chaves_caixa[ck] + BS + '20.0')
        b['drops'] = drops
    escrever(arq, d, pasta)
    return [{'boss': i + 1, 'chave': ordem[i], 'nome': re.sub('§.', '', str(bs[ordem[i]]['nome'])),
             'vida': tab_bosses[i]['vida'], 'limite_armazem': lim[i], 'stack_spawner': stk[i],
             'chave_caixa': chave_por_boss[i]} for i in range(len(ordem))]


# ------------------------------------------------------------------ Caixas/caixas.yml
def _partes_item(s):
    p = str(s).split(BS)
    return p[:-3], float(p[-3]), p[-2], p[-1]


def caixas(mo, pasta=None):
    """Normaliza as chances para somar 100%, corrige a chave da Mineração e mede a cadeia de chaves."""
    arq = 'Caixas/caixas.yml'
    d = ler(arq)
    cx = d['caixa']
    cx['mineracao']['item-chave'] = str(cx['mineracao']['item-chave']).replace('chave☢vip', 'chave☢mineracao')
    chaves = {}
    resumo = {}
    for nome, c in cx.items():
        itens = [str(x) for x in c['itens']]
        total = sum(_partes_item(x)[1] for x in itens)
        novos, tabela = [], []
        for x in itens:
            corpo, ch, a, b = _partes_item(x)
            nova = round(100 * ch / total, 4)
            novos.append(BS.join(corpo + [f'{nova:g}', a, b]))
            tabela.append((re.sub(r'&.', '', re.sub(r'\[L\].*?\[L\]|\[URL\].*?\[URL\]', '', BS.join(corpo)))[:70], nova))
            m = re.search(r'\{chave☢(\w+)\}', x)
            if m and x.startswith('131'):
                chaves.setdefault(m.group(1), BS.join(corpo))
        soma = sum(t[1] for t in tabela)
        if abs(soma - 100) > 1e-6:
            corpo, ch, a, b = _partes_item(novos[-1])
            ajuste = round(ch + 100 - soma, 4)
            novos[-1] = BS.join(corpo + [f'{ajuste:g}', a, b])
            tabela[-1] = (tabela[-1][0], ajuste)
        c['itens'] = novos
        resumo[nome] = tabela
    # cadeia de chaves: quantas chaves de cada caixa saem, em média, ao abrir uma caixa
    caixa_da_chave = {'mineracao': 'mineracao', 'vip': 'vip', 'farm': 'farm', 'magica': 'magica',
                      'magma': 'magma', 'draconica': 'draconica'}
    cadeia = {}
    for nome, tabela in resumo.items():
        cadeia[nome] = {}
        for txt, ch in tabela:
            m = re.search(r'Chave (VIP|Farm|Mágica|Magma|Draconica|Mineracao)', txt)
            if m:
                alvo = {'VIP': 'vip', 'Farm': 'farm', 'Mágica': 'magica', 'Magma': 'magma',
                        'Draconica': 'draconica', 'Mineracao': 'mineracao'}[m.group(1)]
                cadeia[nome][alvo] = cadeia[nome].get(alvo, 0) + ch / 100
    escrever(arq, d, pasta)
    return {'tabelas': resumo, 'cadeia': cadeia, 'itens_chave': chaves, 'caixa_da_chave': caixa_da_chave}
