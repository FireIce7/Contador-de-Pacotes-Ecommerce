# config.py

import os
import sys
import re
import logging

# Determinar o caminho base da aplicação
if getattr(sys, 'frozen', False):
    # Executando como um executável PyInstaller
    BASE_DIR = os.path.dirname(sys.executable)
    # Caminho para recursos incluídos no executável
    RESOURCE_PATH = sys._MEIPASS
else:
    # Executando como script Python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_PATH = BASE_DIR

# Definir as pastas de dados e logs no diretório base
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_DIR = os.path.join(DATA_DIR, 'db')
LOG_DIR = os.path.join(DATA_DIR, 'logs')

# Criar as pastas se não existirem
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Caminhos para os bancos de dados
DB_PATH = os.path.join(DB_DIR, 'packages.db')
TEST_DB_PATH = os.path.join(DB_DIR, 'packagestest.db')  # Banco de dados para testes

# Caminho para o arquivo de áudio personalizado
ALERT_SOUND_PATH = os.path.join(RESOURCE_PATH, 'sounds', 'alert.wav')

# Caminho para o arquivo de log
LOG_PATH = os.path.join(LOG_DIR, 'app.log')

# Configuração de logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.DEBUG,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# Constantes para configuração
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ROLE = "admin"
TRANSPORTADORA_PADRAO = "Selecione a Transportadora"
STATUS_PENDING = "pending"
STATUS_COLLECTED = "collected"

# Expressão regular para validação de códigos de pacote
PACKAGE_CODE_REGEX = re.compile(r'^(GC|AJ)\d{16}$|^BR\w{13}$|^44\d{9}$|\d{15,}$')
