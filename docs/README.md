# Índice - Documentação Script Conta Estoque

## 📋 Visão Geral

Esta documentação detalha o **script de conta estoque** utilizado no sistema de gerenciamento pecuário. O script é responsável por calcular e alocar custos de alimentação (ingredientes/dietas) aos animais, gerando relatórios de baixa de estoque com classificação contábil completa.

## 📚 Documentos Disponíveis

### 1. 🎯 [Resumo Executivo](./resumo-executivo-conta-estoque.md)
**Recomendado para:** Gestores, analistas de negócio, novos membros da equipe

**Conteúdo:**
- Visão geral simplificada do processo
- Processo em 5 passos principais
- Principais conceitos explicados
- Casos de uso práticos
- FAQ e glossário rápido
- Recomendações de melhorias

**Tempo de leitura:** ~10 minutos

---

### 2. 📊 [Diagramas de Fluxo](./diagrama-fluxo-conta-estoque.md)
**Recomendado para:** Desenvolvedores, arquitetos, analistas técnicos

**Conteúdo:**
- Diagrama geral do processo (Mermaid)
- Fluxos detalhados de cada etapa
- Critérios de mapeamento visualizados
- Timeline de processamento
- Hierarquia de localidades (Nested Set)
- Dependências entre tabelas
- Fórmulas chave ilustradas

**Tempo de análise:** ~15 minutos

---

### 3. 🔍 [Análise Detalhada](./analise-consulta-conta-estoque.md)
**Recomendado para:** DBAs, desenvolvedores SQL, analistas de dados

**Conteúdo:**
- Análise completa das 12 tabelas temporárias
- Propósito e lógica de cada etapa
- Campos, filtros e joins explicados
- Regras de negócio detalhadas
- Otimizações implementadas
- Window functions e técnicas avançadas
- Pontos de atenção para manutenção
- Glossário técnico completo

**Tempo de leitura:** ~45 minutos

---

## 🎓 Como Usar Esta Documentação

### Para Entender o Sistema Rapidamente
1. Leia o **Resumo Executivo** (10 min)
2. Visualize os **Diagramas de Fluxo** (15 min)
3. Consulte seções específicas da **Análise Detalhada** conforme necessário

### Para Manutenção/Desenvolvimento
1. Revise os **Diagramas de Fluxo** para entender arquitetura
2. Estude a **Análise Detalhada** da(s) etapa(s) que precisa modificar
3. Consulte regras de negócio e glossário conforme necessário

### Para Análise de Negócio
1. Leia o **Resumo Executivo** completo
2. Foque na seção "Principais Conceitos"
3. Revise "Casos de Uso" e "Limitações Atuais"

### Para Novos Membros da Equipe
**Dia 1-2:** Resumo Executivo + Diagramas principais  
**Dia 3-5:** Análise Detalhada seções 1-6  
**Dia 6-10:** Análise Detalhada seções 7-12 + Regras de Negócio

---

## 🏗️ Estrutura do Script

### Visão em Alto Nível

```
ENTRADA
   ↓
   ├─→ Animais Ativos (#animais)
   ├─→ Quantidade Real (#qtdIngrediente)
   ↓
PROCESSAMENTO (10 etapas)
   ↓
SAÍDA
   └─→ Relatório de Baixa de Estoque
```

### 12 Tabelas Temporárias Sequenciais

