# Como os plugins interpretam os campos (Etapa A)

Fonte: configs/ (clone de eoJhoon/Arquivos-para-o-claude, main, 20/10/2026). Os plugins são da família
"ghost" (ghostencantamentos, ghostrankup, ghosteconomia, ghostmcmmo). Não há documentação pública
(1 busca na web, nada encontrado). Tudo abaixo vem da leitura dos .yml.

Legenda de confiança:
- **confirmado**: o próprio arquivo diz (comentário, mensagem do plugin ou formato inequívoco).
- **provável**: dedução forte pela coerência interna dos números; confirmar com o teste indicado em duvidas-plugin.md.
- **não dá para saber lendo**: vai para duvidas-plugin.md.

## 1. Encantamentos (Encantamentos/encantamentos.yml)

### 1.1 Escala da chance: porcentagem (provável)
- Encantamentos de combate usam `chance: 100` para "sempre" (Fúria, Executor, Toque Dourado) e valores
  como 1,5 / 2,5 / 10. A mesa de encantamento usa `chance-minima: 1` e `chance-maximo: 100`. Escala 0 a 100.
- Os encantamentos de mina usam a mesma chave `chance` com valores muito pequenos (Explosivo 0,0008).
  Lido como fração, o Explosivo sozinho daria 80% por bloco no nível 1.000 e a soma passaria de 300%,
  o que não faz sentido. Lido como %, a soma no nível máximo dá 3,51% por bloco.
- O menu mostra `@enchantchance%` e a lore da skin diz "Chance: 0.07%", reforçando a leitura em %.
- Conclusão de trabalho: **chance por bloco quebrado, em %**. Teste D1 confirma.

### 1.2 Faixas e aumento-por-nivel (provável)
Formato dos encantamentos de mina:
```
efeito:
  '1-1000':           # faixa de nível do encantamento
    chance: 0.0008
    aumento-por-nivel: 0.0008
    radios: '3x3x3'
```
- Chance no nível n ≈ `chance + aumento-por-nivel × (n − 1)` ou `× n`. Como `chance = aumento` em todos,
  a diferença é de 1 nível (n × base ou (n+1) × base). Irrelevante para a economia, mas o teste D1 resolve.
- Speed e Haste usam faixas de 1 nível (`'1-1'`, `'2-2'`) com `chance: 5` e `aumento: 0`: 5% por bloco,
  efeito de 20 s. A 18,7 blocos/s isso dispara quase todo segundo, ou seja, efeito permanente na prática.
- Laser, Meteoro e Tempestade de Fogo têm `level-necessario` até 3.000, mas o `efeito` só vai até 1.000.
  O que acontece acima de 1.000 não dá para saber lendo (D2).

Chance no nível máximo (1.000), em % por bloco, lida como 1.000 × base:

| Encantamento | Base | Nível 1.000 | radios |
|---|---|---|---|
| Explosivo | 0,0008 | 0,80% | 3x3x3 |
| Cruz | 0,0007 | 0,70% | 10x7x8 |
| Drill | 0,0005 | 0,50% | 1x15 |
| Mob Explosivo | 0,0005 | 0,50% | 5x5x5 (mob PIG, 5 s) |
| Laser | 0,0004 | 0,40% | 4x30 |
| Trincheira (Fenda) | 0,00025 | 0,25% | 9x7 |
| Meteoro | 0,00015 | 0,15% | 10 |
| Tempestade de Fogo | 0,0001 | 0,10% | 10x12 |
| Chuva Ácida | 0,00007 | 0,07% | 10x10x25 |
| Destruidor | 0,00003 | 0,03% | 1 camada inteira |
| Nuclear | 0,00001 | 0,01% | mina inteira |
| **Soma** | | **3,51%** | |

### 1.3 Formato de `radios` (não dá para saber lendo)
Aparecem 4 formatos: 3 números (`3x3x3`, `10x10x25`), 2 números (`1x15`, `9x7`, `4x30`), 1 número
(`10`) e nenhum (Nuclear, Destruidor: o tamanho vem do próprio efeito). Não está claro se é raio ou
dimensão total, nem qual eixo é qual. Isso muda os blocos por ativação em até 8x (raio 3 = cubo 7x7x7 = 343;
dimensão 3 = 27). Teste D3.

### 1.4 Bloco quebrado por área: Fortuna, outro encantamento, chave (não dá para saber lendo)
Não existe no encantamentos.yml, no config.yml do plugin, nem no MinaReset nenhuma chave que controle
isso (procurei todas as chaves dos três arquivos). O comportamento está no código do plugin. Testes D4 a D6.

