# database.py

import sqlite3
from config import DB_PATH, TEST_DB_PATH, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, DEFAULT_ROLE, logging
import bcrypt

def get_database_connection(test=False):
    """
    Retorna uma conexão e cursor para o banco de dados.
    Se `test` for True, retorna a conexão para o banco de dados de teste.
    """
    db_path = TEST_DB_PATH if test else DB_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    initialize_database(conn, cursor)
    return conn, cursor

def initialize_database(conn, cursor):
    """
    Cria as tabelas necessárias se não existirem e adiciona um usuário admin padrão.
    """
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transportadora TEXT NOT NULL,
                codigo_pacote TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL,
                hora TEXT NOT NULL,
                status TEXT NOT NULL,
                coleta_number INTEGER NOT NULL
            )
        ''')

        # Verifica se há usuários no banco
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        if user_count == 0:
            # Adiciona o usuário admin padrão
            hashed_password = bcrypt.hashpw(DEFAULT_ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           (DEFAULT_ADMIN_USERNAME, hashed_password.decode('utf-8'), DEFAULT_ROLE))
            conn.commit()
            logging.info("Usuário admin padrão criado.")
    except Exception as e:
        logging.error(f"Erro ao inicializar o banco de dados: {e}")
        raise
