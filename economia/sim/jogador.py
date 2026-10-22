"""Simulação de um jogador, passo a passo, em horas efetivas de jogo.

A estratégia é a fração do money que vai para a picareta (o resto vai para rank):
- equilibrado: 0,5 (jogador típico; é ele que calibra os preços dos ranks)
- ingenuo: 0,2 (corre para o rank)
- otimizado: a fração que termina mais rápido (procurada em jogadores.py/otimizado)
Dentro da picareta, o jogador compra sempre o upgrade de melhor retorno que consegue pagar.
Se não houver nada para comprar (travado pelo nível da picareta), a sobra vai para o rank.
"""
from dataclasses import dataclass, field

from .modelo import Modelo, TODOS, FIXOS, AREA

PASSO_H = 1 / 30  # 2 minutos
LIMITE_PAYBACK_H = 20  # jogador real não compra upgrade que leva mais de 20 h para se pagar
FRACOES = {'equilibrado': 0.5, 'ingenuo': 0.2}


@dataclass
class Resultado:
    estrategia: str
    horas_por_posicao: list = field(default_factory=list)   # horas gastas em cada s (0..98)
    horas_total: float = 0.0
    chegou: bool = False
    niveis_final: dict = field(default_factory=dict)
    picareta_final: int = 0
    gasto_picareta: float = 0.0
    gasto_rank: float = 0.0
    gemas_gastas: float = 0.0
    compras: int = 0
    compras_por_hora: list = field(default_factory=list)
    renda_final: float = 0.0
    linha_do_tempo: list = field(default_factory=list)       # por rank: (h, s, picareta, money/h, M)
    horas_prestigio: list = field(default_factory=list)


