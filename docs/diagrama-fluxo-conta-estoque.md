# Diagrama de Fluxo - Script Conta Estoque

## Fluxo Geral do Processo

```mermaid
graph TD
    A[Início: BEGIN TRAN] --> B[Criar Tabelas Temporárias]
    
    B --> C1[#animais<br/>Base de Animais Ativos]
    B --> C2[#qtdIngrediente<br/>Quantidade Real Consumida]
    
    C1 --> D[#dados_calc<br/>Distribuição de Trato]
    C2 --> K[#result<br/>Ajuste Proporcional]
    
    D --> E[#categoria_operacional<br/>Categoria Vigente]
    
    E --> F[#dados_conta_estoque<br/>Mapeamento Conta Estoque]
    
    D --> G[#tratos_por_dieta<br/>Consumo com Ajustes MS]
    
    G --> H[#quantidades<br/>Agregação]
    
    H --> I[#rel_baixa<br/>Baixas Existentes]
    
    I --> J[#dados_consolidados<br/>Consolidação e Rateio]
    
    J --> L[#dadosFinal<br/>União com Conta Estoque]
    F --> L
    
    L --> K
    
    K --> M[SELECT FINAL<br/>Resultado Agregado]
    
    M --> N[ROLLBACK<br/>Fim da Transação]
    
    style C1 fill:#e1f5fe
    style C2 fill:#e1f5fe
    style K fill:#c8e6c9
    style M fill:#c8e6c9
    style N fill:#ffccbc
```

## Fluxo Detalhado por Etapa

### Etapa 1: Base de Dados

```mermaid
graph LR
    A[animal] -->|INNER JOIN| B[localidadehierarquia]
    B -->|Nested Set<br/>h1, h2| C[localidadehierarquia_pai]
    C --> D[#animais<br/>+ id_pk_fazenda]
    
    D -->|CREATE CLUSTERED INDEX| E[idx_id_pk_fazenda]
    D -->|CREATE NONCLUSTERED INDEX| F[idx_id_pk]
    
    style D fill:#e1f5fe
    style E fill:#fff9c4
    style F fill:#fff9c4
```

### Etapa 2: Quantidade Real de Ingredientes

```mermaid
graph LR
    A[int_cf_imp_trato_item] -->|INNER JOIN| B[CF_Dieta]
    A -->|INNER JOIN| C[LocalidadeHierarquia]
    A -->|Filtro: data = 2025-07-01| D[WHERE]
    C -->|Filtro: h1/h2| D
    D -->|SUM quantidade_ingrediente| E[#qtdIngrediente<br/>GROUP BY ingrediente]
    
    style E fill:#e1f5fe
```

### Etapa 3-4: Distribuição e Categoria

```mermaid
graph TD
    A[cf_imp_trato_novo] -->|INNER JOIN| B[cf_dieta]
    A -->|INNER JOIN| C[lote_confinamento]
    C -->|INNER JOIN| D[lote_confinamento_itens]
    D -->|INNER JOIN| E[#animais]
    E -->|Calc: DATEDIFF idade_meses| F[#dados_calc]
    
    F -->|OUTER APPLY| G[categoria_operacional_historico]
    G -->|TOP 1 ORDER BY data DESC| H[#categoria_operacional]
    
    style F fill:#e1f5fe
    style H fill:#e1f5fe
```

### Etapa 5: Mapeamento para Conta Estoque

```mermaid
graph TD
    A[#dados_calc] -->|INNER JOIN| B[#categoria_operacional]
    A -->|LEFT JOIN| C[custos_conta_estoque]
    C -->|INNER JOIN| D[custos_conta_estoquexsubcategoria]
    
    E[Critérios de Match] --> F{5 Condições}
    F -->|1| G[Sexo]
    F -->|2| H[Idade entre min/max]
    F -->|3| I[Grupo Genético]
    F -->|4| J[Fazenda]
    F -->|5| K[Subcategoria]
    
    G --> L[#dados_conta_estoque]
    H --> L
    I --> L
    J --> L
    K --> L
    
    L -->|Window: SUM OVER| M[tot_ani_dia<br/>tot_ani_dia_dieta]
    
    style L fill:#e1f5fe
    style M fill:#fff9c4
```

### Etapa 6: Ajustes de Matéria Seca e Custos

