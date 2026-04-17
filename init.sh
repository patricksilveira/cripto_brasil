#!/bin/bash
# Initialization Script for CriptoBrasil Dashboard

echo "🚀 Inicializando Projeto CriptoBrasil..."

# 1. Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
else
    echo "✅ Ambiente virtual 'venv' já existe."
fi

# 2. Activate Virtual Env
source venv/bin/activate

# 3. Install requirements
echo "🛠 Instalando dependências em requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create paths
mkdir -p saida_csv

# 5. Process Data
echo "🧹 Limpando dados do arquivo Excel e gerando arquivos CSV..."
python data_clean.py

echo "✅ Tarefas de inicialização concluídas com sucesso!"
echo "Para iniciar o dashboard, execute:"
echo "source venv/bin/activate"
echo "streamlit run dashboard.py"
