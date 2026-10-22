// Documento de preços para o Enzo e o João digitarem nos plugins.
// Lê economia/saida/doc_dados.json (gerado por gen/doc_dados.py) e escreve
// economia/saida/Precos_Economia_Rede_Nexus.docx
// Uso: node gen/doc_precos.js   (dentro de economia/)
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  AlignmentType, HeadingLevel, BorderStyle, LevelFormat, PageBreak, Footer, PageNumber,
} = require('docx');

const ECON = path.resolve(__dirname, '..');
const d = JSON.parse(fs.readFileSync(path.join(ECON, 'saida', 'doc_dados.json'), 'utf8'));

const AZUL = '1F4E78', AZUL_CLARO = 'DDEBF7', CINZA = 'F2F2F2', AMARELO = 'FFF2CC';
const LARG = 9638; // A4 com margens de 2 cm, em DXA
const borda = { style: BorderStyle.SINGLE, size: 4, color: 'BFBFBF' };
const bordas = { top: borda, bottom: borda, left: borda, right: borda };

// Números: inteiros sem separador (como vão no .yml), decimais com ponto.
function n(v) {
  if (v === null || v === undefined || v === '') return '-';
  if (typeof v === 'string') return v;
  if (Number.isInteger(v)) return String(v);
  if (Math.abs(v) >= 1) return String(Math.round(v * 100) / 100);
  return Number(v.toPrecision(6)).toString().includes('e') ? v.toFixed(10).replace(/0+$/, '') : String(Number(v.toPrecision(6)));
}
function curto(v) { // leitura rápida: 1,19 bi / 3,4 mi / 12.500
  if (typeof v !== 'number') return '';
  const a = Math.abs(v);
  const br = (x, c) => x.toFixed(c).replace('.', ',');
  if (a >= 1e9) return br(v / 1e9, 2) + ' bi';
  if (a >= 1e6) return br(v / 1e6, 2) + ' mi';
  if (a >= 1e3) return Math.round(v).toLocaleString('pt-BR');
  return br(v, Number.isInteger(v) ? 0 : 2);
}

const P = (texto, op = {}) => new Paragraph({
  spacing: { after: op.after ?? 120, before: op.before ?? 0 },
  keepNext: op.keepNext ?? false,
  children: (Array.isArray(texto) ? texto : [texto]).map(t => typeof t === 'string' ? new TextRun(t) : t),
});
const B = (t) => new TextRun({ text: t, bold: true });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, keepNext: true, spacing: { before: 240, after: 120 }, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 200, after: 100 }, children: [new TextRun(t)] });
const item = (texto) => new Paragraph({ numbering: { reference: 'lista', level: 0 }, spacing: { after: 60 },
  children: (Array.isArray(texto) ? texto : [texto]).map(t => typeof t === 'string' ? new TextRun(t) : t) });

function tabela(cab, linhas, larguras, op = {}) {
  op = { ...op, nLinhas: linhas.length };
  const total = larguras.reduce((a, b) => a + b, 0);
  const cel = (txt, i, j, eCab) => new TableCell({
    borders: bordas,
    width: { size: larguras[j], type: WidthType.DXA },
    shading: eCab ? { fill: AZUL, type: ShadingType.CLEAR, color: 'auto' }
      : (op.destaque && op.destaque(i, j) ? { fill: AMARELO, type: ShadingType.CLEAR, color: 'auto' }
        : (i % 2 ? { fill: CINZA, type: ShadingType.CLEAR, color: 'auto' } : undefined)),
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({
      alignment: (!eCab && /^[-+]?[\d.,]+(%| bi| mi)?$/.test(String(txt))) ? AlignmentType.RIGHT : AlignmentType.LEFT,
      keepNext: !!op.junto && i < op.nLinhas - 1,
      children: [new TextRun({ text: String(txt), bold: eCab, color: eCab ? 'FFFFFF' : undefined, size: 18 })],
    })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: larguras,
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: cab.map((c, j) => cel(c, -1, j, true)) }),
      ...linhas.map((l, i) => new TableRow({ cantSplit: true, children: l.map((c, j) => cel(c, i, j, false)) })),
    ],
  });
}
const espaco = () => new Paragraph({ spacing: { after: 120 }, children: [] });

