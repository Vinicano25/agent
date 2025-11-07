# Análise Detalhada - Script Conta Estoque

## Visão Geral
Este script SQL é responsável por calcular e processar informações de **conta estoque** (inventory accounting) no sistema de gerenciamento pecuário. O script utiliza múltiplas tabelas temporárias para processar dados de animais, dietas, ingredientes e movimentações, gerando um relatório consolidado de baixa de estoque.

**Período Analisado:** 2025-07-01 (data fixa no script)  
**Localidade:** ID 25984511002902 (fazenda específica)

---

## Estrutura do Script

O script é composto por **12 tabelas temporárias** que processam dados em etapas sequenciais:

### 1️⃣ **#animais** - Base de Animais Ativos

#### Propósito
Seleciona todos os animais ativos na fazenda, estabelecendo a base para os cálculos de consumo.

#### Consulta
```sql
SELECT ani.*,
       h_pai.id_pk AS id_pk_fazenda 
  INTO #animais
  FROM animal ani 
INNER JOIN localidadehierarquia h ON (ani.id_fk_localidade = h.id_pk
                                  AND h.sync_status = 1)
INNER JOIN localidadehierarquia h_pai ON (h.h1 >= h_pai.h1
                                      AND h.h2 <= h_pai.h2
                                      AND h_pai.sync_status = 1
                                      AND h_pai.id_fk_tipo_localidade = 5000200)
 WHERE ani.sync_status = 1
   AND ani.id_fk_gi_status_animal = 12000200
```

#### Campos Principais
- **ani.***: Todos os campos da tabela animal
- **id_pk_fazenda**: ID da fazenda pai na hierarquia

#### Filtros Aplicados
- `sync_status = 1`: Apenas registros ativos/sincronizados
- `id_fk_gi_status_animal = 12000200`: Status específico do animal (provavelmente "Ativo" ou "Em Confinamento")
- `id_fk_tipo_localidade = 5000200`: Tipo de localidade = Fazenda

#### Hierarquia de Localização
Utiliza nested set model (h1, h2) para navegar na hierarquia de localidades e identificar a fazenda pai de cada animal.

#### Índices Criados
- **Clustered**: `id_pk_fazenda` - Otimiza buscas por fazenda
- **Non-Clustered**: `id_pk` - Otimiza joins com outras tabelas

---

### 2️⃣ **#qtdIngrediente** - Quantidade Total de Ingredientes

#### Propósito
Calcula a quantidade total de cada ingrediente utilizado no período específico.

#### Consulta
```sql
SELECT  id_fk_ingrediente,
        SUM(CAR.QUANTIDADE_INGREDIENTE) AS TOTAL
INTO    #qtdIngrediente
FROM    int_cf_imp_trato_item car 
INNER JOIN CF_Dieta d ON (car.id_fk_dieta = d.id_pk)
INNER JOIN LocalidadeHierarquia lh ON (lh.id_pk = car.id_fk_localidade)
WHERE CAST(car.data as date) >= '2025-07-01'
  AND CAST(car.data as date) <= '2025-07-01'
  AND lh.h1 >= 3258
  AND lh.h2 <= 5549
GROUP BY id_fk_ingrediente
```

#### Campos
- **id_fk_ingrediente**: ID do ingrediente
- **TOTAL**: Soma total da quantidade do ingrediente

#### Filtros
- **Data**: 2025-07-01 (mesmo dia início e fim)
- **Hierarquia**: lh.h1 >= 3258 AND lh.h2 <= 5549 (range de localidades)

#### Tabelas Envolvidas
- `int_cf_imp_trato_item`: Itens de trato importados
- `CF_Dieta`: Dietas do confinamento
- `LocalidadeHierarquia`: Hierarquia de localidades

---

### 3️⃣ **#dados_calc** - Dados de Distribuição de Trato

#### Propósito
Captura informações detalhadas sobre a distribuição de dietas por lote e animal.

