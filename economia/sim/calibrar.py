"""Acha o preço de cada rank para o jogador 'equilibrado' bater as horas-alvo.

Começa com preço = horas-alvo x (parte do money que vai para rank) x renda de referência e
corrige rank a rank pela razão entre o tempo-alvo e o tempo simulado, até convergir.
"""
from .modelo import Modelo, arred
from .jogador import Jogador


def chute_inicial(mo: Modelo):
    custos = []
    for s in range(99):
        money, _ = mo.renda_ref(s + 0.5)
        frac = mo.P['design.fracao_do_tempo_por_atividade'][s // 10]
        renda = money * (frac['mina'] + frac['agricultura'] * mo.P['design.money_agricultura_vs_mina'])
        custos.append(mo.alvo_h[s] * (1 - mo.sigma) * renda)
    custos.append(custos[-1])  # posição 99 = preço de prestigiar (Dragão X -> prestígio)
    return custos


def crescente(valores):
    """Ajuste crescente mais próximo (média geométrica dos vizinhos que descem). Algoritmo PAV."""
    import math
    blocos = []   # (soma dos logs, quantidade)
    for v in valores:
        blocos.append([math.log(v), 1])
        while len(blocos) > 1 and blocos[-2][0] / blocos[-2][1] > blocos[-1][0] / blocos[-1][1]:
            s, n = blocos.pop()
            blocos[-1][0] += s
            blocos[-1][1] += n
    out = []
    for s, n in blocos:
        out += [math.exp(s / n)] * n
    return out


def calibrar(mo: Modelo, iteracoes=25, tolerancia=0.02, verbose=False):
    custos = chute_inicial(mo)
    hist = []
    for it in range(iteracoes):
        r = Jogador(mo, custos, 'equilibrado').rodar(horas_max=mo.total_h * 3)
        h = r.horas_por_posicao
        if len(h) < 99:
            for s in range(len(h), 99):
                custos[s] *= 0.7
        erro_max = 0.0
        for s in range(min(99, len(h))):
            razao = mo.alvo_h[s] / max(h[s], 1e-6)
            erro_max = max(erro_max, abs(razao - 1))
            custos[s] *= razao ** 0.8
        custos[:99] = crescente(custos[:99])   # rank nunca mais barato que o anterior
        hist.append((it, round(r.horas_total, 1), round(erro_max, 3)))
        if verbose:
            print('iteracao', it, 'horas', round(r.horas_total, 1), 'erro max', round(erro_max, 3))
        if len(h) == 99 and erro_max < tolerancia:
            break
    custos = [arred(c) for c in custos]
    return custos, hist


def multiplicadores(f1, crescimento, n):
    """Fator de preço em cada prestígio: [1 (1a volta), f1, f1 x c, f1 x c^2, ...]."""
    return [1.0] + [f1 * crescimento ** i for i in range(n)]


def calibrar_prestigio(mo: Modelo, custos, verbose=False):
    """Fator de preço do 1o prestígio para a volta levar as horas-alvo.

    O jogador mantém picareta e dinheiro (decisão do Enzo) e volta para a mina Cidadão.
    Cada prestígio seguinte custa 'crescimento' vezes o anterior.
    """
    alvo = mo.P['design.prestigio_horas_cada']
    cresc = mo.P['design.prestigio_crescimento']
    n = mo.P['ranks.prestigios']
    lo, hi = 0.01, 10.0
    f1, h = 1.0, None
    for _ in range(25):
        f1 = (lo * hi) ** 0.5
        mult = multiplicadores(f1, cresc, n)
        r = Jogador(mo, custos, 'equilibrado').rodar(horas_max=mo.total_h * 2 + alvo * 4, prestigios=2,
                                                    mult_prestigio=mult)
        h = r.horas_prestigio[1] if len(r.horas_prestigio) > 1 else 1e9
        if verbose:
            print('f1', round(f1, 3), 'horas da 1a volta de prestigio', round(h, 1))
        if abs(h / alvo - 1) < 0.03:
            break
        if h < alvo:
            lo = f1
        else:
            hi = f1
    return round(f1, 4), multiplicadores(round(f1, 4), cresc, n)