const filhos = [];
const add = (...x) => filhos.push(...x);

// ---------------------------------------------------------------- capa
add(new Paragraph({ alignment: AlignmentType.LEFT, spacing: { after: 80 },
  children: [new TextRun({ text: 'Economia Rede Nexus', bold: true, size: 44, color: AZUL })] }));
add(P([new TextRun({ text: 'Tabela de preços para colocar nos plugins (versão 1)', size: 28 })], { after: 60 }));
add(P([new TextRun({ text: '21/10/2026. Todos os números saíram do simulador e foram conferidos.', italics: true, color: '595959' })], { after: 240 }));

// ---------------------------------------------------------------- como usar
add(H1('Como usar este documento'));
add(item('Cada tabela diz em qual arquivo e em qual campo o número vai. Os nomes dos campos são os mesmos que vocês já usam.'));
add(item('Copiem os números exatamente como estão. Números grandes estão sem pontos (ex.: 15600 = quinze mil e seiscentos). Casas decimais usam ponto, igual ao arquivo .yml.'));
add(item('Na coluna "leitura" o número aparece do jeito fácil de ler (ex.: 1,19 bi). Essa coluna não vai para o arquivo.'));
add(item('Preço dos encantamentos: igual ao formato que vocês já usam (faixa de níveis, custo no começo da faixa e aumento por nível).'));
add(item('Conferência feita: o preço de cada um dos 1.000 níveis calculado pelas faixas é igual ao que o simulador usou; nenhum preço cai de um nível para o seguinte; as caixas somam 100%.'));
add(item('O que não é preço (correções e ideias) ficou separado no final, na parte "Sugestões". Só façam se quiserem.'));

// ---------------------------------------------------------------- resumo
const r = d.resumo;
add(H1('Resumo'));
add(item(['Jogador ativo leva ', B(`${Math.round(r.horas_ativo)} horas`), ' de jogo para chegar no Dragão X (umas ', B(`${String(r.semanas.ativo).replace('.', ',')} semanas`), ' jogando 4 h por dia).']));
const sem = (x) => String(x).replace('.', ',');
add(item(`Muito ativo (7 h/dia): ${sem(r.semanas.muito_ativo)} semanas. Hardcore (10 h/dia): ${sem(r.semanas.hardcore)} semanas. Casual (1,5 h/dia): ${sem(r.semanas.casual)} semanas (acima da meta de 12 a 18; melhorar isso precisaria de um bônus diário, que é plugin novo).`));
add(item(`Quem corre só para rank (${Math.round(r.horas_rush)} h) e quem otimiza tudo (${Math.round(r.horas_otim)} h) terminam quase junto com o jogador normal: não tem atalho.`));
add(item(`Prestígio com os mesmos preços dos ranks: cada volta leva umas ${Math.round(r.prestigio_horas.reduce((a, b) => a + b, 0) / r.prestigio_horas.length)} h, porque a picareta e o money continuam.`));
add(item(`No Dragão X, o jogador normal tem os encantamentos entre o nível ${Math.min(...Object.values(r.niveis_fim).filter(x => x > 2))} e ${Math.max(...Object.values(r.niveis_fim))}. O 1000 fica para os prestígios.`));

// ---------------------------------------------------------------- ranks
add(new Paragraph({ children: [new PageBreak()] }));
add(H1('1. Ranks'));
add(P(['Arquivo ', B('Rankup/ranks.yml'), ', campo ', B('custo: money'), ' de cada rank (prestígio 1). O preço é para sair do rank e ir para o próximo. O preço do Dragão X é o preço de prestigiar. Nos prestígios, usem os mesmos preços.']));
add(tabela(['Rank', 'Chave no arquivo', 'money', 'leitura', 'horas no rank'],
  d.ranks.map(x => [x.rank, x.chave, n(x.preco), curto(x.preco), x.horas ? x.horas.toFixed(2).replace('.', ',') : '-']),
  [2400, 2000, 2000, 1800, 1438]));