#### Consulta
```sql
SELECT CAST(dist.data_hora AS DATE) AS data,
       dieta.id_pk AS id_pk_dieta,
       dieta.nome AS nome_dieta,
       dist.id_fk_lote,
       lote.codigo,
       ani.id_pk AS id_pk_animal,
       CAST(ani.data_nascimento AS DATE) AS data_nascimento,
       ani.sexo,
       DATEDIFF(MONTH, CAST(ani.data_nascimento AS DATE),
       CAST(GETDATE() AS DATE)) AS idade_meses,
       ani.id_fk_gi_grupo_genetico,
       ani.id_fk_localidade,
       ani.id_pk_fazenda AS pk_fazenda
  INTO #dados_calc
  FROM cf_imp_trato_novo dist
INNER JOIN cf_dieta dieta ON (dist.id_fk_dieta = dieta.id_pk 
                          AND dieta.sync_status = 1)
INNER JOIN lote_confinamento lote ON (dist.id_fk_lote = lote.id_pk)
INNER JOIN lote_confinamento_itens lote_i ON (lote.id_pk = lote_i.id_fk_lote)
INNER JOIN #animais ani ON (lote_i.id_fk_animal = ani.id_pk)
 WHERE CAST(dist.data_hora AS DATE) BETWEEN '2025-07-01' AND '2025-07-01'
   AND dist.sync_status = 1
```

#### Campos Principais
- **data**: Data da distribuição
- **id_pk_dieta, nome_dieta**: Identificação da dieta
- **id_fk_lote, codigo**: Identificação do lote
- **id_pk_animal**: ID do animal
- **data_nascimento, sexo**: Atributos do animal
- **idade_meses**: Idade calculada em meses
- **id_fk_gi_grupo_genetico**: Grupo genético
- **pk_fazenda**: Fazenda do animal

#### Lógica de Negócio
- Relaciona distribuição de trato → dieta → lote → animais
- Calcula idade em meses usando `DATEDIFF`
- Filtra apenas registros do dia 2025-07-01

---

### 4️⃣ **#categoria_operacional** - Categoria Operacional dos Animais

#### Propósito
Identifica a categoria operacional (subcategoria) de cada animal na data da distribuição.

#### Consulta
```sql
SELECT id_fk_animal,
       categoria_data_distriuicao.id_fk_subcategoria_destino,
       dc.data
  INTO #categoria_operacional
  FROM #dados_calc dc
OUTER APPLY (SELECT TOP 1 id_fk_animal,
                    coh.id_fk_subcategoria_destino
               FROM categoria_operacional_historico coh
              WHERE dc.id_pk_animal = coh.id_fk_animal
                AND CONVERT(DATE, coh.data_alteracao) <= CONVERT(DATE, dc.data)
                AND coh.sync_status = 1
           ORDER BY coh.data_alteracao DESC) categoria_data_distriuicao
```

#### Campos
- **id_fk_animal**: ID do animal
- **id_fk_subcategoria_destino**: Subcategoria operacional aplicável
- **data**: Data de referência

#### Lógica
Utiliza `OUTER APPLY` para buscar a categoria operacional mais recente **antes ou igual à data de distribuição**. Isso garante que o animal seja classificado com a categoria vigente naquele momento.

---

### 5️⃣ **#dados_conta_estoque** - Mapeamento para Conta Estoque

#### Propósito
Mapeia animais para suas respectivas contas contábeis de estoque baseado em critérios múltiplos.

#### Consulta
```sql
SELECT tab.data,
       tab.id_fk_lote,
       tab.tot_ani_lote,
       tab.conta_estoque,
       SUM(TAB.tot_ani_lote) OVER (PARTITION BY tab.data) AS tot_ani_dia,
       SUM(TAB.tot_ani_lote) OVER (PARTITION BY tab.data, tab.id_pk_dieta) AS tot_ani_dia_dieta,
       tab.codigo_externo_conta_estoque,
       tab.ativo_conta_estoque
  INTO #dados_conta_estoque
  FROM (
    SELECT d.data,
           d.id_fk_lote,
           d.id_pk_dieta,
           COUNT(DISTINCT d.id_pk_animal) AS tot_ani_lote,
           contas_estoque.nome AS conta_estoque,
           contas_estoque.codigo_externo AS codigo_externo_conta_estoque,
           contas_estoque.ativo AS ativo_conta_estoque
      FROM #dados_calc d
    INNER JOIN #categoria_operacional co ON (co.id_fk_animal = d.id_pk_animal 
                                         AND CONVERT(date, co.data) = CONVERT(date, d.data))
    LEFT JOIN (SELECT ce.nome,
                      ce.idade_inicial,
                      ce.idade_final,
                      ce.id_fk_gi_grupo_genetico,
                      ce.id_fk_localidade,
                      ce.sync_status,
                      ce.sexo,
                      cce.id_fk_sub_categoria,
                      ce.codigo_externo,
                      ce.ativo
                 FROM custos_conta_estoque ce
           INNER JOIN custos_conta_estoquexsubcategoria cce 
                   ON (cce.id_fk_conta_estoque = ce.id_pk
                   AND cce.sync_status = 1)
              ) contas_estoque 
           ON (d.sexo = contas_estoque.sexo
           AND DATEDIFF(MONTH, d.data_nascimento, d.data) 
               BETWEEN contas_estoque.idade_inicial AND contas_estoque.idade_final
           AND d.id_fk_gi_grupo_genetico = contas_estoque.id_fk_gi_grupo_genetico
           AND d.pk_fazenda = contas_estoque.id_fk_localidade
           AND contas_estoque.sync_status = 1
           AND contas_estoque.id_fk_sub_categoria = co.id_fk_subcategoria_destino)
    GROUP BY d.data, d.id_fk_lote, d.id_pk_dieta,
             contas_estoque.nome, contas_estoque.codigo_externo, contas_estoque.ativo
  ) TAB
```

