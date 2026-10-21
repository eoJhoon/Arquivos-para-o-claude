"""Planilha legível para o Enzo e o João: economia/saida/Economia_Rede_Nexus.xlsx

Lê economia/saida/resultado.json (gerado por gen.gerar_tudo). Não calcula nada novo.
"""
import json
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

ECON = Path(__file__).resolve().parents[1]
if str(ECON) not in sys.path:
    sys.path.insert(0, str(ECON))

from sim.modelo import Modelo, NIVELADOS, AREA        # noqa: E402
from sim.params import Params                          # noqa: E402

TITULO = Font(bold=True, size=13, color='FFFFFF')
CAB = Font(bold=True, color='FFFFFF')
FUNDO_TIT = PatternFill('solid', fgColor='1F4E78')
FUNDO_CAB = PatternFill('solid', fgColor='2E75B6')
ATENCAO = PatternFill('solid', fgColor='FFE699')    # amarelo: atenção
CRITICO = PatternFill('solid', fgColor='F4B183')    # laranja: crítico
FINA = Side(style='thin', color='BFBFBF')
BORDA = Border(left=FINA, right=FINA, top=FINA, bottom=FINA)
ROMANOS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
NOME_ENC = {'speed': 'Speed', 'haste': 'Haste', 'fortuna': 'Fortuna Aprimorada', 'gemado': 'Gemado',
            'chaveiro': 'Chaveiro', 'Explosivo': 'Impacto Explosivo', 'cruz': 'Ataque em Cruz', 'Drill': 'Drill',
            'laser': 'Laser de Perfuração', 'mobexplosivo': 'Mob Explosivo', 'trincheira': 'Fenda',
            'meteoro': 'Impacto Meteoro', 'tempestadedefogo': 'Tempestade de Fogo', 'chuvaacida': 'Chuva Ácida',
            'destruidor': 'Destruidor', 'nuclear': 'Detonação Nuclear'}


def fmt(v):
    """Número no jeito brasileiro: 1.234.567 / 12,5 mil / 3,4 bi."""
    if isinstance(v, str) or v is None:
        return v
    a = abs(v)
    if a >= 1e9:
        return f'{v / 1e9:,.2f} bi'.replace(',', 'X').replace('.', ',').replace('X', '.')
    if a >= 1e6:
        return f'{v / 1e6:,.2f} mi'.replace(',', 'X').replace('.', ',').replace('X', '.')
    if a >= 1000:
        return f'{v:,.0f}'.replace(',', '.')
    if a >= 10 or float(v).is_integer():
        return f'{v:.0f}'
    return f'{v:.4g}'.replace('.', ',')


class Aba:
    def __init__(self, wb, nome, titulo, explicacao):
        self.ws = wb.create_sheet(nome)
        self.lin = 1
        self.larg = {}
        self.ws.cell(1, 1, titulo).font = TITULO
        self.ws.cell(1, 1).fill = FUNDO_TIT
        self.ws.cell(2, 1, explicacao).alignment = Alignment(wrap_text=True, vertical='top')
        self.ws.row_dimensions[2].height = 15 * (1 + len(explicacao) // 110)
        self.ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=8)
        self.lin = 4

    def tabela(self, cabecalho, linhas, destaque=None):
        ws = self.ws
        for j, c in enumerate(cabecalho, 1):
            cel = ws.cell(self.lin, j, c)
            cel.font, cel.fill, cel.border = CAB, FUNDO_CAB, BORDA
            cel.alignment = Alignment(wrap_text=True, horizontal='center', vertical='center')
            self._larg(j, c, cab=True)
        self.lin += 1
        for i, linha in enumerate(linhas):
            for j, v in enumerate(linha, 1):
                cel = ws.cell(self.lin, j, fmt(v))
                cel.border = BORDA
                cel.alignment = Alignment(horizontal='right' if not isinstance(v, str) else 'left')
                self._larg(j, fmt(v))
                if destaque:
                    cor = destaque(i, j, v)
                    if cor:
                        cel.fill = cor
            self.lin += 1
        self.lin += 1

    def texto(self, t):
        self.ws.cell(self.lin, 1, t).alignment = Alignment(wrap_text=False)
        self.lin += 1

    def _larg(self, j, v, cab=False):
        n = len(str(v)) if v is not None else 0
        if cab:
            n = min(n, 22)
        self.larg[j] = max(self.larg.get(j, 8), n + 2)

    def fechar(self):
        for j, w in self.larg.items():
            self.ws.column_dimensions[get_column_letter(j)].width = min(w, 70)
        self.ws.column_dimensions['A'].width = max(self.ws.column_dimensions['A'].width or 0, 14)
        self.ws.freeze_panes = 'A5'