// ---------------------------------------------------------------- minas
add(H1('2. Minas'));
add(P(['Arquivo ', B('MinaReset/blocos.yml'), ', campos ', B('moeda: money: quantia'), ' e ', B('moeda: gemas: quantia'), '. A chance da chave continua 0.10 (não mexer).']));
add(tabela(['Mina', 'Bloco', 'money por bloco', 'gemas por bloco'],
  d.minas.map(x => [x.mina, x.bloco, n(x.money), n(x.gemas)]), [3000, 2638, 2000, 2000]));
add(P('A mina VIP paga o dobro da Cidadão, como vocês pediram. Na VIP, troquem o formato antigo (quantia 2000 de gemas) pelo mesmo formato das outras minas (money e gemas separados).', { before: 120 }));

// ---------------------------------------------------------------- picareta
add(new Paragraph({ children: [new PageBreak()] }));
add(H1('3. Picareta'));
add(H2('3.1 EXP por bloco'));
add(P(['Arquivo ', B('Encantamentos/evolutivos.yml'), ', picareta, ', B('exp-base: itens-exp'), '. A picareta ganha EXP em todas as minas, mais nas minas avançadas. Hoje o nível da picareta só serve para liberar os encantamentos (tabela 3.3).']));
add(tabela(['Bloco', 'Mina', 'EXP por bloco'],
  Object.entries(d.exp).map(([b, v]) => [b, { STAINED_CLAY: 'Cidadão e Explorador', COBBLESTONE: 'Guerreiro', LAPIS_BLOCK: 'Tritão', PRISMARINE: 'Guardião', GOLD_BLOCK: 'Monge', IRON_BLOCK: 'Avatar', QUARTZ_BLOCK: 'Yeti', COAL_BLOCK: 'Necromante', REDSTONE_BLOCK: 'Dragão', EMERALD_BLOCK: 'VIP' }[b] || '', n(v)]),
  [3200, 3638, 2800]));

add(H2('3.2 Fortuna Aprimorada, Gemado e Chaveiro'));
add(P(['Arquivo ', B('Encantamentos/encantamentos.yml'), ', campo ', B("booster: '1-1000'"), '. Mesmo formato de hoje: quantidade e aumento por nível iguais.']));
add(tabela(['Encantamento', 'Chave no arquivo', 'quantidade', 'aumento-por-nivel', 'no nível 1000'],
  d.boost.map(x => [x.nome, x.chave, n(x.quantidade), n(x.aumento), `+${x.no_1000}%`]), [2300, 2000, 1700, 1900, 1738]));

add(H2('3.3 Encantamentos de área: chance e liberação'));
add(P(['Arquivo ', B('Encantamentos/encantamentos.yml'), ", campo ", B("efeito: '1-1000'"), ". Coloquem o mesmo número em chance e em aumento-por-nivel (igual ao formato de hoje). O radios continua igual ao de vocês. ", B('Libera na picareta'), ": em ", B('level-necessario'), ", do nível 0 até o anterior a esse, nivel-máximo 0; dali para cima, nivel-máximo 1000."]));
add(tabela(['Encantamento', 'Chave', 'chance e aumento', 'radios', 'libera na picareta', 'chance no 1000', 'ativações/h no 1000'],
  d.area.map(x => [x.nome, x.chave, n(x.chance), x.radios, String(x.libera), `${n(x.chance_1000)}%`, n(x.ativ_h_1000)]),
  [1700, 1500, 1500, 1000, 1200, 1300, 1438]));
add(P('Atenção: a Detonação Nuclear quebra a mina inteira (uns 600 mil blocos de uma vez). No nível 1000 isso acontece mais ou menos 1 vez a cada 25 horas por jogador. Testem o lag antes de liberar.', { before: 120 }));