#### Campos Principais
- **conta_estoque**: Nome da conta contábil
- **tot_ani_lote**: Total de animais no lote
- **tot_ani_dia**: Total de animais no dia (window function)
- **tot_ani_dia_dieta**: Total de animais por dia e dieta (window function)
- **codigo_externo_conta_estoque**: Código externo da conta
- **ativo_conta_estoque**: Flag indicando se é ativo imobilizado (1) ou estoque (0)

#### Critérios de Mapeamento
A conta estoque é determinada por:
1. **Sexo** do animal
2. **Idade** (em meses) deve estar entre idade_inicial e idade_final
3. **Grupo genético**
4. **Fazenda** (localidade)
5. **Subcategoria operacional**

#### Window Functions
- `SUM(...) OVER (PARTITION BY tab.data)`: Total de animais por dia
- `SUM(...) OVER (PARTITION BY tab.data, tab.id_pk_dieta)`: Total de animais por dia e dieta

---

### 6️⃣ **#tratos_por_dieta** - Consumo de Ingredientes por Trato

#### Propósito
Detalha o consumo de ingredientes por dieta, aplicando correções de matéria seca (MS) e buscando informações de custo.

#### Consulta (simplificada)
```sql
SELECT tab.data
     , tab.id_fk_lote
     , CASE WHEN (x.flag_ms = 1) 
            THEN (quantidade_ingrediente * ms_ingrediente)/100 
            ELSE quantidade_ingrediente 
       END AS quantidade_ingrediente
     , tab.id_fk_ingrediente
     , tab.id_fk_dieta
     , tab.ms_ingrediente  
     , CASE WHEN x.flag_ms IS NOT NULL 
            THEN x.flag_ms 
            ELSE p.flag_ms 
       END AS flag_ms
     , p.codigo_externo
     , p.conta_contabil
     , p.item_contabil
     , p.centro_custo
     , p.classe_valor
     , CONVERT(VARCHAR(50), p.descricao) COLLATE Cyrillic_General_CI_AI AS descricao
     , d.nome as nome_dieta
     , CASE WHEN y.centro_custo IS NULL 
            THEN dcc.centro_custo_baixa 
            ELSE y.centro_custo 
       END AS centro_custo_baixa
     , gi_u.descricao as unidade
     , PercentoPerda.porcentagem_perda
  INTO #tratos_por_dieta
  FROM (...)
```

#### Principais Transformações

##### 6.1 Correção de Matéria Seca (MS)
```sql
CASE WHEN (x.flag_ms = 1) 
     THEN (quantidade_ingrediente * ms_ingrediente)/100 
     ELSE quantidade_ingrediente 
END AS quantidade_ingrediente
```
- Se `flag_ms = 1`: Ajusta quantidade pela matéria seca
- Se `flag_ms = 0`: Mantém quantidade original

##### 6.2 Centro de Custo de Baixa
```sql
CASE WHEN y.centro_custo IS NULL 
     THEN dcc.centro_custo_baixa 
     ELSE y.centro_custo 
END AS centro_custo_baixa
```
- Prioriza centro de custo histórico da dieta
- Fallback para centro de custo padrão de baixa

