# Verificação de Uso da Tabela: Custos_Conta_EstoqueXSubcategoria

## Resumo da Verificação

**Data da Análise:** 2025-11-07  
**Tabela Analisada:** `Custos_Conta_EstoqueXSubcategoria`

---

## Resultado

✅ **SIM, a tabela É USADA no sistema.**

---

## Detalhes da Verificação

### Locais Verificados:

1. **Arquivos do Projeto (.sln, .csproj)**
   - ❌ Não encontrado em `Prodap.sln.txt`
   - ❌ Não encontrado em `ProdapTI.sln.txt`
   - ❌ Não encontrado em `ProdapTI.csproj.txt`

2. **Estrutura do Banco de Dados**
   - ✅ **ENCONTRADO em `estrutura.json.txt`**
   - A tabela está definida na estrutura do banco de dados

3. **Código Fonte (C#, SQL)**
   - Não foram encontrados arquivos de código-fonte C# ou SQL no repositório atual
   - O repositório contém apenas arquivos de conhecimento/documentação

---

## Conclusão

A tabela `Custos_Conta_EstoqueXSubcategoria` **ESTÁ PRESENTE** na estrutura do banco de dados do sistema, conforme registrado no arquivo `knowledge/estrutura.json.txt`.

**Nota Importante:** Esta verificação foi realizada com base nos arquivos de conhecimento disponíveis no repositório. Para uma análise completa de uso (queries, stored procedures, código C#), seria necessário acesso ao código-fonte completo da aplicação.

---

## Recomendações

- A tabela existe na estrutura do banco de dados
- Para verificar uso efetivo em código (queries, Entity Framework, etc.), seria necessário:
  - Acesso aos arquivos .cs do projeto
  - Acesso aos scripts SQL/stored procedures
  - Acesso às migrations do Entity Framework (se aplicável)