add(H2('3.4 Preço de cada nível (upgrade)'));
add(P(['Arquivo ', B('Encantamentos/encantamentos.yml'), ', campo ', B('upgrade'), ' de cada encantamento. Uma linha por faixa: em ', B('custo'), ' vai o preço no começo da faixa e em ', B('aumento'), ' quanto sobe a cada nível. A faixa 0-0 é o primeiro nível (nos encantamentos de área, é o preço de liberar). Os campos requisitos e aumento-requisitos ficam vazios ({}).']));
for (const [nome, faixas] of Object.entries(d.precos)) {
  add(new Paragraph({ keepNext: true, spacing: { before: 160, after: 60 }, children: [B(nome)] }));
  add(tabela(['faixa', 'custo money', 'aumento money', 'custo gemas', 'aumento gemas', 'money no fim (leitura)'],
    faixas.map(f => { const [a, b] = f.faixa.split('-').map(Number); const fim = f.money + f.aum_money * (b - a);
      return [f.faixa, n(f.money), n(f.aum_money), n(f.gemas), n(f.aum_gemas), curto(fim)]; }),
    [1300, 1700, 1600, 1700, 1600, 1738], { junto: true }));
}
add(H2('3.5 Speed e Haste'));
add(P(['Campo ', B('upgrade'), '. A chance de 5 que vocês usam já deixa o efeito praticamente contínuo (são uns 18 blocos por segundo), então não precisa mexer na chance.']));
add(tabela(['Encantamento', 'nível', 'faixa', 'custo money', 'custo gemas'],
  d.fixos.map(x => [x.nome, String(x.nivel), x.faixa, n(x.money), n(x.gemas)]), [2400, 1300, 1500, 2200, 2238]));

add(H2('3.6 Skins da picareta'));
add(P(['Arquivo ', B('Encantamentos/evolutivos.yml'), ', picareta, ', B('skins'), '. Bônus = ', B('bonus: money'), ' (em %); preço = ', B('custo: money'), '. Na descrição (item-menu), troquem o "Dinheiro: +X%" pelo bônus abaixo e tirem as linhas de Gemas e "Poder especial", que não existem no plugin.']));
add(tabela(['Skin', 'bonus money (%)', 'custo money'],
  d.skins.map(s => [`skin-${s.skin}`, String(s.bonus_pct), s.preco_money ? n(s.preco_money) : 'grátis (inicial)']), [3200, 3200, 3238]));

// ---------------------------------------------------------------- plantações
add(new Paragraph({ children: [new PageBreak()] }));
add(H1('4. Plantações'));
add(P(['Arquivo ', B('Armazem/armazem.yml'), ', plantações, campo ', B('moedas'), ' (money e sementes que o jogador recebe por unidade vendida). "Compra" é o preço para comprar a plantação uma vez. "Loja" é o preço da semente avulsa, alto de propósito para ninguém lucrar comprando e revendendo.']));
add(tabela(['Plantação', 'libera no rank', 'money', 'sementes', 'compra (1 vez)', 'loja por unidade', 'colheitas por hora'],
  d.plantas.map(x => [x.nome, x.libera, n(x.money), n(x.sementes), x.compra ? n(x.compra) : '-', x.loja ? n(x.loja) : '-', x.por_hora ? n(x.por_hora) : 'automático']),
  [1300, 1500, 1000, 1100, 1600, 1500, 1638]));
add(H2('Lucro do armazém por rank'));
add(P(['Para o preço da plantação acompanhar o rank, cada grupo do LuckPerms recebe a permissão ', B('armazem.lucro.money@X'), ' (o próprio plugin do armazém tem isso). Ex.: grupos rank30 a rank39 recebem armazem.lucro.money@217.0.']));
add(tabela(['Rank', 'grupos do LuckPerms', 'X (lucro %)'],
  d.lucro.map(x => { const i = Number(x.grupos.replace('rank', '')) || 0; return [x.rank, `rank${i} a rank${i + 9}`, n(x.lucro)]; }), [3200, 3600, 2838]));
