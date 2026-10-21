# O que medir no servidor

Lista gerada a partir de params/hipoteses.yaml. Cada teste troca uma suposição por um número real.
Quando medirem, mudem o valor no params, troquem o tipo para "medido" e escrevam a fonte.

1. **armazem** (hoje: {"capacidade_inicial": 1000, "item_cenoura_capacidade": 1000). Teste: quanto +1 de 'Limite de Armazém' soma de verdade
2. **encantamentos_area** (hoje: {"Explosivo": {"contribuicao": 0.3, "blocos": 27, "radios": ). Teste: ativar cada um numa parede e contar
3. **servidor.blocos_area_rolam_chave** (hoje: true). Teste: contando chaves com e sem Explosivo
4. **servidor.booster_soma_porcentagem** (hoje: true). Teste: Fortuna Aprimorada 1000, quebrar 100 blocos na mina 1, deve dar 400
5. **servidor.cana_quebras_por_hora** (hoje: 100000). Teste: 1 min colhendo
6. **servidor.cenoura_quebras_por_hora** (hoje: 153000). Teste: 1 min colhendo cenoura
7. **servidor.exp_aumento_linear** (hoje: true). Teste: no menu da picareta (Experiência @exp/@maxexp)
8. **servidor.golpes_por_segundo** (hoje: 4). Teste: cronometrar uma luta
9. **servidor.melancia_quebras_por_hora** (hoje: 100000). Teste: 1 min colhendo
10. **servidor.mobs_por_spawn_por_spawner** (hoje: 1). Teste: 1 spawner por 5 min, contar mobs
11. **servidor.speed_haste_aumentam_producao** (hoje: false). Teste: 5 min com Haste II
12. **servidor.velocidade_igual_em_todas_as_minas** (hoje: true). Teste: repetir o teste de 5 min na mina Dragão