class Jogador:
    def __init__(self, modelo: Modelo, custos_rank, estrategia='equilibrado', niveis=None, exp=0.0):
        self.mo = modelo
        self.custos = custos_rank
        self.nome = estrategia if isinstance(estrategia, str) else f'fracao_{estrategia:.2f}'
        self.sigma = FRACOES[estrategia] if isinstance(estrategia, str) else float(estrategia)
        self.niv = {e: 0 for e in TODOS}
        if niveis:
            self.niv.update(niveis)
        self.exp = exp
        self.frac = modelo.P['design.fracao_do_tempo_por_atividade']
        self.agro = modelo.P['design.money_agricultura_vs_mina']
        self.exp_bloco = modelo.exp_por_bloco()
        self.maximos = modelo.P['picareta.niveis_maximos']

    def renda(self, s):
        mo, n = self.mo, self.niv
        m = s // 10
        M = mo.mult_area(n)
        f = self.frac[m]
        mina_money = mo.R * mo.mina_money(m) * M * mo.F(n['fortuna'])
        mina_gemas = mo.R * mo.mina_gemas(m) * M * mo.G(n['gemado'])
        # chaves: o que as caixas devolvem vale uma fração da renda da mina (sobe com o Chaveiro)
        caixas = mo.P['design.chaveiro_valor_da_chave'] * mina_money * mo.K(n['chaveiro'])
        money = f['mina'] * (mina_money + caixas) + f['agricultura'] * self.agro * mo.renda_ref(s)[0]
        gemas = f['mina'] * mina_gemas
        return money, gemas, M

    def ganho(self, e, M):
        mo, n = self.mo, self.niv
        if e == 'fortuna':
            return mo.f_fort / mo.F(n[e])
        if e == 'gemado':
            return 0.5 * mo.f_gem / mo.G(n[e])   # gemas são metade do preço da picareta
        if e == 'chaveiro':
            return mo.P['design.chaveiro_valor_da_chave'] * mo.f_chav / mo.K(n[e])
        if e in FIXOS:
            return 1e-4
        return mo.area[e]['contribuicao'] / 1000 / M

    def melhor_compra(self, p, money_h, gemas_h, M, fundo, gemas):
        """Upgrade de melhor retorno que dá para pagar agora. None se nada couber."""
        melhor, tem_algum = None, False
        self.reserva = 0.0   # quanto vale juntar para o melhor upgrade que ainda não cabe
        melhor_fora = None
        for e in TODOS:
            L = self.niv[e] + 1
            if L > self.maximos[e]:
                continue
            if e not in FIXOS and L > self.mo.teto_por_picareta(e, p):
                continue
            tem_algum = True
            cm, cg = self.mo.preco(e, L)
            if cm > fundo or cg > gemas:
                roi_fora = self.ganho(e, M) / max(cm / max(money_h, 1e-9), 1e-12)
                if melhor_fora is None or roi_fora > melhor_fora[0]:
                    melhor_fora = (roi_fora, cm)
                continue
            ganho = self.ganho(e, M)
            if L == 1 and e in AREA:
                # o 1o nível é caro (desbloqueio): avalia o pacote até onde a picareta deixa
                teto = min(self.mo.teto_por_picareta(e, p), 200)   # avalia liberar + os primeiros 200 níveis
                custo_pac = sum(self.mo.preco(e, x)[0] for x in range(1, teto + 1))
                ganho, cm_eq = ganho * teto, custo_pac
            else:
                cm_eq = cm
            horas = max(cm_eq / max(money_h, 1e-9), cg / max(gemas_h, 1e-9) * self.mo.sigma)
            roi = ganho / max(horas, 1e-12)
            if roi < 1 / LIMITE_PAYBACK_H and e not in FIXOS:
                continue   # não vale a pena: demora demais para se pagar
            if melhor is None or roi > melhor[0]:
                melhor = (roi, e, L, cm, cg)
        if melhor_fora:
            self.reserva = melhor_fora[1]
        return melhor, tem_algum

    def rodar(self, horas_max=1200, prestigios=0, mult_prestigio=1.0, linha=False):
        mo = self.mo
        r = Resultado(self.nome)
        s, t, gemas = 0, 0.0, 0.0
        fundo_pic, fundo_rank = 0.0, 0.0
        prest, entrou_s, inicio_prest = 0, 0.0, 0.0
        compras_hora, prox_marca = 0, 1.0
        while t < horas_max:
            m = s // 10
            money_h, gemas_h, M = self.renda(s)
            ganho_m = money_h * PASSO_H
            gemas += gemas_h * PASSO_H
            self.exp += self.frac[m]['mina'] * mo.R * self.exp_bloco[m] * PASSO_H
            p = mo.nivel_da_exp(self.exp)
            t += PASSO_H
            fundo_pic += ganho_m * self.sigma
            fundo_rank += ganho_m * (1 - self.sigma)
            while True:
                melhor, tem_algum = self.melhor_compra(p, money_h, gemas_h, M, fundo_pic, gemas)
                if melhor is None:
                    break
                _, e, L, cm, cg = melhor
                self.niv[e] = L
                fundo_pic -= cm
                gemas -= cg
                r.gasto_picareta += cm
                r.gemas_gastas += cg
                r.compras += 1
                compras_hora += 1
                money_h, gemas_h, M = self.renda(s)
            # o jogador só guarda para a picareta o que precisa para o próximo upgrade bom
            sobra = fundo_pic - (self.reserva if tem_algum else 0.0)
            if sobra > 0:
                fundo_rank += sobra
                fundo_pic -= sobra
            if t >= prox_marca:
                r.compras_por_hora.append(compras_hora)
                compras_hora, prox_marca = 0, prox_marca + 1.0

            if isinstance(mult_prestigio, (list, tuple)):
                fator = mult_prestigio[min(prest, len(mult_prestigio) - 1)]
            else:
                fator = mult_prestigio ** prest
            custo = self.custos[s] * fator
            if fundo_rank < custo:
                continue
            fundo_rank -= custo
            r.gasto_rank += custo
            if s < 99:
                if prest == 0:
                    r.horas_por_posicao.append(t - entrou_s)
                entrou_s = t
                s += 1
                if linha and prest == 0:
                    r.linha_do_tempo.append((round(t, 2), s, p, money_h, round(M, 3)))
                if s == 99 and prest == 0:
                    r.horas_total, r.chegou = t, True
                    inicio_prest = t
                    if prestigios == 0:
                        break
            else:
                # Dragão X: o custo da posição 99 é o preço de prestigiar
                r.horas_prestigio.append(t - inicio_prest)
                inicio_prest = t
                prest += 1
                s, entrou_s = 0, t
                if prest >= prestigios:
                    break
        if not r.chegou:
            r.horas_total = t
        r.niveis_final = dict(self.niv)
        r.picareta_final = mo.nivel_da_exp(self.exp)
        r.renda_final = self.renda(s)[0]
        return r


def otimizado(modelo, custos, fracoes=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9), horas_max=1500):
    """O mais rápido entre várias divisões de gasto. É o 'jogador que otimiza'."""
    melhores = []
    for f in fracoes:
        r = Jogador(modelo, custos, f).rodar(horas_max=horas_max)
        melhores.append((r.horas_total if r.chegou else 1e9, f, r))
    melhores.sort(key=lambda x: x[0])
    return melhores[0][2], [(round(h, 1), f) for h, f, _ in melhores]