add(P('Liberar a colheita por rank: em Armazem/config.yml existe permissao-para-plantar-e-quebrar e uma permissão por plantação (nether_warts.use, carrot.use, melon_steam.use, sugar_cane_block.use, cactus.use). Deem cada permissão aos grupos a partir do rank da tabela acima e depois liguem a opção.', { before: 120 }));

add(H2('Cacto e armazém'));
add(P(`O cacto produz sozinho e para quando o armazém enche. Proposta de limite de cactos por jogador e quanto rende (o lucro por rank já está incluso):`));
add(tabela(['Nível', 'cactos', 'libera em', 'money por hora', '% da mina'],
  d.cacto.map(c => [String(c.nivel), String(c.cactos), c.libera, curto(c.money_h), `${String(c.vs_mina_pct).replace('.', ',')}%`]), [1200, 1500, 2600, 2400, 1938]));
add(P(['Armazém: começa com ', B(n(d.armazem.inicial)), '. Item da Cenoura ("Limite de Armazém"): ', B(`+${n(d.armazem.por_item)}`), ' por item, chance de ', B(`${n(d.armazem.chance_item)}%`), ` por colheita de cenoura (uns ${String(d.armazem.itens_h).replace('.', ',')} itens por hora). Máximo: `, B(n(d.armazem.maximo)), '. Com isso o armazém guarda no máximo umas 8 h de cacto: ficar AFK mais que isso não rende mais.'], { before: 120 }));

// ---------------------------------------------------------------- combate
add(new Paragraph({ children: [new PageBreak()] }));
add(H1('5. Spawners e almas'));
add(P(['Preço do spawner: loja. Almas por cabeça: ', B('Armazem/armazem.yml'), ', spawners, ', B('moedas: almas'), ' (e money 0).']));
add(tabela(['Spawner', 'libera em', 'preço (money)', 'almas por cabeça', 'almas por hora (1 spawner)'],
  d.spawners.map(s => [s.nome, s.libera, n(s.preco), n(s.almas_cabeca), n(s.almas_h)]), [1700, 2000, 2000, 1800, 2138]));
add(P('Limite de spawners por jogador (sobe com o item "Stack de Spawners" dos bosses): ' +
  Object.entries(d.limite_spawners).map(([k, v]) => `${k} ${v}`).join(', ') + '.', { before: 120 }));

add(H1('6. Matadoras'));
add(P('Não veio config da Matadora, então estes são os valores para quem for configurar. Cada uma exige a anterior.'));
add(tabela(['Matadora', 'dano', 'libera em', 'money', 'almas', 'Fragmentos de Arena'],
  d.matadoras.map(m => [String(m.matadora), n(m.dano), m.libera, n(m.preco_money), n(m.preco_almas), String(m.fragmentos_arena)]),
  [1200, 1400, 2000, 1800, 1700, 1538]));

add(H1('7. Bosses'));
add(P(['Arquivo ', B('Bosses/bosses.yml'), '. ', B('vida'), ' = dano da Matadora recomendada x 4 golpes por segundo x tempo de luta. Nos drops: cabeça do boss sempre (100), ', B('Limite de Armazém'), ' e ', B('Stack de Spawners'), ' com 50% de chance na quantidade abaixo, e a chave com 20%.']));
add(tabela(['Boss', 'nome no arquivo', 'vida', 'luta (s)', 'Matadora', 'Limite de Armazém +', 'Stack de Spawners +', 'chave (20%)'],
  d.bosses.map(b => [String(b.boss), b.chave_config, n(b.vida), String(b.luta_s), String(b.matadora), String(b.limite), String(b.stack), b.chave_caixa || '-']),
  [700, 1700, 1400, 900, 1000, 1400, 1400, 1138]));