##### 6.3 Porcentagem de Perda (OUTER APPLY)
Busca a porcentagem de perda vigente para o ingrediente na data:
```sql
OUTER APPLY (SELECT p_i.porcentagem_perda AS porcentagem_perda 
               FROM (...)
              WHERE tab.data BETWEEN p_i.data_inicial AND p_i.data_final
                AND tab.id_fk_ingrediente = p_i.id_fk_ingrediente
                AND lh1.h1 >= 3258
                AND lh1.h2 <= 5549
            ) AS PercentoPerda
```

#### Tabelas Envolvidas
- `Historico_Consumo`: Histórico de consumo
- `int_cf_imp_trato_item`: Itens de trato importados
- `Produto`: Informações de custo e classificação
- `Centro_Custo_Dieta_Historico`: Histórico de centro de custo por dieta
- `Ingrediente_Flag_MS`: Flag de matéria seca por ingrediente com vigência
- `Perda_Insumo`: Percentual de perda por insumo com vigência

---

### 7️⃣ **#quantidades** - Agregação de Quantidades

#### Propósito
Agrega quantidades de ingredientes por data, lote e dieta, consolidando informações de custo.

#### Consulta
```sql
SELECT CONVERT(date, q.data) AS data
     , q.descricao
     , q.id_fk_lote
     , SUM(q.quantidade_ingrediente) AS quantidade
     , q.centro_custo_baixa AS centro_custo
     , q.item_contabil
     , q.conta_contabil
     , q.classe_valor
     , q.codigo_externo
     , q.unidade
     , q.id_fk_ingrediente
     , q.id_fk_dieta
     , COALESCE(q.porcentagem_perda, 0) AS porcentagem_perda
  INTO #quantidades
  FROM #tratos_por_dieta q
GROUP BY q.codigo_externo, q.descricao, q.id_fk_lote,
         q.conta_contabil, q.item_contabil, q.classe_valor,
         q.centro_custo_baixa, CONVERT(date, q.data),
         q.unidade, q.id_fk_ingrediente, q.id_fk_dieta,
         q.porcentagem_perda
```

#### Agregação
- **SUM(quantidade_ingrediente)**: Soma total por grupo
- **COALESCE(porcentagem_perda, 0)**: Substitui NULL por 0

#### Agrupamento
Agrupa por todas as dimensões relevantes exceto quantidade.

---

### 8️⃣ **#rel_baixa** - Relatórios de Baixa Existentes

#### Propósito
Busca relatórios de baixa de estoque já processados para evitar duplicação.

#### Consulta
```sql
SELECT centroDeCusto, quantidade, id_fk_ingrediente, 
       data_impresao, perda, id_fk_localidade
  INTO #rel_baixa
  FROM Relatorio_baixa_estoque 
 WHERE CAST(data_impresao as date) >= '2025-07-01'
   AND CAST(data_impresao as date) <= '2025-07-01'
   AND id_fk_localidade = 25984511002902
   AND sync_status = 1
GROUP BY centroDeCusto, quantidade, id_fk_ingrediente, 
         data_impresao, perda, id_fk_localidade
```

#### Uso
Utilizado para filtrar registros já baixados (LEFT JOIN na próxima etapa).

---

### 9️⃣ **#dados_consolidados** - Consolidação e Rateio

#### Propósito
Consolida dados e realiza rateio de quantidades quando múltiplos lotes compartilham a mesma quantidade.