Por que isso é a dúvida número 1: se bloco de área puder disparar encantamento, as ativações novas por
ativação são `chance × blocos atingidos`. No nível máximo, contando o volume literal do `radios`:
- Explosivo: 0,8% × 27 = 0,22
- Mob Explosivo: 0,5% × 125 = 0,63
- Chuva Ácida: 0,07% × 2.500 = 1,75
- Destruidor: 0,03% × 8.836 (camada 94x94) = 2,65
- Cruz: 0,7% × 560 = 3,92
- Nuclear: 0,01% × 751.060 = 75

A soma passa muito de 1: a cadeia não termina sozinha e a mina inteira cai em sequência. Com uma
regra "bloco de área não dispara encantamento", o risco some.

### 1.5 Boosters (provável, com 2 dúvidas)
```
booster_money:  booster: '1-1000': {quantidade: 0.05, aumento-por-nivel: 0.05}
booster_gemas:  0.05 por nível
booster_chaveiro: 0.02 por nível
```
- O MinaReset soma o booster ao dinheiro do bloco pela placeholder `%ghostencantamentos_booster_money%`
  (MinaReset/config.yml, `booster-adicionar`). **confirmado** que o booster entra no dinheiro da mina.
- No nível 1.000 a placeholder vale 50 (money e gemas) e 20 (chaveiro). Lido como %, dá +50% e +20%,
  coerente com a lore `@enchantbooster%`. Teste D7 confirma se é +50% ou ×50.
- `booster_money` só aceita capacete, peitoral, calça, bota e livro (`ids`), mas o menu da picareta
  evolutiva oferece "Fortuna Aprimorada" que aponta para `booster_money`. Ou o menu ignora `ids`, ou o
  upgrade na picareta falha (D8). Isso também define se os boosters de armadura e picareta se somam.
- `booster_prisma` aparece no menu da picareta (slot 20), mas **não existe** no encantamentos.yml.
  Esse botão do menu está quebrado.
- `desconto_money`: 5% a 25% (níveis 1 a 5) de desconto no custo de evolução.

### 1.6 Custo de upgrade por nível (provável)
```
upgrade:
  0-10:  {custo: {gemas: 30000, money: 50000}, aumento: {gemas: 367, money: 1256}}
  11-50: {custo: {gemas: 34138, money: 64263}, aumento: {...}}
```
- Leitura: custo do nível n dentro da faixa = `custo + aumento × (n − início da faixa)`.
- Prova pela coerência: no Explosivo, Chaveiro e Gemado o início de cada faixa é exatamente o fim da
  anterior mais o `aumento` da nova (diferença zero em todas as 8 faixas). Em Drill, Cruz, Laser,
  Meteoro, Trincheira e outros há saltos pequenos entre faixas (os números foram montados de outro jeito),
  mas o formato é o mesmo.
- Moedas aceitas no custo: `money` e `gemas` (definidas em Encantamentos/config.yml; existe também `tempo`).
- Teste D9 confirma o custo exato dos níveis 0, 1, 10 e 11.

### 1.7 Picareta evolutiva (Encantamentos/evolutivos.yml)
- Item inicial `270\[E]{32:32000,34:32000}`: picareta de madeira com Eficiência 32.000 e Inquebrável
  32.000. Quebra instantânea; a velocidade real é limitada pelo jogador (os 18,73 blocos/s medidos).
- EXP da picareta: `exp-inicial: 2500`, `aumento: 39`, e só `STAINED_CLAY: 1` ganha EXP.
  Duas dúvidas: se o aumento é +39 de EXP por nível ou +39% (D10), e se a picareta para de ganhar EXP
  nas minas 3 em diante (pedra, lápis, prismarinho... não estão na lista) (D11).
- O `level-necessario` dos encantamentos de mina está aberto (0 a 1.000, sem requisito): o nível da
  picareta não trava nenhum encantamento hoje.
- Skins: `bonus.money` 10 a 50 (provavelmente +10% a +50% de dinheiro). A lore das skins anuncia valores
  diferentes do config (skin 2 diz +15%, config dá 20; skin 1 diz +10%, config dá `{}`) e promete bônus de
  gemas e "poder especial" que não existem no config. Hoje a lore engana o jogador.

## 2. Minas (MinaReset/)

### 2.1 Tamanho e reset (confirmado)
- Todas as minas de rank: 94 x 85 x 94 = 751.060 blocos (bate com `totalblocos`). minapvp: 743.070.
- `reset: 1200`: reseta a cada 20 min. `porcentagem: 40`: reseta antes se 40% dos blocos forem quebrados
  (300.424 blocos). Texto do holograma confirma.
- Cada mina tem um único bloco (100%).

### 2.2 Valor por bloco (confirmado)
Fica em MinaReset/blocos.yml, por bloco e por mina, em `moeda`:

| Mina | Bloco | money/bloco | gemas/bloco | chance de chave |
|---|---|---|---|---|
| rank1 | argila 9 | 1 | 1 | 0,10 |
| rank2 | argila 13 | 3 | 1,2 | 0,105 |
| rank3 | pedregulho | 8 | 1,5 | 0,11 |
| rank4 | bloco de lápis | 20 | 2 | 0,115 |
| rank5 | prismarinho | 50 | 2,5 | 0,12 |
| rank6 | bloco de ouro | 120 | 3 | 0,125 |
| rank7 | bloco de ferro | 280 | 4 | 0,13 |
| rank8 | bloco de quartzo | 650 | 5 | 0,135 |
| rank9 | bloco de carvão | 1.500 | 6,5 | 0,14 |
| rank10 | bloco de redstone | 3.500 | 8 | (sem chave) |
| vip | bloco de esmeralda | 0 | 2.000 | 0,20 (vai pro correio) |
| mina12 | argila 9 | nada (`funciona: false`) | | |
| minapvp | bloco de lápis | sem config própria | | |

- `chance: 100.0` no money e gemas: sempre paga. Escala em % (100 = sempre). **confirmado**.
- `fortunefunciona: false` no money: Fortuna não multiplica o dinheiro. Atenção: no money a chave se chama
  `fortunefunciona` e nas gemas `funcionafortuna`; a mensagem de ajuda do plugin fala em `funciona-fortuna`.
  Uma delas pode estar sendo ignorada (D12).
- A mina vip usa um formato antigo (`quantia/moeda/fortunefunciona: "nao"`) e paga 2.000 gemas por bloco,
  1.000 vezes a mina 1. Ver D13.
- O mapeamento "qual rank minera em qual mina" não está nos arquivos (100 ranks, 10 minas de rank). D14.

### 2.3 Fortuna da mina (confirmado o formato)
`fortuna: '0'..'5' {min, max}` define quantos itens caem (drop `351:4\@qnt`), não o dinheiro. Do nível 4
para o 5 o drop pula de 8 a 10 para 64 a 128. Só afeta o drop físico, que hoje está desligado nas minas de
rank (só a entrada `*` usa `@qnt`, e ela está com `funciona: false`).

### 2.4 Chave de mineração (provável)
Drop `131:0\1\[nome]...\0.10\padrao\padrao`: 1 chave com chance 0,10. Se for % (mesma escala do drop
padrão `100.0`), dá 1 chave a cada 1.000 blocos, ou **67 chaves por hora** na mina 1. A economia antiga do
ChatGPT previa 1/20.000 (3,4/h): o servidor hoje está **20 vezes acima** disso. Teste D15.

## 3. Rankup (Rankup/)

### 3.1 Formato do custo (confirmado)
```
rank5:
  rank: rank5
  rank-prox: rank6
  prestigio:
    '1':
      tag: '&7[Cidadão VI]'
      grupo-lp: rank5
      custo: {money: 60000.0, itens: []}
```
- 100 entradas (default, rank1 a rank99). Custo hoje linear: 10.000 × posição (10 mil a 1 milhão).
  Total para chegar ao fim: 50,5 milhões.
- `custo` aceita `money` e lista `itens`. As cabeças e os Fragmentos (Pesca, Plantação, Arena, Mineração)
  já existem como moedas internas (`ghostrankup_moedaid_...`, /acougue) e a lore diz "Acumule para upar de rank".
  Ou seja, o plugin já suporta exigir cabeça ou Fragmento no rankup.
- A moeda `tempo` existe mas sem comando de remoção (`remove: ''`).
- O último rank (rank99, Dragão X) aponta para `rank100`, que não existe (D16).

### 3.2 Prestígio já existe no plugin (confirmado)
Cada rank tem uma lista `prestigio` (hoje todos só com o '1'), o menu tem "Adicionar/Remover Prestígio",
`gui-prestigio` e a mensagem "Agora você está no prestígio @prestigio". Isso resolve a decisão 5 (prestígio
no final) sem plugin novo, mas não sabemos o que o prestígio reseta (D17).

### 3.3 Risco: comando de preço automático
`config.yml` tem `comandos-executar: '1250000 100 0-10 1 Sim money'` e `reset-todas-moedas-antes-de-fazer-calculo: true`.
Pelo editor, isso significa "preço inicial 1,25 milhão, +100% por rank, ranks 0 a 10, prestígio 1". Os
preços atuais não batem com isso, então provavelmente não rodou. Se rodar (no reload ou no início), ele
reescreve os preços que vamos gerar e talvez zere as moedas. D18.

## 4. Correções ao HANDOFF
- Chance de chave real: 0,10% por bloco na mina 1 (não 1/20.000, que era a proposta do ChatGPT).
- Soma das chances no máximo: 3,51%, não ~4%.
- A trava Σ(chance × blocos) ≤ 0,3 só é necessária se o teste D4 mostrar que bloco de área dispara
  encantamento. Pelos volumes acima, sem essa regra o problema é muito pior do que o HANDOFF estimou.
- O Prestígio não precisa de sistema novo (seção 3.2).