```mermaid
graph TD
    A[Historico_Consumo] -->|INNER JOIN| B[int_cf_imp_trato_item]
    B -->|INNER JOIN| C[Produto]
    B -->|INNER JOIN| D[CF_Dieta]
    
    E[Ingrediente_Flag_MS] -->|LEFT JOIN<br/>Temporal| F{flag_ms = 1?}
    F -->|Sim| G[qtd * ms / 100]
    F -->|Não| H[qtd original]
    
    I[Centro_Custo_Dieta_Historico] -->|LEFT JOIN<br/>Temporal| J{Centro Custo?}
    J -->|Existe| K[centro_custo histórico]
    J -->|NULL| L[centro_custo_baixa padrão]
    
    M[Perda_Insumo] -->|OUTER APPLY<br/>Temporal| N[porcentagem_perda]
    
    G --> O[#tratos_por_dieta]
    H --> O
    K --> O
    L --> O
    N --> O
    
    style O fill:#e1f5fe
```

### Etapa 7-9: Consolidação e Rateio

```mermaid
graph TD
    A[#tratos_por_dieta] -->|SUM quantidade<br/>GROUP BY dimensões| B[#quantidades]
    
    C[Relatorio_baixa_estoque] -->|Filtro: data + localidade| D[#rel_baixa]
    
    B -->|LEFT JOIN| D
    D -->|Eliminar já baixados| E[WHERE rb.id IS NULL]
    
    E -->|DISTINCT| F[Subquery TAB]
    
    F -->|Window: COUNT lotes| G[Rateio:<br/>qtd / COUNT lote]
    
    G -->|Window: SUM total| H[#dados_consolidados<br/>+ qtd_total_ingrediente]
    
    style B fill:#e1f5fe
    style D fill:#e1f5fe
    style H fill:#e1f5fe
```

### Etapa 10-12: Finalização e Ajuste

```mermaid
graph TD
    A[#dados_consolidados] -->|LEFT JOIN| B[#dados_conta_estoque]
    B -->|CASE ativo| C{Tipo de Ativo}
    C -->|1| D[Ativo Imobilizado]
    C -->|0| E[Estoque]
    C -->|NULL| F[NULL]
    
    A --> G[#dadosFinal]
    D --> G
    E --> G
    F --> G
    
    G -->|JOIN| H[#qtdIngrediente]
    
    H -->|Fórmula Ajuste| I[qtd * REAL / PLANEJADO]
    
    I -->|Filtro: conta_estoque NOT NULL| J[#result]
    
    J -->|SUM quantidade<br/>GROUP BY dimensões| K[SELECT FINAL<br/>Resultado Agregado]
    
    style G fill:#e1f5fe
    style J fill:#e1f5fe
    style K fill:#c8e6c9
```

## Fórmulas Chave

### 1. Ajuste de Matéria Seca (MS)
```
SE flag_ms = 1 ENTÃO
    quantidade_ajustada = (quantidade * ms_ingrediente) / 100
SENÃO
    quantidade_ajustada = quantidade
FIM SE
```

### 2. Rateio por Lote
```
quantidade_rateada = quantidade / COUNT(lotes_com_mesma_quantidade)
```

### 3. Ajuste Proporcional Final
```
quantidade_final = quantidade_planejada * (quantidade_real / SUM(quantidade_planejada_total))
```

## Critérios de Mapeamento de Conta Estoque

```mermaid
graph TD
    A[Animal] --> B{Critério 1:<br/>Sexo}
    B -->|Match| C{Critério 2:<br/>Idade em Meses}
    C -->|Entre min/max| D{Critério 3:<br/>Grupo Genético}
    D -->|Match| E{Critério 4:<br/>Fazenda}
    E -->|Match| F{Critério 5:<br/>Subcategoria}
    F -->|Match| G[✓ Conta Estoque<br/>Encontrada]
    
    B -->|No Match| H[✗ Sem Conta]
    C -->|Fora Range| H
    D -->|No Match| H
    E -->|No Match| H
    F -->|No Match| H
    
    H --> I[conta_estoque:<br/>'Não Encontrada']
    
    style G fill:#c8e6c9
    style H fill:#ffcdd2
    style I fill:#ffcdd2
```

## Timeline de Processamento

