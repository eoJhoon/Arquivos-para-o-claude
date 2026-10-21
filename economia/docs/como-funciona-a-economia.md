# Como a economia funciona (v1, 21/10/2026)

Documento técnico para o Gui revisar. Os números estão na planilha `saida/Economia_Rede_Nexus.xlsx`
e em `saida/numeros.md`; aqui fica o raciocínio. Nada foi escolhido à mão: os preços saem do
simulador a partir de `params/`.

## 1. Diagnóstico (Etapa 1 do prompt mestre)

Dados medidos: 67.440 blocos/h na mina 1; Fly não ajuda; Fungo 153.000 quebras/h; bloco de área paga
inteiro; bloco de área não disparou outro encantamento (1 teste); tamanho e reset das minas.

O que ainda é hipótese (lista completa em `saida/o-que-medir.md`): velocidade nas minas avançadas,
quantos blocos cada encantamento de área quebra de verdade, se o booster soma % (Fortuna 300 = +300%),
Cenoura/Melancia/Cana por hora, golpes por segundo no boss, mobs por spawn.

Erros do modelo antigo que este corrige: produção da mina subestimada (10,3k contra 67,4k medido);
preços sem tempo de pagamento; encantamentos sem simulação; rank desligado do resto; moedas extras
(Composto, Fibra Nexus) removidas; último rank chamado "Nexus" (é Dragão); Explorador mais barato
que Cidadão; chave a 0,10% por bloco dava 67 chaves/h (e centenas com área).

## 2. A régua: renda de referência

Tudo é medido em "horas de renda". A renda de referência I(s) é o money por hora de um jogador
típico minerando na posição s (0 = Cidadão I, 99 = Dragão X), com a picareta que ele costuma ter ali:

I(s) = 67.440 blocos/h x money por bloco da mina x M x (1 + Fortuna)

- Money por bloco: 1 na mina Cidadão e x2,5 a cada mina (1; 2,5; 6,2; 16; 39; 98; 240; 610; 1.500; 3.800).
  Gemas: 1 e x1,6 a cada mina. Mina VIP: o dobro da Cidadão (2 e 2), como o Enzo pediu.
- M = blocos totais por bloco quebrado (1 + contribuição dos encantamentos de área).
- Picareta típica: nível = 1000 x (fração do jogo / 1,5) ^ 0,7. Começa rápido (nível 68 com 5 h) e chega
  no Dragão X perto de 740 (no simulador, com a folga de EXP, o jogador típico chega com 814). O 1000
  fica para os prestígios.
- Atenção: com uma linha por nível, o encantamentos.yml passou de ~200 KB para 3 MB. Testar se o plugin
  carrega rápido no reload.

## 3. Picareta (Etapa 3)

Preço de cada nível = (quanto o nível aumenta a renda) x (horas para se pagar) x I(onde esse nível
costuma ser comprado). As horas para se pagar crescem de 15 min no começo do jogo a 10 h no fim.
Gemas: mesmo número de horas, em renda de gemas, dividido por 0,5 (metade do money vai para a
picareta), então money e gemas acabam no mesmo ritmo (o "50/50 de esforço" do prompt).

- Fortuna Aprimorada: +0,30% de money por nível (+300% no 1000). Gemado: +0,20% (+200%).
  Chaveiro: +0,10% relativo de chave por nível (+100%, o dobro de chaves).
- 11 encantamentos de área: cada um tem uma contribuição no nível 1000 (0,25 a 0,35 bloco extra por
  bloco quebrado; soma 3,3, então M chega a 4,3). A chance sai da contribuição dividida pelos blocos
  da ativação. Se o Enzo medir os blocos de verdade, a chance se corrige sozinha.
- A área cresce nos marcos 250/500/750 até o tamanho que eles já usam hoje.
- Liberação pelo nível da picareta (EXP): Explosivo no 0, Cruz 30, Drill 60, Laser 100, Mob 150,
  Fenda 200, Meteoro 280, Tempestade 360, Chuva 440, Destruidor 520, Nuclear 600. O nível máximo de cada
  encantamento acompanha o nível da picareta. Isso é o que impede subir a picareta só com money:
  EXP só vem minerando.
- EXP por bloco diferente em cada mina (0,6 na argila até 1,8 na redstone), para a picareta andar 10%
  à frente do jogador típico.
- O config tem uma linha por nível (1000 linhas por encantamento) com aumento 0. Assim não importa como
  o plugin lê "aumento-por-nivel": o valor de cada nível é o que está escrito.
- Speed e Haste: chance 100 (efeito contínuo, como a descrição promete). Não aumentam a produção
  (hipótese), então custam pouco.
- Multiplicador de Prisma removido do menu; booster de money removido das armaduras (decisões do Enzo).
  A Fortuna Aprimorada da picareta usa o encantamento booster_money: é por ele que a Fortuna funciona.
- Skins: +0%, 3%, 6%, 9% e 12% de money (a descrição agora bate com o config; tiramos as promessas de
  bônus de gemas e "poder especial" que não existiam).

## 4. Minas e ranks (Etapa 4)

