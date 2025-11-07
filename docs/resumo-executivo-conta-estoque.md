# Resumo Executivo - Script Conta Estoque

## O que faz este script?

Este script SQL **calcula e distribui custos de alimentação** (ingredientes/dietas) para animais em confinamento, gerando um relatório de baixa de estoque com classificação contábil completa.

## Resultado Final

O script produz uma tabela com as seguintes informações por ingrediente:

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| **data** | Data da baixa | 2025-07-01 |
| **descricao** | Nome do ingrediente | Milho Moído |
| **quantidade** | Quantidade ajustada (kg) | 1,250.50 |
| **centro_custo** | Centro de custo | Confinamento A |
| **conta_contabil** | Conta contábil | 1.1.01.001 |
| **item_contabil** | Item contábil | Alimentação |
| **classe_valor** | Classe de valor | Custo Direto |
| **codigo_externo** | Código ERP | PROD-001 |
| **unidade** | Unidade de medida | KG |
| **porcentagem_perda** | % de perda | 2.5 |
| **conta_estoque** | Conta estoque animal | Machos 12-24 meses |
| **codigo_externo_conta_estoque** | Código conta estoque | CE-M12-24 |
| **ativo_conta_estoque** | Tipo de ativo | Estoque |

---

## Processo em 5 Passos Principais

### 1️⃣ Identificar Animais e Quantidades Reais
- Busca **animais ativos** na fazenda
- Obtém **quantidade real consumida** de cada ingrediente

### 2️⃣ Mapear Distribuição de Alimento
- Identifica qual **dieta** foi fornecida a cada **lote**
- Relaciona lotes com **animais individuais**
- Determina a **categoria operacional** de cada animal

### 3️⃣ Classificar Contabilmente
- Mapeia cada animal para sua **conta estoque** baseado em:
  - Sexo (M/F)
  - Idade (em meses)
  - Grupo genético (raça)
  - Fazenda
  - Categoria operacional
- Define **centro de custo** de baixa

### 4️⃣ Calcular Consumo com Ajustes
- Aplica ajuste de **Matéria Seca (MS)** nos ingredientes
- Adiciona **percentual de perda** histórico
- Busca informações de **custo e classificação contábil**
- Realiza **rateio proporcional** entre lotes

### 5️⃣ Ajustar pela Quantidade Real
- Compara quantidade **planejada** vs **real medida**
- Ajusta proporcionalmente todas as distribuições
- Garante que o total **bata com o consumo real**

---

## Principais Conceitos

### 🌾 Matéria Seca (MS)
**Problema:** Ingredientes contêm água/umidade variável  
**Solução:** Ajusta quantidade para considerar apenas o nutriente efetivo

**Exemplo:**
- Silagem com 30% MS
- 100 kg de silagem = 30 kg de matéria seca
- Se `flag_ms = 1`, quantidade ajustada = 100 × 0.30 = 30 kg

### 📊 Conta Estoque
**Problema:** Custos precisam ser alocados corretamente por tipo de animal  
**Solução:** Mapeia animais para contas contábeis específicas

**Exemplo:**
- Macho, 18 meses, Nelore, Fazenda A, Em Engorda
- → **Conta:** "Machos Nelore 12-24m Engorda"
- → **Tipo:** "Estoque" (para venda)

vs.

- Fêmea, 36 meses, Angus, Fazenda B, Reprodutora
- → **Conta:** "Fêmeas Angus Matriz"
- → **Tipo:** "Ativo Imobilizado" (permanente)

### 🎯 Rateio Proporcional
**Problema:** Múltiplos lotes podem compartilhar o mesmo carregamento  
**Solução:** Divide igualmente entre os lotes

**Exemplo:**
- Carregamento de 1.000 kg de milho
- Usado por 4 lotes
- Cada lote recebe: 1.000 ÷ 4 = 250 kg

