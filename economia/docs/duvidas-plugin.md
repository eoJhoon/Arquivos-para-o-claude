# Dúvidas sobre os plugins: testes para o Enzo e o João

Lendo os arquivos não dá para saber essas coisas. Cada uma tem um teste rápido no servidor.
Façam na ordem: as 4 primeiras são as que mais mudam a economia.

Dica geral: usem uma conta de teste, zerem o dinheiro antes (`money remove`) e anotem o saldo antes e
depois. Mandem o resultado de cada teste com o número (D1, D2...).

## Prioridade alta

**D4. Bloco quebrado pela explosão pode ativar outro encantamento?**
Isso é o mais importante de todos. Se puder, uma explosão puxa outra e a mina inteira cai sozinha.
- Teste: deem a uma picareta Explosivo bem alto e Cruz bem alto (`/es enchant`). Minerem 2 minutos
  olhando o chat/efeitos. Se aparecer Cruz saindo do meio de uma explosão (sem vocês terem quebrado
  aquele bloco), a resposta é sim.
- Se o plugin tiver opção para desligar isso, desliguem. Se não tiver, avisem.

**D5. Bloco quebrado pela explosão paga dinheiro e gemas?** (vocês disseram que deve valer o bloco
inteiro; queremos confirmar que o plugin faz isso)
- Teste: picareta só com Explosivo. Saldo zerado. Quebrem 1 bloco por vez até sair 1 explosão. Vejam
  quanto entrou na hora da explosão. Se entrar uns 27 (mina 1), paga tudo.

**D6. Bloco quebrado pela explosão pode dar chave?**
- Teste: igual ao D5, mas contem quantas chaves caem em 10 minutos com e sem Explosivo.

**D15. Quantas chaves caem por hora na mina 1?**
- O arquivo diz chance 0,10. Se for porcentagem, cai 1 chave a cada 1.000 blocos (umas 67 por hora).
- Teste: minerem 5 minutos na mina 1 com picareta sem encantamento e contem as chaves. Se der umas 5 ou 6,
  é porcentagem.

## Prioridade média

**D1. A chance do encantamento é porcentagem?**
- Teste: coloquem Explosivo nível 1 e abram o menu da picareta. Que número aparece em "Ativação"?
  Depois coloquem nível 100 e vejam de novo. Mandem os dois números (print serve).

**D3. O que significa o tamanho da explosão (`radios`)?**
- Teste: Explosivo (3x3x3) e Chuva Ácida (10x10x25). Ativem cada um numa parede lisa e tirem print do
  buraco. Contem quantos blocos de largura, altura e profundidade.

**D7. O Booster de Money soma ou multiplica?**
- Teste: Fortuna Aprimorada (booster_money) no nível 1.000 (máximo). Quebrem 100 blocos na mina 1 e vejam
  quanto entrou. Sem booster entra 100. Se entrar uns 150, é +50%. Se entrar uns 5.000, multiplica.

**D8. Booster de Money na picareta funciona?**
O arquivo só deixa esse encantamento em armadura e livro, mas o menu da picareta oferece.
- Teste: tentem upar "Fortuna Aprimorada" no menu da picareta. Funciona? Se tiver armadura com o mesmo
  booster, os dois somam? (repitam o teste D7 com e sem a armadura)

**D12. Fortuna mexe no dinheiro ou nas gemas?**
- Teste: picareta com Fortuna (encantamento normal do jogo) nível 3. Quebrem 100 blocos na mina 1. Entrou
  100 money e 100 gemas, ou mais que isso em algum dos dois?

**D14. Qual rank minera em qual mina?**
São 100 ranks e 10 minas. Digam quais ranks entram em cada mina (ex.: Cidadão I a X na mina 1).

**D17. O que o prestígio faz?**
O plugin de rankup já tem prestígio. Testem numa conta: o que acontece com o rank, o dinheiro, a picareta
e os encantamentos quando a conta faz prestígio? Isso decide como vamos montar o final do jogo.

**D18. O comando automático de preço roda sozinho?**
No config do Rankup tem `comandos-executar: '1250000 100 0-10 1 Sim money'`. Ele roda quando? Se rodar
no reload ou quando o servidor liga, ele troca os preços dos ranks e pode zerar as moedas.
- Teste: num servidor de teste, deem `/rankup reload` e vejam se o preço do Cidadão I mudou de 10.000.
  Se não souberem, apaguem essa linha antes de colocar os preços novos.

## Prioridade baixa

**D2.** Laser, Meteoro e Tempestade deixam upar até o nível 3.000, mas a chance só está configurada até
1.000. No nível 1.001 a chance continua, para ou zera? (só importa se alguém passar de 1.000)

**D9.** Abram o menu da picareta com Explosivo nos níveis 0, 1, 10 e 11 e mandem o "Custo" de cada um.
Assim confirmamos a conta do preço.

**D10.** EXP da picareta: quanto falta para o nível 2 e para o nível 3? (aparece na lore "Experiência").

**D11.** A picareta ganha EXP minerando na mina 3 (pedregulho) ou só na argila? No arquivo só a argila dá EXP.

**D13.** A mina VIP paga mesmo 2.000 gemas por bloco? (a mina 1 paga 1). É de propósito?

**D16.** O que acontece quando o jogador está no Dragão X e tenta upar? (o arquivo aponta para um rank
que não existe)

## Coisas quebradas que dá para arrumar já (não precisa testar)
- O botão "Multiplicador de Prisma" no menu da picareta aponta para um encantamento que não existe.
- A descrição das skins mostra bônus diferentes do que o arquivo dá (ex.: Picareta de Pedra diz +15%, dá 20)
  e promete bônus de gemas e "poder especial" que não estão configurados.
- A mina12 não paga nada (`funciona: false`).
