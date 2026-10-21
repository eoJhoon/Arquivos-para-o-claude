# Economia da Rede Nexus

Aqui fica a economia do servidor feita como "receita". Vocês mudam os ingredientes (os números em
`params/`) e o robô do GitHub refaz todos os arquivos dos plugins sozinho.

## O que tem em cada pasta

- `params/`: os números de entrada. Três arquivos:
  - `medido.yaml`: o que vocês testaram no servidor (ex.: 5.620 blocos em 5 minutos).
  - `decidido.yaml`: o que vocês decidiram (ex.: mina VIP paga o dobro).
  - `hipoteses.yaml`: o que ainda é chute ou proposta. Cada item diz como testar.
- `sim/`: o simulador. Ele joga o servidor de mentira, minuto a minuto, e acha os preços.
- `gen/`: escreve os .yml dos plugins (Rankup, Encantamentos, MinaReset, Armazem, Spawners, Bosses, Caixas).
- `tests/`: as travas. Se uma mudança quebrar a economia, o robô fica vermelho e explica o porquê.
- `saida/`: o resultado. Abram a planilha `Economia_Rede_Nexus.xlsx`. Tem também `o-que-medir.md`
  (lista de testes) e `comandos-luckperms.txt` (comandos para colar no console).

## Como mudar um número (pelo site do GitHub)

1. Abram o arquivo em `params/` (ex.: `hipoteses.yaml`).
2. Cliquem no lápis (Edit), troquem o `valor` e expliquem na `fonte` de onde veio.
3. Cliquem em "Commit changes".
4. Esperem uns 5 minutos. Na aba **Actions** aparece o robô rodando.
   - Verde: deu certo. Os .yml novos já estão salvos no repositório.
   - Vermelho: alguma trava reprovou. Cliquem nele e leiam a mensagem (em português).
5. Baixem os .yml novos para o servidor e deem reload nos plugins.

Exemplos do que dá para mudar sem medo:
- Testaram de novo a mineração e deu outro número: `medido.yaml`, `mineracao.blocos_por_hora`.
- Acham que o jogo está curto ou longo: `decidido.yaml`, `metas.horas_ativo_total`.
- Querem o Cidadão mais rápido: `hipoteses.yaml`, `design.peso_horas_por_rank` (primeiro número).
- Mediram quantos blocos o Explosivo quebra: `hipoteses.yaml`, `encantamentos_area`, `blocos` do Explosivo.
  A chance se corrige sozinha e a economia não muda.

Quando chamar o Gui: sistema novo, mudar como uma mecânica funciona, trava vermelha que vocês não
entenderam, ou rebalancear tudo.

## Rodar no computador (opcional)

```
cd economia
pip install pyyaml ruamel.yaml==0.18.6 pytest openpyxl
python -m gen.gerar_tudo
python -m gen.planilha
python -m gen.relatorio
python -m pytest -q
```