#### Consulta
```sql
SELECT final.data, final.descricao, final.quantidade,
       final.centro_custo, final.item_contabil, final.conta_contabil,
       final.classe_valor, final.codigo_externo, final.unidade,
       final.id_fk_ingrediente, final.porcentagem_perda, final.integracao,
       final.id_fk_lote,
       SUM(final.quantidade) OVER (PARTITION BY final.data, final.id_fk_ingrediente) 
           AS qtd_total_ingrediente
  INTO #dados_consolidados
  FROM (
    SELECT TAB.data, TAB.descricao,
           tab.quantidade / COUNT(id_fk_lote) OVER (PARTITION BY tab.quantidade) AS quantidade,
           TAB.centro_custo, TAB.item_contabil, TAB.conta_contabil,
           TAB.classe_valor, TAB.codigo_externo, TAB.unidade,
           TAB.id_fk_ingrediente, TAB.porcentagem_perda, TAB.integracao,
           TAB.id_fk_lote
      FROM (
        SELECT DISTINCT q.data, q.descricao, q.quantidade,
               q.centro_custo, q.item_contabil, q.conta_contabil,
               q.classe_valor, q.codigo_externo, q.unidade,
               q.id_fk_ingrediente, q.porcentagem_perda,
               '' as integracao, q.id_fk_lote
          FROM #quantidades AS q 
        LEFT JOIN #rel_baixa AS rb 
               ON (q.id_fk_ingrediente = rb.id_fk_ingrediente 
               AND CAST(q.data as date) = CAST(rb.data_impresao as date)  
               AND rb.centroDeCusto = q.centro_custo)
         WHERE q.quantidade > 0
      ) TAB
  ) final
ORDER BY final.data desc, final.centro_custo, final.codigo_externo
```

#### Lógica de Rateio
```sql
tab.quantidade / COUNT(id_fk_lote) OVER (PARTITION BY tab.quantidade)
```
- Divide quantidade pelo número de lotes que compartilham a mesma quantidade
- Isso distribui proporcionalmente o consumo entre lotes

#### Window Function
```sql
SUM(final.quantidade) OVER (PARTITION BY final.data, final.id_fk_ingrediente)
```
- Calcula total do ingrediente por dia para conferência

---

### 🔟 **#dadosFinal** - Dados Finais com Conta Estoque

#### Propósito
Combina dados consolidados com informações de conta estoque e formata para apresentação.

#### Consulta
```sql
SELECT dc.data, dc.descricao,
       CAST(dc.quantidade AS decimal(10,2)) AS quantidade,
       COUNT(dc.quantidade) OVER (PARTITION BY dc.data, dc.quantidade) AS qtd_conta_estoque,
       dc.qtd_total_ingrediente,
       dc.centro_custo, dc.item_contabil, dc.conta_contabil,
       dc.classe_valor, dc.codigo_externo, dc.unidade,
       dc.id_fk_ingrediente, dc.porcentagem_perda,
       '' as integracao,
       ISNULL(ce.conta_estoque, 'Não Encontrada') AS conta_estoque,
       ce.codigo_externo_conta_estoque,
       CASE WHEN ce.ativo_conta_estoque = 1 THEN 'Ativo Imobilizado'
            WHEN ce.ativo_conta_estoque = 0 THEN 'Estoque'
            ELSE NULL
       END AS ativo_conta_estoque,
       ce.tot_ani_dia_dieta,
       ce.tot_ani_dia,
       ce.tot_ani_lote 
  INTO #dadosFinal
  FROM #dados_consolidados dc 
LEFT JOIN #dados_conta_estoque ce 
       ON (dc.data = ce.data AND dc.id_fk_lote = ce.id_fk_lote)
GROUP BY dc.data, dc.descricao, dc.quantidade, dc.qtd_total_ingrediente,
         dc.centro_custo, dc.item_contabil, dc.conta_contabil,
         dc.classe_valor, dc.codigo_externo, dc.unidade,
         dc.id_fk_ingrediente, dc.porcentagem_perda, dc.integracao,
         ce.tot_ani_dia_dieta, ce.tot_ani_dia, ce.tot_ani_lote,
         ISNULL(ce.conta_estoque, 'Não Encontrada'),
         ce.codigo_externo_conta_estoque,
         CASE WHEN ce.ativo_conta_estoque = 1 THEN 'Ativo Imobilizado'
              WHEN ce.ativo_conta_estoque = 0 THEN 'Estoque'
              ELSE NULL
         END
ORDER BY dc.descricao
```

#### Campos Adicionais
- **qtd_conta_estoque**: Contagem de registros por quantidade
- **conta_estoque**: Nome da conta ou 'Não Encontrada'
- **ativo_conta_estoque**: Classificação como 'Ativo Imobilizado' ou 'Estoque'
- **tot_ani_dia_dieta, tot_ani_dia, tot_ani_lote**: Totalizadores de animais

---

### 1️⃣1️⃣ **#result** - Ajuste Proporcional por Quantidade Real

