#!/bin/bash
# Script para executar Django com o ambiente correto
export PYTHONPATH=/Users/brunoibiapina/Desktop/Desenvolvimento/lotesys/.venv/lib/python3.13/site-packages:$PYTHONPATH
exec /Users/brunoibiapina/Desktop/Desenvolvimento/lotesys/.venv/bin/python3.13 "$@"