O simulador joga o servidor de 2 em 2 minutos: minera, ganha money e gemas, compra o upgrade de melhor
retorno, sobe de rank. O preço de cada rank é ajustado até o jogador típico passar o tempo-alvo em
cada rank (5 h no Cidadão até 46 h no Dragão, soma 230 h). Os preços nunca caem de um rank para o
seguinte.

Estratégias testadas: típico (metade do money na picareta), quem corre para rank (20%) e a melhor
divisão possível (otimizado). A diferença ficou abaixo de 10%: nenhuma estratégia é muito superior.
Com o payback antigo de 25 h no fim, correr para rank era 16% mais rápido; por isso ficou 10 h.

Requisitos extras (cabeças de spawner, cabeça de boss, Fragmentos de Mineração) nos ranks V e X a
partir do Tritão estão na planilha, aba Ranks. Ainda não estão no ranks.yml porque não sabemos o formato
do campo `itens` (ver seção 9).

Chave de mineração: 0,02% por bloco (1 a cada 5.000), 13 por hora na mina 1 sem encantamento. Os blocos
de área também rolam chave (Enzo), então com área e Chaveiro fica entre 30 e 100 por hora no fim.

## 5. Agricultura, cacto e armazém (Etapas 5 e 6)

- O armazém tem um preço fixo por item. Para o preço acompanhar o rank, cada grupo do LuckPerms recebe a
  permissão `armazem.lucro.money@X` (o próprio plugin suporta). Os comandos estão em
  `saida/comandos-luckperms.txt`. O lucro fica grande no fim (+345.000% no Dragão) porque a mina também
  cresce 3.800x; é só um número no plugin.
- Fungo rende 70% da mina em money; Cana 45% e é a 2a em sementes; Melancia é a melhor em sementes
  (100 mil/h); Cenoura dá o item de expansão (0,02% por colheita, ~30 itens/h).
- Liberação por rank (decisão: depois da mina, travado por rank): Fungo Guerreiro I, Cenoura Guerreiro V,
  Melancia Tritão I, Cana Tritão V, Cacto Guardião I. Feito por permissão (comandos no mesmo arquivo).
- Sem lucro comprando e revendendo: a loja vende cada semente por 3x o maior preço de venda possível.
- Cacto: 10 níveis (50 a 1.000 cactos), no máximo 10% da renda da mina por hora. O armazém segura no
  máximo 8 h de cacto: quem fica AFK mais tempo não ganha mais. Com multicontas liberadas, isso é o que
  limita o farm de contas paradas.
- Armazém: começa em 1.000; cada item da Cenoura +1.000 (hipótese: falta confirmar quanto o item soma).

## 6. Spawners e almas (Etapa 7)

Os 5 spawners do armazém (Vaca, Porco, Zumbi, Esqueleto, Golem) agora soltam a cabeça direto no armazém,
que vende por almas (1; 2,5; 6; 15; 40 almas por cabeça). Liberam do Tritão I ao Avatar I. Preço de cada
spawner: 1,5 h de renda. Limite por jogador: 1 a 64, subindo com o item "Stack de Spawners" dos bosses.
`stack-por-player` agora está ligado (antes era infinito, um exploit).

## 7. Matadoras e bosses (Etapa 8)

Matadora k libera no Tritão VI (k=1) até o Necromante X (k=10). Preço: 3 h de renda em money + 4 h de
almas, e exige a Matadora anterior. IX e Nexus pedem 10 e 30 Fragmentos de Arena. Não veio config de
Matadora: é especificação para quem for configurar.

Vida do boss = dano da Matadora recomendada x 4 golpes/s x tempo de luta (60 s no boss 1 até 240 s no
10). Os bosses agora sempre dão a cabeça (requisito de rank), dão "Limite de Armazém" e "Stack de
Spawners" maiores conforme o boss, e chaves Mágica (bosses 3 a 6), Magma (7 e 8) e Dracônica (9 e 10).

## 8. Caixas e fragmentos (Etapa 9)

As chances de todas as caixas agora somam 100%, mantendo a proporção que vocês já tinham. A chave da
mina abria a caixa errada (o config da caixa Mineração esperava a chave VIP): corrigido. Cadeia de
chaves medida: cada caixa devolve no máximo 0,03 chave por abertura, então não existe chave infinita.

## 9. O que falta para a v2

1. Formato do campo `itens` no ranks.yml: com um exemplo (colocar 1 item num rank pelo /rankup editar e
   mandar o trecho do arquivo), o gerador passa a escrever os requisitos de cabeça, boss e fragmento.
2. Plugin que solta itens na colheita (para a Cenoura dar o item de expansão e as plantações darem o
   Fragmento de Plantação). Não veio no repositório.
3. Plugin da Matadora, da pesca e da loja (preço dos spawners, sementes e ovos de boss).
4. Testes da lista `saida/o-que-medir.md`, principalmente blocos por ativação e o booster de money.
5. Casual: com 1,5 h/dia o jogo leva ~21 semanas (meta 12 a 18). Opções: aceitar, ou dar um bônus de
   volta diário (precisa de plugin). Hoje o modelo aceita.
6. Desempenho: a Detonação Nuclear quebra ~600 mil blocos de uma vez (1 vez a cada ~25 h por jogador no
   máximo). Vale testar o lag antes de liberar.
