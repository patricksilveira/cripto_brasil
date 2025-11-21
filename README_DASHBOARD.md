# Dashboard Criptobrasil

Um dashboard interativo para visualizar dados mensais de operações com criptoativos no Brasil.

## 📋 Características

- **Visão Geral**: Métricas principais e evolução temporal
- **Operações**: Análise detalhada de operações por tipo (PF/PJ, Exterior, Exchanges)
- **Usuários**: Acompanhamento de CPFs e CNPJs únicos
- **Gênero**: Distribuição por gênero das operações e valores
- **Criptoativos**: Análise dos principais criptoativos, volume de operações e valor médio

## 🚀 Como Usar

### Instalação

1. Navegue até a pasta do projeto:
```bash
cd /Users/patricksilveira/Code/cripto_brasil
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

### Executar o Dashboard

```bash
streamlit run dashboard.py
```

O dashboard abrirá no navegador em `http://localhost:8501`

## 📊 Atualizando os Dados

A cada mês quando você tiver novos dados:

1. **Atualize os arquivos CSV** em `saida_csv/`:
   - `relatorio1_operacoes_por_tipo.csv`
   - `relatorio2_cpfs_cnpjs_unicos.csv`
   - `relatorio3_genero_operacoes.csv`
   - `relatorio4_criptoativos_mensal.csv`

2. **Recarregue o dashboard** - Ele detectará automaticamente os novos dados

   Ou clique em `R` no Streamlit para recarregar, ou pressione `Ctrl+R` no navegador.

## 📁 Estrutura dos Arquivos

```
cripto_brasil/
├── dashboard.py                           # Aplicação principal
├── requirements.txt                       # Dependências Python
├── data_clean.py                         # Script para limpar dados
└── saida_csv/
    ├── relatorio1_operacoes_por_tipo.csv
    ├── relatorio2_cpfs_cnpjs_unicos.csv
    ├── relatorio3_genero_operacoes.csv
    └── relatorio4_criptoativos_mensal.csv
```

## 🎨 Interface

### Barra Lateral
- **Filtro de Período**: Selecione o intervalo de datas para visualização
- Todos os gráficos atualizam dinamicamente

### Abas Principais

1. **📈 Visão Geral**
   - Métricas de alto nível
   - Evolução do valor total
   - Crescimento de usuários

2. **💰 Operações**
   - Composição de operações (PF/PJ, Exterior, Exchanges)
   - Evolução temporal
   - Tabela detalhada

3. **👥 Usuários**
   - Gráficos de CPFs e CNPJs únicos
   - Razão CNPJ/CPF
   - Dados históricos

4. **⚖️ Gênero**
   - Percentual de operações por gênero
   - Distribuição de valores
   - Tendências ao longo do tempo

5. **🪙 Criptoativos**
   - Top N criptoativos (customizável)
   - Análise por valor total
   - Número de operações
   - Valor médio por operação

## 💡 Dicas

- Use os filtros de data para focar em períodos específicos
- Passe o mouse sobre os gráficos para ver valores detalhados
- Clique nas legendas para mostrar/ocultar séries
- O slider no tab de criptoativos permite customizar quantos tokens visualizar

## 📝 Notas

- O cache de dados é mantido pela sessão. Para limpar, clique em "Clear Cache" no menu do Streamlit
- Os dados são carregados diretamente dos CSVs, sem necessidade de banco de dados
- A aplicação é responsiva e funciona bem em diferentes tamanhos de tela

## 🔧 Troubleshooting

Se o dashboard não carrega:
1. Verifique se todos os 4 arquivos CSV estão presentes em `saida_csv/`
2. Confirme que o formato dos CSVs está correto
3. Tente limpar o cache: `streamlit cache clear`
4. Verifique se não há erros na coluna de data

## 📞 Suporte

Para problemas ou sugestões, verifique:
- Os logs do terminal onde você rodou o Streamlit
- A aba "Ferramentas de Desenvolvedor" do navegador (F12)

---

**Dashboard criado para acompanhamento mensal dos dados de criptoativos no Brasil** 📊🪙