### ⚖️ Ajuste pela Quantidade Real
**Problema:** Quantidade planejada ≠ quantidade realmente consumida  
**Solução:** Ajusta proporcionalmente todas as alocações

**Exemplo:**
- Planejado: 1.000 kg de milho total
- Medido real: 950 kg
- Fator de ajuste: 950 ÷ 1.000 = 0.95
- Lote que tinha 250 kg → 250 × 0.95 = 237.5 kg

---

## Fluxo Simplificado

```
┌────────────────────────────────────────────────────────┐
│ ENTRADA: Data + Fazenda                                │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 1. Buscar Animais Ativos                               │
│    - Status ativo                                      │
│    - Com localização válida                            │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 2. Buscar Quantidade Real Consumida                    │
│    - Por ingrediente                                   │
│    - Medição efetiva                                   │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 3. Mapear Distribuição                                 │
│    - Qual lote recebeu qual dieta                      │
│    - Quais animais estão em cada lote                  │
│    - Calcular idade e categorizar animais              │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 4. Classificar Contabilmente                           │
│    - Determinar conta estoque de cada animal           │
│    - 5 critérios: Sexo + Idade + Raça + Local + Cat.  │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 5. Calcular Consumo de Ingredientes                    │
│    - Aplicar ajuste de Matéria Seca                    │
│    - Adicionar percentual de perda                     │
│    - Buscar classificação contábil e custos            │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 6. Consolidar e Ratear                                 │
│    - Agregar por dimensões                             │
│    - Ratear entre lotes quando necessário              │
│    - Filtrar baixas já processadas                     │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 7. Ajustar pela Quantidade Real                        │
│    - Comparar planejado vs real                        │
│    - Calcular fator de ajuste                          │
│    - Aplicar proporcionalmente                         │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ 8. Agregar Resultado Final                             │
│    - Agrupar por todas as dimensões                    │
│    - Somar quantidades ajustadas                       │
└────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────┐
│ SAÍDA: Relatório de Baixa de Estoque                   │
│        Com classificação contábil completa             │
└────────────────────────────────────────────────────────┘
```

---

## Casos de Uso

### ✅ Uso Correto
1. **Gerar relatório de baixa de estoque diária**
   - Input: Data + Fazenda
   - Output: Relatório com classificação contábil

2. **Análise de custo de alimentação**
   - Por lote
   - Por categoria de animal
   - Por centro de custo

3. **Integração com ERP**
   - Lançamentos contábeis automáticos
   - Classificação por conta estoque

### ⚠️ Limitações Atuais

1. **Data Hardcoded**
   ```sql
   WHERE CAST(car.data as date) = '2025-07-01'
   ```
   ❌ Problema: Data fixa no código  
   ✅ Solução: Parametrizar a data

2. **Localidade Hardcoded**
   ```sql
   WHERE id_fk_localidade = 25984511002902
   ```
   ❌ Problema: Fazenda específica  
   ✅ Solução: Aceitar como parâmetro

3. **Transação com ROLLBACK**
   ```sql
   BEGIN TRAN
   -- ... código ...
   ROLLBACK
   ```
   ❌ Problema: Nenhuma alteração é persistida  
   ✅ Solução: Trocar para COMMIT ou remover transação

4. **Performance**
   - 12 tabelas temporárias sequenciais
   - Índices apenas em #animais
   - ✅ Solução: Adicionar índices em outras temp tables

---

## Otimizações Recomendadas

### 1. Parametrização
```sql
DECLARE @DataInicio DATE = '2025-07-01'
DECLARE @DataFim DATE = '2025-07-01'
DECLARE @IdFazenda BIGINT = 25984511002902
```

### 2. Índices Adicionais
```sql
-- Otimizar joins
CREATE INDEX idx_data_ingrediente 
  ON #quantidades (data, id_fk_ingrediente)

CREATE INDEX idx_data_lote 
  ON #dados_consolidados (data, id_fk_lote)
```

