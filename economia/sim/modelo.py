"""Fórmulas da economia. Tudo sai dos parâmetros; nenhum número de jogo é escrito aqui.

Glossário
- posição s: 0 = Cidadão I ... 99 = Dragão X. Mina do jogador = s // 10.
- bloco primário: bloco que o jogador quebra com a picareta. Os blocos de área vêm por cima.
- M (multiplicador de área): blocos totais por bloco primário = 1 + soma das contribuições.
- renda de referência: o que um jogador típico ganha por hora de mina numa posição s, com a
  picareta que ele costuma ter ali. Serve de régua para os preços.
"""
import math
from functools import lru_cache

from .params import Params

AREA = ['Explosivo', 'cruz', 'Drill', 'laser', 'mobexplosivo', 'trincheira', 'meteoro',
        'tempestadedefogo', 'chuvaacida', 'destruidor', 'nuclear']
BOOST = ['fortuna', 'gemado', 'chaveiro']
FIXOS = ['speed', 'haste']
NIVELADOS = BOOST + AREA
TODOS = FIXOS + NIVELADOS

# nome do encantamento no plugin (chave em encantamentos.yml)
CHAVE_PLUGIN = {'fortuna': 'booster_money', 'gemado': 'booster_gemas', 'chaveiro': 'booster_chaveiro'}


def arred(x, sig=3):
    """Arredonda para 'sig' algarismos significativos (preços legíveis)."""
    if x <= 0:
        return 0
    e = math.floor(math.log10(x)) - sig + 1
    v = round(x / 10 ** e) * 10 ** e
    if e >= 0:
        return int(round(v))
    return round(v, -e)