| # | Nome | Propósito | Doc. Detalhada |
|---|------|-----------|----------------|
| 1 | `#animais` | Base de animais ativos | [Seção 1](./analise-consulta-conta-estoque.md#1%EF%B8%8F⃣-animais---base-de-animais-ativos) |
| 2 | `#qtdIngrediente` | Quantidade real consumida | [Seção 2](./analise-consulta-conta-estoque.md#2%EF%B8%8F⃣-qtdingrediente---quantidade-total-de-ingredientes) |
| 3 | `#dados_calc` | Distribuição de trato | [Seção 3](./analise-consulta-conta-estoque.md#3%EF%B8%8F⃣-dados_calc---dados-de-distribuição-de-trato) |
| 4 | `#categoria_operacional` | Categoria vigente | [Seção 4](./analise-consulta-conta-estoque.md#4%EF%B8%8F⃣-categoria_operacional---categoria-operacional-dos-animais) |
| 5 | `#dados_conta_estoque` | Mapeamento conta contábil | [Seção 5](./analise-consulta-conta-estoque.md#5%EF%B8%8F⃣-dados_conta_estoque---mapeamento-para-conta-estoque) |
| 6 | `#tratos_por_dieta` | Consumo com ajustes MS | [Seção 6](./analise-consulta-conta-estoque.md#6%EF%B8%8F⃣-tratos_por_dieta---consumo-de-ingredientes-por-trato) |
| 7 | `#quantidades` | Agregação | [Seção 7](./analise-consulta-conta-estoque.md#7%EF%B8%8F⃣-quantidades---agregação-de-quantidades) |
| 8 | `#rel_baixa` | Baixas existentes (filtro) | [Seção 8](./analise-consulta-conta-estoque.md#8%EF%B8%8F⃣-rel_baixa---relatórios-de-baixa-existentes) |
| 9 | `#dados_consolidados` | Consolidação e rateio | [Seção 9](./analise-consulta-conta-estoque.md#9%EF%B8%8F⃣-dados_consolidados---consolidação-e-rateio) |
| 10 | `#dadosFinal` | União com conta estoque | [Seção 10](./analise-consulta-conta-estoque.md#🔟-dadosfinal---dados-finais-com-conta-estoque) |
| 11 | `#result` | Ajuste proporcional | [Seção 11](./analise-consulta-conta-estoque.md#1%EF%B8%8F⃣1%EF%B8%8F⃣-result---ajuste-proporcional-por-quantidade-real) |
| 12 | `SELECT FINAL` | Resultado agregado | [Seção 12](./analise-consulta-conta-estoque.md#1%EF%B8%8F⃣2%EF%B8%8F⃣-resultado-final---agregação-final) |

---

## 🔑 Conceitos-Chave

### Matéria Seca (MS)
**O que é:** Conteúdo nutricional efetivo do alimento, excluindo água/umidade.

**Por que importa:** Silagem pode ter 70% de água, então 100kg de silagem = apenas 30kg de nutrientes. O ajuste garante cálculo correto de custo nutricional.

**Onde é aplicado:** Etapa 6 (#tratos_por_dieta)

**Doc. completa:** [Resumo Executivo - Seção MS](./resumo-executivo-conta-estoque.md#🌾-matéria-seca-ms)

---

### Conta Estoque
**O que é:** Classificação contábil que determina onde o custo do animal será registrado.

**Por que importa:** Animais diferentes têm finalidades diferentes (reprodução vs venda), e precisam ser contabilizados em contas distintas.

**Critérios:** Sexo + Idade + Raça + Fazenda + Categoria Operacional (5 critérios simultâneos)

**Onde é aplicado:** Etapa 5 (#dados_conta_estoque)

**Doc. completa:** [Resumo Executivo - Seção Conta Estoque](./resumo-executivo-conta-estoque.md#📊-conta-estoque)

---

### Rateio Proporcional
**O que é:** Distribuição igualitária de um carregamento entre múltiplos lotes.

**Por que importa:** Quando um carregamento atende vários lotes, o sistema precisa dividir o custo proporcionalmente.

**Fórmula:** `quantidade ÷ COUNT(lotes)`

**Onde é aplicado:** Etapa 9 (#dados_consolidados)

**Doc. completa:** [Resumo Executivo - Seção Rateio](./resumo-executivo-conta-estoque.md#🎯-rateio-proporcional)

---

### Ajuste pela Quantidade Real
**O que é:** Correção proporcional de todas as alocações baseado no consumo real medido.

**Por que importa:** Garante que o total contabilizado = total realmente consumido (evita divergências).

**Fórmula:** `quantidade × (real ÷ planejado)`

**Onde é aplicado:** Etapa 11 (#result)

**Doc. completa:** [Resumo Executivo - Seção Ajuste](./resumo-executivo-conta-estoque.md#⚖️-ajuste-pela-quantidade-real)

---

## 📖 Glossário Rápido

| Termo | Significado | Link |
|-------|-------------|------|
| **MS** | Matéria Seca (conteúdo nutricional efetivo) | [Detalhes](./resumo-executivo-conta-estoque.md#🌾-matéria-seca-ms) |
| **Conta Estoque** | Classificação contábil do animal | [Detalhes](./resumo-executivo-conta-estoque.md#📊-conta-estoque) |
| **Trato** | Refeição/alimentação dos animais | [Glossário](./analise-consulta-conta-estoque.md#glossário-de-termos) |
| **Dieta** | Receita da alimentação (composição) | [Glossário](./analise-consulta-conta-estoque.md#glossário-de-termos) |
| **Lote** | Grupo de animais gerenciado junto | [Glossário](./analise-consulta-conta-estoque.md#glossário-de-termos) |
| **Subcategoria** | Classificação funcional (Engorda, Recria) | [Glossário](./analise-consulta-conta-estoque.md#glossário-de-termos) |
| **Centro de Custo** | Departamento/área responsável pelo custo | [Glossário](./analise-consulta-conta-estoque.md#glossário-de-termos) |
| **Nested Set Model** | Modelo de hierarquia usando h1/h2 | [Detalhes](./analise-consulta-conta-estoque.md#hierarquia-de-localização) |

---

## ⚡ Otimizações e Melhorias

### Recomendações Prioritárias

#### 🔧 Alta Prioridade
1. **Parametrizar datas e localidades** - Atualmente hardcoded
2. **Adicionar índices em tabelas temporárias** - Apenas #animais tem índices
3. **Trocar ROLLBACK por COMMIT** - Se dados devem ser persistidos

#### 📊 Média Prioridade
4. **Criar stored procedure** - Facilitar execução e manutenção
5. **Adicionar tratamento de erros** - TRY/CATCH para produção
6. **Monitorar performance** - Identificar gargalos

#### 📝 Baixa Prioridade
7. **Simplificar subqueries** - #dados_consolidados tem 3 níveis
8. **Documentar no código** - Adicionar comentários inline
9. **Criar testes unitários** - Validar cálculos automaticamente

**Doc. completa:** [Resumo Executivo - Próximos Passos](./resumo-executivo-conta-estoque.md#próximos-passos-sugeridos)

---

## ⚠️ Pontos de Atenção

### Limitações Conhecidas

1. **Transação com ROLLBACK**
   - Script não persiste alterações
   - Aparenta ser apenas consulta/relatório
   - Trocar para COMMIT se necessário persistir

2. **Valores Hardcoded**
   - Data: `'2025-07-01'` (múltiplas ocorrências)
   - Localidade: `25984511002902`
   - Hierarquia: `h1 >= 3258 AND h2 <= 5549`

3. **Performance**
   - 12 tabelas temporárias sequenciais
   - Grande volume de dados processado
   - Índices apenas em #animais

**Doc. completa:** [Análise Detalhada - Pontos de Atenção](./analise-consulta-conta-estoque.md#pontos-de-atenção)

---

## 📞 Suporte e Contribuições

### Como Contribuir com a Documentação

1. **Encontrou erro ou imprecisão?**
   - Abra uma issue descrevendo o problema
   - Proponha correção via pull request

2. **Quer adicionar exemplos?**
   - Adicione na seção apropriada do documento
   - Mantenha formatação consistente

3. **Quer expandir explicações?**
   - Priorize clareza sobre brevidade
   - Adicione diagramas se possível (Mermaid)

### Estrutura dos Documentos

```
docs/
├── README.md                              (este arquivo)
├── resumo-executivo-conta-estoque.md     (10 min - visão geral)
├── diagrama-fluxo-conta-estoque.md       (15 min - diagramas)
└── analise-consulta-conta-estoque.md     (45 min - análise completa)
```

---

## 🎯 Checklist de Conhecimento

Use este checklist para avaliar seu domínio do script:

### Nível Básico ✅
- [ ] Entendo o propósito geral do script
- [ ] Conheço o fluxo de alto nível (5 passos)
- [ ] Compreendo o conceito de Matéria Seca (MS)
- [ ] Sei o que é uma Conta Estoque
- [ ] Entendo por que há ajuste pela quantidade real

### Nível Intermediário 🔧
- [ ] Conheço as 12 tabelas temporárias e suas funções
- [ ] Compreendo os critérios de mapeamento de conta estoque
- [ ] Entendo o rateio proporcional entre lotes
- [ ] Sei como funciona o Nested Set Model
- [ ] Conheço as otimizações aplicadas (índices, window functions)

### Nível Avançado 💡
- [ ] Posso explicar cada etapa detalhadamente
- [ ] Compreendo todas as window functions utilizadas
- [ ] Sei identificar gargalos de performance
- [ ] Consigo propor melhorias arquiteturais
- [ ] Posso modificar o script com segurança

---

## 📅 Histórico de Revisões

| Data | Versão | Autor | Mudanças |
|------|--------|-------|----------|
| 2025-01-07 | 1.0 | GitHub Copilot | Documentação inicial completa |

---

## 📄 Licença

Esta documentação é parte do projeto interno e segue as mesmas diretrizes de confidencialidade e uso do sistema principal.

---

## 🔗 Links Úteis

- [Resumo Executivo](./resumo-executivo-conta-estoque.md)
- [Diagramas de Fluxo](./diagrama-fluxo-conta-estoque.md)
- [Análise Detalhada](./analise-consulta-conta-estoque.md)

---

**Última atualização:** 2025-01-07  
**Versão:** 1.0  
**Status:** ✅ Completo