### 3. Estatísticas
```sql
-- Após criar tabelas temporárias grandes
UPDATE STATISTICS #dados_calc
UPDATE STATISTICS #tratos_por_dieta
```

### 4. Eliminar Processamento Duplicado
- Tabela #dados_consolidados tem 3 níveis de subquery
- Poderia ser simplificado

---

## Perguntas Frequentes

### ❓ Por que o script tem ROLLBACK?
**Resposta:** É um script de consulta/relatório. Não deve alterar dados permanentemente. O ROLLBACK garante que qualquer efeito colateral seja desfeito.

### ❓ O que é Matéria Seca (MS)?
**Resposta:** É o conteúdo nutricional efetivo do alimento, excluindo água. Importante porque silagem pode ter 70% de água, então 100kg de silagem = apenas 30kg de nutrientes.

### ❓ Por que ajustar pela quantidade real?
**Resposta:** O planejamento (dieta prevista) nem sempre corresponde ao consumo real (medido pela balança). O ajuste garante que os valores contábeis reflitam o que realmente foi consumido.

### ❓ Como funciona o mapeamento de conta estoque?
**Resposta:** É como classificar animais em "gavetas contábeis". Um macho jovem em engorda vai para uma conta diferente de uma fêmea adulta reprodutora. Isso permite análise de custo por tipo de animal.

### ❓ O que é "nested set model" na hierarquia?
**Resposta:** É uma forma de representar árvores (Fazenda → Setor → Curral) usando dois números (h1, h2). Permite buscar todos os descendentes de forma eficiente com apenas uma comparação numérica.

### ❓ Por que há 12 tabelas temporárias?
**Resposta:** O processo é complexo e envolve muitas transformações. Cada tabela temporária representa uma etapa lógica, facilitando depuração e manutenção.

---

## Glossário Rápido

| Termo | Significado |
|-------|-------------|
| **MS** | Matéria Seca (conteúdo nutricional efetivo) |
| **Conta Estoque** | Classificação contábil do animal |
| **Ativo Imobilizado** | Animal de reprodução (permanece na fazenda) |
| **Estoque** | Animal de engorda (será vendido) |
| **Trato** | Refeição/alimentação dos animais |
| **Dieta** | Receita da alimentação (composição) |
| **Lote** | Grupo de animais gerenciado junto |
| **Subcategoria** | Classificação funcional (Engorda, Recria, etc.) |
| **Centro de Custo** | Departamento/área responsável pelo custo |

---

## Próximos Passos Sugeridos

1. ✅ **Parametrizar** datas e localidades
2. ✅ **Adicionar índices** em tabelas temporárias críticas
3. ✅ **Trocar ROLLBACK** por COMMIT se for persistir dados
4. ✅ **Criar stored procedure** para facilitar execução
5. ✅ **Adicionar tratamento de erros** (TRY/CATCH)
6. ✅ **Documentar parâmetros** esperados
7. ✅ **Criar testes unitários** para validar cálculos
8. ✅ **Monitorar performance** em produção

---

## Exemplo de Uso Ideal

```sql
-- Versão parametrizada (futura)
EXEC sp_gerar_relatorio_baixa_estoque
    @DataInicio = '2025-07-01',
    @DataFim = '2025-07-01',
    @IdFazenda = 25984511002902,
    @PersistirDados = 0  -- 0 = Apenas consulta, 1 = Grava na base

-- Resultado: Tabela com classificação contábil completa
```

---

## Conclusão

Este script é um **sistema sofisticado de custeio pecuário** que:

✅ Garante precisão contábil  
✅ Ajusta por medições reais  
✅ Classifica corretamente por tipo de animal  
✅ Considera perdas e variações de umidade  
✅ Integra múltiplas fontes de dados

**Complexidade:** Alta  
**Valor:** Essencial para gestão financeira e análise de custos  
**Manutenibilidade:** Boa (com documentação adequada)
