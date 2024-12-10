# database.py

import sqlite3
import bcrypt
import sys
from tkinter import messagebox
from config import DB_PATH, TEST_DB_PATH, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, DEFAULT_ROLE
import logging

def initialize_database(conn, cursor):
    """
    Inicializa o banco de dados criando as tabelas necessárias e adicionando índices.
    """
    try:
        # Criar a tabela de pacotes, se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transportadora TEXT,
                codigo_pacote TEXT,
                data TEXT,
                hora TEXT,
                status TEXT,
                coleta_number INTEGER
            )
        ''')
        conn.commit()

        # Criar índices para otimizar consultas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transportadora ON packages (transportadora)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data ON packages (data)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_codigo_pacote ON packages (codigo_pacote)")
        conn.commit()

        # Criar a tabela de usuários, se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT
            )
        ''')
        conn.commit()

        # Criar índices para usuários
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_username ON users (username)")
        conn.commit()

        # Verificar se há usuários cadastrados; se não, criar um usuário administrador padrão
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            hashed_password = bcrypt.hashpw(DEFAULT_ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                           (DEFAULT_ADMIN_USERNAME, hashed_password.decode('utf-8'), DEFAULT_ROLE))
            conn.commit()
    except Exception as e:
        logging.error("Erro ao inicializar o banco de dados: %s", e)
        messagebox.showerror("Erro", "Erro ao inicializar o banco de dados. Verifique os logs para mais detalhes.")
        sys.exit(1)

def get_database_connection(test=False):
    """
    Retorna uma conexão e cursor para o banco de dados.
    """
    try:
        path = TEST_DB_PATH if test else DB_PATH
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        initialize_database(conn, cursor)
        return conn, cursor
    except Exception as e:
        logging.error("Erro ao conectar ao banco de dados: %s", e)
        messagebox.showerror("Erro", "Erro ao conectar ao banco de dados. Verifique os logs para mais detalhes.")
        sys.exit(1)