class Modelo:
    def __init__(self, P=None):
        self.P = P or Params()
        P = self.P
        self.R = P['mineracao.blocos_por_hora']
        self.area = P['encantamentos_area']
        self.occ = P['servidor.ocupacao_media_da_mina']
        self.f_fort = P['picareta.fortuna_pct_por_nivel'] / 100
        self.f_gem = P['picareta.gemado_pct_por_nivel'] / 100
        self.f_chav = P['design.chaveiro_pct_por_nivel'] / 100
        self.sigma = P['design.fracao_money_para_picareta']
        pesos = P['design.peso_horas_por_rank']
        g = P['design.crescimento_dentro_do_rank']
        total = P['metas.horas_ativo_total']
        escala = total / sum(pesos)
        # horas-alvo em cada posição (tempo que o ativo passa em s antes de upar para s+1)
        self.alvo_h = []
        for m, w in enumerate(pesos):
            sub = [1 + g * i for i in range(10)]
            k = w * escala / sum(sub)
            self.alvo_h += [k * x for x in sub]
        # tempo acumulado até chegar em s (s=0 começa em 0 h); s=100 = fim (prestígio)
        self.alvo_acum = [0.0]
        for h in self.alvo_h:
            self.alvo_acum.append(self.alvo_acum[-1] + h)
        self.total_h = self.alvo_acum[-1]

    # ------------------------------------------------------------------ minas
    def mina_money(self, m):
        return arred(self.P['minas.mina1_money_por_bloco'] * self.P['design.razao_money_entre_minas'] ** m, 2)

    def mina_gemas(self, m):
        return arred(self.P['minas.mina1_gemas_por_bloco'] * self.P['design.razao_gemas_entre_minas'] ** m, 2)

    def mina_money_suave(self, s):
        return self.P['minas.mina1_money_por_bloco'] * self.P['design.razao_money_entre_minas'] ** (s / 10)

    def mina_gemas_suave(self, s):
        return self.P['minas.mina1_gemas_por_bloco'] * self.P['design.razao_gemas_entre_minas'] ** (s / 10)

    # ------------------------------------------------------------------ referência de picareta
    def p_ref(self, s):
        """Nível de referência da picareta (e dos encantamentos) na posição s (contínua)."""
        k = self.P['design.picareta_max_na_fracao']
        return 1000 * min(1.0, self.tau(s) / k) ** self.P['design.curva_picareta_expoente']

    def tau(self, s):
        """Fração do jogo (tempo) já jogada ao chegar na posição s."""
        s = max(0.0, min(100.0, s))
        i = int(min(99, s))
        return (self.alvo_acum[i] + (s - i) * self.alvo_h[i]) / self.total_h

    def tau_do_nivel(self, p):
        """Fração do jogo em que o jogador típico chega na picareta p (passa de 1 = depois do Dragão X)."""
        k = self.P['design.picareta_max_na_fracao']
        return k * (p / 1000) ** (1 / self.P['design.curva_picareta_expoente'])

    def s_do_nivel(self, p):
        """Inverso de p_ref: em que posição o jogador típico tem picareta p (máximo 99,99)."""
        alvo = min(1.0, self.tau_do_nivel(p)) * self.total_h
        for i in range(100):
            if self.alvo_acum[i + 1] >= alvo:
                return i + (alvo - self.alvo_acum[i]) / self.alvo_h[i]
        return 100.0

    def libera(self, e):
        return self.area[e]['libera_picareta'] if e in self.area else 0

    def nivel_ref(self, e, s):
        u = self.libera(e)
        p = self.p_ref(s)
        return max(0.0, min(1000.0, (p - u) / (1000 - u) * 1000))

    def teto_por_picareta(self, e, p):
        """Nível máximo do encantamento que a picareta de nível p permite."""
        u = self.libera(e)
        if p < u:
            return 0
        return int(min(1000, math.floor((p - u) / (1000 - u) * 1000))) if u < 1000 else 0

    # ------------------------------------------------------------------ efeitos
    def mult_area(self, niveis):
        return 1 + sum(self.area[e]['contribuicao'] * niveis.get(e, 0) / 1000 for e in AREA)

    def F(self, L):
        return 1 + self.f_fort * L

    def G(self, L):
        return 1 + self.f_gem * L

    def K(self, L):
        return 1 + self.f_chav * L

    def niveis_ref(self, s):
        return {e: self.nivel_ref(e, s) for e in NIVELADOS}

    def renda_ref(self, s):
        """(money/h, gemas/h) de 1 hora só minerando, com a picareta típica da posição s."""
        n = self.niveis_ref(s)
        M = self.mult_area(n)
        money = self.R * self.mina_money_suave(s) * M * self.F(n['fortuna'])
        gemas = self.R * self.mina_gemas_suave(s) * M * self.G(n['gemado'])
        return money, gemas

    # ------------------------------------------------------------------ preço dos níveis
    def payback(self, tau):
        """Horas para um upgrade se pagar, conforme a fração do jogo em que ele é comprado."""
        t1 = self.P['design.payback_horas_inicio']
        t2 = self.P['design.payback_horas_fim']
        return t1 * (t2 / t1) ** tau

    def ganho_relativo(self, e, L, M_ref):
        """Quanto o nível L (vindo do L-1) aumenta a renda, em fração."""
        if e == 'fortuna':
            return self.f_fort / (1 + self.f_fort * (L - 1))
        if e == 'gemado':
            return self.f_gem / (1 + self.f_gem * (L - 1))
        if e == 'chaveiro':
            return self.P['design.chaveiro_valor_da_chave'] * self.f_chav / (1 + self.f_chav * (L - 1))
        return self.area[e]['contribuicao'] / 1000 / M_ref

    def preco(self, e, L):
        """(money, gemas) para subir de L-1 para L. Nunca mais barato que o nível anterior."""
        if e in FIXOS:
            return self.preco_fixo(e, L)
        return self.tabela_precos(e)[L - 1]

    @lru_cache(maxsize=None)
    def tabela_precos(self, e):
        tab, ant_m, ant_g = [], 0, 0
        for L in range(1, 1001):
            m, g = self._preco_bruto(e, L)
            if L > 1 or e not in AREA:
                m, g = max(m, ant_m), max(g, ant_g)
            if L == 1 and e in AREA:
                ant_m, ant_g = 0, 0   # o nível 1 (desbloqueio) não puxa os seguintes para cima
            else:
                ant_m, ant_g = m, g
            tab.append((m, g))
        return tuple(tab)

    def _preco_bruto(self, e, L):
        """(money, gemas) para subir o encantamento e do nível L-1 para L.

        preço em horas = payback(L) x ganho relativo do nível
        money = horas x renda de referência em money onde esse nível costuma ser comprado
        gemas = horas x renda de referência em gemas / fração do money que vai para a picareta
        (assim money e gemas acabam no mesmo ritmo: esforço 50/50)
        """
        if e in FIXOS:
            return self.preco_fixo(e, L)
        u = self.libera(e)
        p = u + (L - 0.5) / 1000 * (1000 - u)
        s = self.s_do_nivel(p)
        n = self.niveis_ref(s)
        M = self.mult_area(n)
        rm, rg = self.renda_ref(s)
        horas = self.payback(min(1.0, self.tau_do_nivel(p))) * self.ganho_relativo(e, L, M)
        if L == 1 and e in AREA:
            horas += self.P['design.desbloqueio_horas']   # comprar o 1o nível = liberar o encantamento
        return arred(horas * rm), arred(horas * rg / self.sigma)

    def preco_fixo(self, e, L):
        # Speed e Haste não aumentam produção (hipótese). Preço = horas de renda numa posição fixa.
        tabela = {('speed', 1): (3, 0.5), ('speed', 2): (25, 2.0),
                  ('haste', 1): (5, 0.5), ('haste', 2): (30, 2.0)}
        s, horas = tabela[(e, L)]
        rm, rg = self.renda_ref(s)
        return arred(horas * rm), arred(horas * rg / self.sigma)

    # ------------------------------------------------------------------ chance dos encantamentos
    def blocos_por_ativacao(self, e, faixa_escala):
        a = self.area[e]
        b = a['blocos']
        for d in a['radios']:
            b *= max(1, round(d * faixa_escala)) / d   # mesma medida arredondada que vai no radios
        return max(1.0, b * self.occ)

    def chance_pct(self, e, L, faixa_escala):
        """Chance em % por bloco primário que entrega a contribuição do nível L."""
        c = self.area[e]['contribuicao'] * L / 1000
        return 100 * c / self.blocos_por_ativacao(e, faixa_escala)

    # ------------------------------------------------------------------ EXP da picareta
    def exp_ate(self, p):
        a, b = self.P['picareta.exp_inicial'], self.P['picareta.exp_aumento']
        return a * p + b * p * (p + 1) / 2

    def nivel_da_exp(self, exp):
        a, b = self.P['picareta.exp_inicial'], self.P['picareta.exp_aumento']
        # resolve a p + b p(p+1)/2 = exp
        A, B, C = b / 2, a + b / 2, -exp
        p = (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)
        return min(1000, int(p))

    def exp_por_bloco(self):
        """EXP por bloco em cada mina, para a picareta andar 10% à frente da referência."""
        folga = self.P['design.exp_folga_picareta']
        frac = self.P['design.fracao_do_tempo_por_atividade']
        out = []
        for m in range(10):
            p0 = min(1000, folga * self.p_ref(10 * m))
            p1 = min(1000, folga * self.p_ref(10 * m + 10))
            horas_mina = sum(self.alvo_h[10 * m:10 * m + 10]) * frac[m]['mina']
            blocos = self.R * horas_mina
            out.append(max(0.1, round((self.exp_ate(p1) - self.exp_ate(p0)) / blocos, 2)))
        return out