// ---------------------------------------------------------------- caixas
add(new Paragraph({ children: [new PageBreak()] }));
add(H1('8. Caixas'));
add(P(['Arquivo ', B('Caixas/caixas.yml'), '. Só muda a chance de cada prêmio (o número antes de \\padrao\\nada), para somar 100%. Mantive a proporção que vocês já tinham. Os prêmios estão na mesma ordem do arquivo.']));
for (const [nome, itens] of Object.entries(d.caixas)) {
  add(new Paragraph({ keepNext: true, spacing: { before: 160, after: 60 }, children: [B(`Caixa ${nome}`)] }));
  if (nome === 'livro') {
    add(P(`Os ${itens.length} livros têm a mesma chance: ${itens[0].chance} cada (o último ${itens[itens.length - 1].chance}, para fechar 100).`));
    continue;
  }
  add(tabela(['Prêmio (na ordem do arquivo)', 'chance'], itens.map(i => [i.item, String(i.chance)]), [7438, 2200], { junto: itens.length <= 22 }));
}

// ---------------------------------------------------------------- requisitos
add(H1('9. Requisitos extras de rank (opcional)'));
add(P('Para ninguém subir só juntando money AFK, os ranks V e X a partir do Tritão podem pedir itens além do money. Precisa do formato do campo itens do ranks.yml (ver Testes).'));
add(tabela(['Rank', 'cabeças de spawner', 'cabeça de boss', 'fragmentos'],
  d.requisitos.map(q => [q.posicao, q.cabecas || '-', q.boss || '-', q.fragmentos || '-']), [2000, 3000, 2400, 2238], { direita: false }));

// ---------------------------------------------------------------- sugestões e testes
add(H1('10. Sugestões (não são preço, façam se quiserem)'));
add(item('Caixa mineracao: o item-chave espera a chave com chave☢vip, mas a mina dá a chave com chave☢mineracao. Trocar para chave☢mineracao.'));
add(item('Menu da picareta: tirar o botão "Multiplicador de Prisma" (o encantamento booster_prisma não existe).'));
add(item('Armaduras evolutivas: tirar o botão de booster_money, já que vocês não usam booster de money.'));
add(item('Spawners/config.yml: stack-por-player está false (limite infinito). Para valer o limite por jogador, trocar para true.'));
add(item('Spawners de Porco, Zumbi, Esqueleto e Golem: hoje soltam carne, osso etc. no chão. Para virar almas no armazém, devem soltar a cabeça com destino armazem (igual a Vaca).'));

add(H1('11. Testes antes do servidor oficial'));
add(item('Fortuna Aprimorada no 1000: quebrar 100 blocos na mina Cidadão. Deve entrar uns 400 de money. Se entrar outra coisa, me avisem (o jeito do bônus somar muda os números).'));
{
  const fx = Object.entries(d.precos).find(([k]) => k.startsWith('Fortuna'))[1].find(f => f.faixa === '251-500');
  const preco = fx.money + fx.aum_money * (299 - 251);
  add(item(`Conferir um preço no menu: com a Fortuna Aprimorada no nível 299, o próximo nível deve custar ${preco} de money (faixa 251-500: ${fx.money} + ${fx.aum_money} x 48). Se o menu mostrar outro valor, o plugin faz a conta da faixa de outro jeito e eu ajusto.`));
}
add(item('Print do buraco de cada encantamento de área numa parede lisa (quantos blocos quebra de verdade).'));
add(item('No /rankup editar, colocar 1 item de custo num rank e mandar o trecho do ranks.yml (para os requisitos da seção 9).'));

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Arial', size: 20 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 30, bold: true, color: AZUL, font: 'Arial' }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 24, bold: true, color: AZUL, font: 'Arial' }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: 'lista', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
    style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: 'Economia Rede Nexus v1  |  página ', size: 16, color: '808080' }),
        new TextRun({ children: [PageNumber.CURRENT], size: 16, color: '808080' })] })] }) },
    children: filhos,
  }],
});

Packer.toBuffer(doc).then(buf => {
  const destino = path.join(ECON, 'saida', 'Precos_Economia_Rede_Nexus.docx');
  fs.writeFileSync(destino, buf);
  console.log(destino);
});