#### Propósito
Ajusta as quantidades proporcionalmente baseado na quantidade real medida (#qtdIngrediente).

#### Consulta
```sql
SELECT data, descricao,
       (quantidade * (QI.TOTAL / SUM(QUANTIDADE) OVER (PARTITION BY DF.id_fk_ingrediente))) 
           as quantidade,
       centro_custo, item_contabil, conta_contabil,
       classe_valor, codigo_externo, unidade,
       DF.id_fk_ingrediente, porcentagem_perda, integracao,
       conta_estoque, codigo_externo_conta_estoque, ativo_conta_estoque
  INTO #result
  FROM #dadosFinal DF
  JOIN #qtdIngrediente QI ON DF.id_fk_ingrediente = QI.id_fk_ingrediente
 WHERE df.codigo_externo_conta_estoque is not null
```

#### Fórmula de Ajuste
```sql
quantidade * (QI.TOTAL / SUM(QUANTIDADE) OVER (PARTITION BY DF.id_fk_ingrediente))
```

**Explicação:**
- `QI.TOTAL`: Quantidade real do ingrediente (medida)
- `SUM(QUANTIDADE) OVER (...)`: Quantidade calculada/planejada do ingrediente
- **Proporção**: Real / Planejado
- **Quantidade ajustada**: Quantidade original × Proporção

Este ajuste garante que o total distribuído corresponda exatamente ao total consumido.

#### Filtro
`WHERE df.codigo_externo_conta_estoque is not null`: Apenas registros com conta estoque definida.

---

### 1️⃣2️⃣ **Resultado Final** - Agregação Final

#### Propósito
Agrega os resultados por todas as dimensões para eliminar duplicações e produzir o output final.

#### Consulta
```sql
SELECT data, descricao,
       SUM(quantidade) as quantidade,
       centro_custo, item_contabil, conta_contabil,
       classe_valor, codigo_externo, unidade,
       id_fk_ingrediente, porcentagem_perda, integracao,
       conta_estoque, codigo_externo_conta_estoque, ativo_conta_estoque
  FROM #result 
GROUP BY data, descricao, centro_custo, item_contabil,
         conta_contabil, classe_valor, codigo_externo,
         unidade, id_fk_ingrediente, porcentagem_perda,
         integracao, conta_estoque, codigo_externo_conta_estoque,
         ativo_conta_estoque
```

#### Campos do Resultado Final
- **data**: Data da baixa
- **descricao**: Descrição do ingrediente/insumo
- **quantidade**: Quantidade ajustada e agregada
- **centro_custo**: Centro de custo para baixa
- **item_contabil, conta_contabil, classe_valor**: Classificação contábil
- **codigo_externo**: Código do produto no sistema externo
- **unidade**: Unidade de medida
- **id_fk_ingrediente**: ID do ingrediente
- **porcentagem_perda**: Percentual de perda aplicado
- **integracao**: Status de integração (vazio)
- **conta_estoque**: Nome da conta estoque
- **codigo_externo_conta_estoque**: Código da conta estoque
- **ativo_conta_estoque**: Tipo (Ativo Imobilizado ou Estoque)

---

## Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. #animais                                                     │
│    └─> Animais ativos da fazenda                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. #qtdIngrediente                                              │
│    └─> Quantidade real consumida de cada ingrediente           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. #dados_calc                                                  │
│    └─> Distribuição de trato por animal/lote/dieta             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. #categoria_operacional                                       │
│    └─> Categoria operacional vigente de cada animal            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. #dados_conta_estoque                                         │
│    └─> Mapeamento animal → conta estoque                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. #tratos_por_dieta                                            │
│    └─> Consumo de ingredientes com ajuste MS e custos          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. #quantidades                                                 │
│    └─> Agregação de quantidades                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. #rel_baixa                                                   │
│    └─> Baixas já processadas (para filtro)                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. #dados_consolidados                                          │
│    └─> Consolidação com rateio por lote                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 10. #dadosFinal                                                 │
│     └─> União com dados de conta estoque                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 11. #result                                                     │
│     └─> Ajuste proporcional pela quantidade real               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 12. SELECT FINAL                                                │
│     └─> Agregação final para resultado                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Regras de Negócio Principais

### 1. Ajuste de Matéria Seca (MS)
```sql
CASE WHEN flag_ms = 1 
     THEN (quantidade * ms_ingrediente) / 100 
     ELSE quantidade 
END
```
Quando `flag_ms = 1`, a quantidade é ajustada para considerar apenas a matéria seca do ingrediente.

### 2. Mapeamento de Conta Estoque
A conta estoque é determinada por **5 critérios simultâneos**:
- Sexo do animal
- Idade em meses (dentro do range)
- Grupo genético
- Fazenda
- Subcategoria operacional

### 3. Centro de Custo de Baixa
Prioridade de definição:
1. Centro de custo histórico da dieta (se existir para a data)
2. Centro de custo padrão de baixa da dieta

### 4. Porcentagem de Perda
- Busca a porcentagem vigente para o ingrediente na data
- Utiliza histórico com data_inicial e data_final
- Aplica filtro de localidade hierárquica

### 5. Rateio de Quantidades
```sql
quantidade / COUNT(id_fk_lote) OVER (PARTITION BY quantidade)
```
Quando múltiplos lotes compartilham a mesma quantidade planejada, o sistema divide igualmente entre eles.

### 6. Ajuste Proporcional Final
```sql
quantidade * (quantidade_real / quantidade_calculada)
```
Ajusta todas as quantidades distribuídas para que o total corresponda exatamente ao consumo real medido.

---

## Otimizações Aplicadas

### Índices em Tabelas Temporárias
```sql
-- #animais
CREATE CLUSTERED INDEX [id_pk_fazenda] ON [#animais] ([id_pk_fazenda] ASC)
CREATE NONCLUSTERED INDEX [id_pk] ON [#animais] ([id_pk] ASC)
```

### Window Functions
Utilizadas para evitar subqueries e melhorar performance:
- `SUM(...) OVER (PARTITION BY ...)`: Totalizações
- `COUNT(...) OVER (PARTITION BY ...)`: Contagens

### OUTER APPLY
Utilizado para buscas correlacionadas eficientes (categoria operacional e porcentagem de perda).

---

## Pontos de Atenção

### ⚠️ Transação
```sql
BEGIN TRAN
-- ... código ...
ROLLBACK
```
O script está envolto em uma transação que é revertida ao final. **Isso significa que nenhuma alteração é persistida** no banco de dados. Provavelmente é um script de consulta/relatório apenas.

### ⚠️ Data Fixa
Múltiplas ocorrências de `'2025-07-01'` hardcoded. O script deveria ser parametrizado para aceitar datas dinâmicas.

### ⚠️ Localidade Hardcoded
```sql
id_fk_localidade = 25984511002902
lh.h1 >= 3258 AND lh.h2 <= 5549
```
IDs de localidade estão fixos no código. Idealmente deveriam ser parâmetros.

### ⚠️ Performance
- Script processa grande volume de dados com múltiplas tabelas temporárias
- Índices estão sendo criados apenas em #animais
- Outras tabelas temporárias poderiam se beneficiar de índices

---

## Glossário de Termos

| Termo | Significado |
|-------|-------------|
| **MS (Matéria Seca)** | Percentual de matéria seca no ingrediente, exclui água e umidade |
| **Conta Estoque** | Conta contábil onde o custo do animal é registrado |
| **Ativo Imobilizado** | Classificação contábil para animais de reprodução |
| **Estoque** | Classificação contábil para animais de engorda/comercialização |
| **Centro de Custo** | Departamento/área responsável pelo custo |
| **Trato** | Alimentação fornecida aos animais |
| **Dieta** | Composição nutricional do alimento |
| **Lote** | Agrupamento de animais para gestão |
| **Subcategoria Operacional** | Classificação funcional do animal (ex: Recria, Engorda) |
| **Nested Set Model** | Modelo de hierarquia usando h1/h2 para representar árvore |

---

## Conclusão

Este script é um **sistema complexo de custeio de estoque** que:

1. ✅ Identifica animais ativos e suas características
2. ✅ Calcula consumo planejado de ingredientes por lote/dieta
3. ✅ Mapeia animais para contas contábeis baseado em múltiplos critérios
4. ✅ Aplica correções (MS, perda, centro de custo)
5. ✅ Realiza rateio proporcional entre lotes
6. ✅ Ajusta valores pelo consumo real medido
7. ✅ Gera relatório final com classificação contábil completa

O resultado final pode ser utilizado para:
- Lançamentos contábeis de consumo
- Relatórios gerenciais de custo
- Análise de eficiência alimentar
- Controle de estoque de ingredientes