```mermaid
gantt
    title Sequência de Execução das Tabelas Temporárias
    dateFormat X
    axisFormat %s
    
    section Base
    #animais           :a1, 0, 1
    #qtdIngrediente    :a2, 0, 1
    
    section Distribuição
    #dados_calc        :b1, after a1, 1
    #categoria_operacional :b2, after b1, 1
    
    section Mapeamento
    #dados_conta_estoque :c1, after b2, 1
    #tratos_por_dieta    :c2, after b1, 2
    
    section Consolidação
    #quantidades       :d1, after c2, 1
    #rel_baixa         :d2, after c2, 1
    #dados_consolidados :d3, after d1, 1
    
    section Finalização
    #dadosFinal        :e1, after d3, 1
    #result            :e2, after e1, 1
    SELECT FINAL       :e3, after e2, 1
```

## Hierarquia de Localidades (Nested Set Model)

```mermaid
graph TD
    A[Fazenda<br/>h1=1, h2=100] --> B[Setor A<br/>h1=2, h2=50]
    A --> C[Setor B<br/>h1=51, h2=99]
    
    B --> D[Curral 1<br/>h1=3, h2=25]
    B --> E[Curral 2<br/>h1=26, h2=49]
    
    C --> F[Curral 3<br/>h1=52, h2=75]
    C --> G[Curral 4<br/>h1=76, h2=98]
    
    H[Buscar Animal<br/>em Curral 1] -->|WHERE| I[h1 >= 3<br/>AND h2 <= 25]
    
    I -->|Retorna| D
    I -->|Ancestrais| B
    I -->|Ancestrais| A
    
    style A fill:#e1f5fe
    style B fill:#c8e6c9
    style D fill:#fff9c4
```

## Estados da Transação

```mermaid
stateDiagram-v2
    [*] --> BEGIN_TRAN
    BEGIN_TRAN --> DROP_TEMP_TABLES
    DROP_TEMP_TABLES --> CREATE_ANIMAIS
    CREATE_ANIMAIS --> CREATE_QTDINGREDIENTE
    CREATE_QTDINGREDIENTE --> CREATE_DADOS_CALC
    CREATE_DADOS_CALC --> CREATE_CATEGORIA_OP
    CREATE_CATEGORIA_OP --> CREATE_CONTA_ESTOQUE
    CREATE_CONTA_ESTOQUE --> CREATE_TRATOS
    CREATE_TRATOS --> CREATE_QUANTIDADES
    CREATE_QUANTIDADES --> CREATE_REL_BAIXA
    CREATE_REL_BAIXA --> CREATE_CONSOLIDADOS
    CREATE_CONSOLIDADOS --> CREATE_DADOS_FINAL
    CREATE_DADOS_FINAL --> CREATE_RESULT
    CREATE_RESULT --> SELECT_FINAL
    SELECT_FINAL --> ROLLBACK
    ROLLBACK --> [*]
    
    note right of ROLLBACK
        ⚠️ Transação revertida
        Nenhuma alteração 
        é persistida
    end note
```

## Dependências entre Tabelas

```mermaid
graph LR
    A[#animais] -->|FK| B[#dados_calc]
    C[#qtdIngrediente] -->|FK| D[#result]
    
    B -->|FK| E[#categoria_operacional]
    B -->|FK| F[#dados_conta_estoque]
    B -->|FK| G[#tratos_por_dieta]
    
    E -->|FK| F
    
    G -->|FK| H[#quantidades]
    
    H -->|FK| I[#dados_consolidados]
    J[#rel_baixa] -.->|LEFT JOIN| I
    
    I -->|FK| K[#dadosFinal]
    F -->|FK| K
    
    K -->|FK| D
    
    D -->|FK| L[SELECT FINAL]
    
    style A fill:#e1f5fe
    style C fill:#e1f5fe
    style L fill:#c8e6c9
```

## Legenda

```mermaid
graph LR
    A[Tabela Base] -->|INNER JOIN| B[Obrigatório]
    C[Tabela Base] -.->|LEFT JOIN| D[Opcional]
    E[Tabela Base] -->|Window Function| F[Agregação]
    
    G[Início]
    H[Processamento]
    I[Resultado Final]
    J[Atenção]
    
    style A fill:#e1f5fe
    style H fill:#fff9c4
    style I fill:#c8e6c9
    style J fill:#ffcdd2
```
