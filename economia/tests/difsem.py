"""Diferença de conteúdo (não de formatação) entre a versão do git e a atual de um .yml."""
import subprocess
import sys

import yaml


def caminhos_diferentes(a, b, caminho=''):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if k not in a:
                yield f'{caminho}/{k} (novo)'
            elif k not in b:
                yield f'{caminho}/{k} (removido)'
            else:
                yield from caminhos_diferentes(a[k], b[k], f'{caminho}/{k}')
    elif a != b:
        yield caminho


def original(rel, ref='main'):
    txt = subprocess.run(['git', 'show', f'{ref}:{rel}'], capture_output=True, check=True).stdout.decode('utf-8')
    return yaml.safe_load(txt)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    for rel in sys.argv[1:]:
        antes = original(rel)
        depois = yaml.safe_load(open(rel, encoding='utf-8'))
        dif = list(caminhos_diferentes(antes, depois))
        resumo = {}
        for c in dif:
            partes = c.split('/')
            chave = '/'.join(partes[:4])
            resumo[chave] = resumo.get(chave, 0) + 1
        print(f'== {rel}: {len(dif)} diferenças')
        for k, v in sorted(resumo.items())[:40]:
            print(f'   {k}: {v}')
