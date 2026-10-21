"""Leitura e escrita dos .yml dos plugins sem bagunçar o resto do arquivo.

Usa ruamel.yaml em modo ida e volta: mensagens, posições e itens que não mexemos ficam iguais
(só a quebra de linhas longas pode mudar, o que não muda o conteúdo).
"""
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

REPO = Path(__file__).resolve().parents[2]   # raiz do repositório (pasta com Rankup/, MinaReset/...)


def yaml_rt():
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    return y


def ler(rel):
    return yaml_rt().load((REPO / rel).read_text(encoding='utf-8'))


def escrever(rel, dados, pasta=None):
    destino = (pasta or REPO) / rel
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, 'w', encoding='utf-8', newline='\n') as f:
        yaml_rt().dump(dados, f)
    return destino


def mapa(**kw):
    """Dicionário que sai numa linha só no .yml ({a: 1, b: 2})."""
    m = CommentedMap()
    for k, v in kw.items():
        m[k] = v
    m.fa.set_flow_style()
    return m


def mapa_de(d, flow=True):
    m = CommentedMap()
    for k, v in d.items():
        m[k] = v
    if flow:
        m.fa.set_flow_style()
    return m


def num(x):
    """Número limpo para o .yml (inteiro quando dá)."""
    if isinstance(x, float) and x.is_integer():
        return int(x)
    return x