def nome_pos(mo, s):
    return f"{mo.P['ranks.nomes'][s // 10]} {ROMANOS[s % 10]}"


def gerar():
    res = json.loads((ECON / 'saida' / 'resultado.json').read_text(encoding='utf-8'))
    mo = Modelo()
    P = Params()
    wb = Workbook()
    wb.remove(wb.active)

    # Resumo
    a = Aba(wb, 'Resumo', 'Economia Rede Nexus: resumo',
            'Tudo aqui sai do simulador (pasta economia). Para mudar um número, mudem o parâmetro em '
            'economia/params e o GitHub gera tudo de novo. Horas = horas efetivas jogando.')
    eq, ot, ing = res['equilibrado'], res['otimizado'], res['ingenuo']
    linhas = [['Jogador ativo típico (metade do money na picareta)', eq['horas_total'], 'h até o Dragão X'],
              ['Jogador que otimiza (melhor divisão de gasto)', ot['horas_total'], 'h até o Dragão X'],
              ['Jogador que só corre para o rank', ing['horas_total'], 'h até o Dragão X'],
              ['Picareta do jogador típico no Dragão X', eq['picareta_final'], 'nível (máximo 1000)'],
              ['Upgrades de picareta comprados até o Dragão X', eq['compras'], 'compras'],
              ['Soma dos 99 ranks (1a volta)', sum(res['custos_rank'][:99]), 'money'],
              ['1o prestígio custa', res['fator_prestigio_1'], 'x o preço da 1a volta (picareta e money ficam)']]
    for nome, p in P['metas.perfis'].items():
        sem = eq['horas_total'] / (p['horas_dia'] * 7)
        linhas.append([f'Perfil {nome} ({p["horas_dia"]} h/dia)', round(sem, 1),
                       f'semanas (meta {p["semanas_min"]} a {p["semanas_max"]})'])
    a.tabela(['Item', 'Valor', 'Unidade'], linhas,
             destaque=lambda i, j, v: ATENCAO if (i == 7 and j == 2) else None)
    a.fechar()

    # Ranks
    a = Aba(wb, 'Ranks', 'Preço dos 100 ranks',
            'Preço = money para sair do rank e ir para o próximo. Dragão X = preço de prestigiar. '
            'Tempo = horas do jogador ativo típico naquele rank (simulado).')
    lin = []
    acum = 0
    for s in range(100):
        h = eq['horas_por_posicao'][s] if s < len(eq['horas_por_posicao']) else 0
        acum += h
        lin.append([nome_pos(mo, s), res['custos_rank'][s], round(h, 2), round(acum, 1),
                    res['custos_rank'][s] * res['multiplicadores_prestigio'][1]])
    a.tabela(['Rank', 'Preço (money)', 'Horas no rank', 'Horas acumuladas', 'Preço no 1o prestígio'], lin)
    a.texto('Requisitos extras (itens) nos ranks V e X, a partir do Tritão. Ainda não estão no ranks.yml: '
            'falta saber o formato do campo itens (ver relatório).')
    a.tabela(['Rank', 'Cabeças de spawner', 'Cabeça de boss', 'Fragmentos'],
             [[r['posicao'], r.get('cabecas', '-'), r.get('boss', '-'), r.get('fragmentos', '-')]
              for r in res.get('requisitos_rank', [])])
    a.fechar()

    # Minas
    a = Aba(wb, 'Minas', 'Valor das minas',
            'Money e gemas por bloco. Renda típica = 1 hora minerando com a picareta que o jogador costuma ter '
            'ao chegar nesse rank (blocos de área inclusos).')
    lin = []
    for m, t in enumerate(res['minas'][:10]):
        rm, rg = mo.renda_ref(10 * m)
        lin.append([t['mina'], t['bloco'], t['money'], t['gemas'], f"{t['chave_pct']}%", rm, rg])
    v = res['minas'][10]
    lin.append([v['mina'], v['bloco'], v['money'], v['gemas'], f"{v['chave_pct']}%", '', ''])
    a.tabela(['Mina', 'Bloco', 'Money/bloco', 'Gemas/bloco', 'Chance de chave', 'Renda típica money/h',
              'Renda típica gemas/h'], lin)
    a.texto(f"Blocos por hora (medido): {fmt(mo.R)}. Chaves por hora sem encantamento: "
            f"{fmt(mo.R * P['design.chance_chave_pct'] / 100)}.")
    a.fechar()

    # Picareta
    a = Aba(wb, 'Picareta', 'Encantamentos: preço e efeito por nível',
            'Preço de subir para o nível. Cada nível dá exatamente o efeito da tabela (o config tem uma linha '
            'por nível). Libera = nível da picareta (EXP) que solta o encantamento.')
    niveis = [1, 2, 10, 50, 100, 250, 500, 750, 1000]
    lin = []
    for e in NIVELADOS:
        for L in niveis:
            cm, cg = res['precos_amostra'][e][str(L)]
            if e == 'fortuna':
                efeito = f'+{L * P["picareta.fortuna_pct_por_nivel"]:.1f}% money'
            elif e == 'gemado':
                efeito = f'+{L * P["picareta.gemado_pct_por_nivel"]:.1f}% gemas'
            elif e == 'chaveiro':
                efeito = f'+{L * P["design.chaveiro_pct_por_nivel"]:.1f}% chaves'
            else:
                from gen.encantamentos import escala_da_faixa
                esc = escala_da_faixa(mo, L)
                efeito = (f'{mo.chance_pct(e, L, esc):.5f}% por bloco, ~{mo.blocos_por_ativacao(e, esc):.0f} blocos')
            lin.append([NOME_ENC[e], L, cm, cg, efeito, mo.libera(e)])
    a.tabela(['Encantamento', 'Nível', 'Money', 'Gemas', 'Efeito no nível', 'Libera (picareta)'], lin)
    a.texto('Speed e Haste: 2 níveis cada, efeito contínuo. Preços na aba Resumo do relatório.')
    a.fechar()

    # Área
    a = Aba(wb, 'Area', 'Encantamentos de área no máximo',
            'Ativações por hora e blocos extras por hora no nível 1000, minerando 1 hora. '
            'Contribuição = blocos extras por bloco quebrado.')
    from gen.encantamentos import escala_da_faixa
    lin = []
    for e in AREA:
        ch = mo.chance_pct(e, 1000, 1.0)
        ativ = mo.R * ch / 100
        lin.append([NOME_ENC[e], f'{ch:.5f}%', round(ativ, 1), mo.blocos_por_ativacao(e, 1.0),
                    mo.area[e]['contribuicao'], mo.R * mo.area[e]['contribuicao']])
    a.tabela(['Encantamento', 'Chance/bloco', 'Ativações/h', 'Blocos por ativação', 'Contribuição',
              'Blocos extras/h'], lin, destaque=lambda i, j, v: CRITICO if (j == 4 and isinstance(v, float)
                                                                            and v > 100000) else None)
    a.texto('Nuclear quebra a mina inteira (~600 mil blocos de uma vez). Ver desempenho no relatório.')
    a.fechar()

    # Agricultura
    ag = res['agricultura']
    a = Aba(wb, 'Plantacoes', 'Plantações',
            'Preço base por unidade no armazém (vale do Guerreiro). Nos ranks seguintes o lucro sobe por permissão '
            '(armazem.lucro.money), igual à mina. Colheita liberada por rank.')
    lin = []
    for k, b in ag['base'].items():
        lin.append([k.capitalize(), nome_pos(mo, b['libera_rank']), b['money'], b['sementes'], b['quebras_h'],
                    ag['implantacao'][k], ag['loja_preco_unidade'][k]])
    a.tabela(['Plantação', 'Libera em', 'Venda money/un', 'Venda sementes/un', 'Colheitas/h', 'Compra (1 vez)',
              'Preço na loja/un'], lin)
    lin = [[l['rank'], f"+{l['lucro_pct']}%", l['mina_money_h'], l['fungo_money_h'], l['cana_money_h'],
            l['cenoura_money_h'], l['melancia_money_h'], l['melancia_sementes_h'], l['cana_sementes_h']]
           for l in ag['tabela']]
    a.tabela(['Rank', 'Lucro armazém', 'Mina money/h', 'Fungo money/h', 'Cana money/h', 'Cenoura money/h',
              'Melancia money/h', 'Melancia sementes/h', 'Cana sementes/h'], lin)
    a.texto(f"Item de expansão da Cenoura: {ag['item_cenoura_por_hora']:.1f} por hora colhendo cenoura.")
    a.fechar()

    # Cacto e armazém
    a = Aba(wb, 'Cacto e Armazem', 'Cacto automático e armazém',
            'Cacto produz sozinho, mas para quando o armazém enche. O armazém comporta no máximo 8 h de cacto: '
            'quem fica AFK mais tempo não ganha mais.')
    c = res['cacto']
    a.tabela(['Nível', 'Cactos', 'Libera em', 'Money/h', 'Sementes/h', '% da mina', 'Custo money',
              'Custo sementes', 'Se paga em (h)'],
             [[n['nivel'], n['cactos'], n['libera'], n['money_h'], n['sementes_h'], n['vs_mina_pct'],
               n['custo_money'], n['custo_sementes'], n['retorno_horas']] for n in c['niveis']])
    arm = res['armazem']
    a.tabela(['Cactos', 'Capacidade p/ 8 h', 'Itens da Cenoura', 'Horas colhendo cenoura'],
             [[m['cactos'], m['capacidade_para_8h'], m['itens_cenoura'], m['horas_de_cenoura']] for m in arm['marcos']])
    a.texto(f"Capacidade inicial {fmt(arm['capacidade_inicial'])}; cada item da Cenoura +{fmt(arm['por_item'])}; "
            f"máximo {fmt(arm['maximo'])}.")
    a.fechar()

    # Combate
    sp = res['spawners']
    a = Aba(wb, 'Combate', 'Spawners, Matadoras e bosses',
            'Spawner solta mobs; a cabeça vai para o armazém e vira almas. Almas compram Matadoras e invocam bosses.')
    a.tabela(['Spawner', 'Libera em', 'Preço (money)', 'Cabeças/h', 'Almas/cabeça', 'Almas/h por spawner'],
             [[t['nome'], t['libera'], t['preco_money'], t['cabecas_h'], t['almas_por_cabeca'],
               t['almas_h_por_spawner']] for t in sp['tipos']])
    a.tabela(['Rank', 'Limite de spawners'], [[k, v] for k, v in sp['limite_por_rank'].items()])
    a.tabela(['Matadora', 'Dano', 'Libera em', 'Money', 'Almas', 'Fragmentos de Arena'],
             [[m['matadora'], m['dano'], m['libera'], m['preco_money'], m['preco_almas'], m['fragmentos_arena']]
              for m in res['matadoras']])
    a.tabela(['Boss', 'Nome no config', 'Vida', 'Luta (s)', 'Matadora', 'Cooldown (h)', 'Invocar (almas)',
              'Limite armazém', 'Stack spawner', 'Chave'],
             [[b['boss'], bc['nome'], b['vida'], b['luta_s'], b['matadora'], b['cooldown_h'], b['invocar_almas'],
               bc['limite_armazem'], bc['stack_spawner'], bc['chave_caixa'] or '-']
              for b, bc in zip(res['bosses'], res['bosses_config'])])
    a.fechar()

    # Caixas
    a = Aba(wb, 'Caixas', 'Caixas: chance de cada prêmio (soma 100%)',
            'Chances normalizadas para somar 100%, mantendo a proporção que vocês já tinham.')
    for nome, tab in res['caixas']['tabelas'].items():
        a.texto(f'Caixa {nome}')
        a.tabela(['Prêmio', 'Chance %'], [[t[0], t[1]] for t in tab])
    a.fechar()

    # Prestígio
    a = Aba(wb, 'Prestigio', 'Prestígios',
            'Fator = quanto custa cada rank naquele prestígio comparado à 1a volta. O jogador mantém picareta e money.')
    a.tabela(['Prestígio', 'Fator de preço', 'Horas da volta (simulado)'],
             [[p, round(res['multiplicadores_prestigio'][p], 3),
               round(res['prestigio_horas'][p], 1) if p < len(res['prestigio_horas']) else '']
              for p in range(1, len(res['multiplicadores_prestigio']))])
    a.fechar()

    # Parâmetros
    a = Aba(wb, 'Parametros', 'De onde vem cada número',
            'medido = teste no servidor; decidido = Enzo e João; hipotese = proposta ou suposição a validar.')
    lin = []
    for k in sorted(P):
        m = P.meta(k)
        v = m['valor']
        txt = v if isinstance(v, (int, float, str, bool)) else json.dumps(v, ensure_ascii=False)[:60]
        lin.append([k, str(txt), m['tipo'], m['fonte']])
    a.tabela(['Parâmetro', 'Valor', 'Tipo', 'Fonte'], lin,
             destaque=lambda i, j, v: ATENCAO if (j == 3 and v == 'hipotese') else None)
    a.fechar()

    destino = ECON / 'saida' / 'Economia_Rede_Nexus.xlsx'
    wb.save(destino)
    return destino


if __name__ == '__main__':
    print(gerar())
