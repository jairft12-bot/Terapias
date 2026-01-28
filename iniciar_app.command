#!/bin/bash
cd "$(dirname "$0")"
echo "Iniciando Visor de Terapias..."
echo "------------------------------"

# Intentar encontrar streamlit y ejecutarlo
if command -v streamlit &> /dev/null; then
    streamlit run terapias.py
else
    # Fallback: intentar instalarlo o correrlo via python
    echo "Streamlit no detectado directamente. Intentando via Python..."
    python3 -m pip install -r requirements.txt
    python3 -m streamlit run terapias.py
fi

# Mantener ventana abierta si falla
read -p "Presiona Enter para cerrar..."
