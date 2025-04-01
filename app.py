import streamlit as st
import sqlite3
from datetime import datetime

# Configuração do banco de dados
def init_db():
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT UNIQUE,
                        senha TEXT,
                        tipo TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transacoes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario TEXT,
                        tipo TEXT,
                        valor REAL,
                        descricao TEXT,
                        data TEXT)''')
    conn.commit()
    conn.close()

# Função para adicionar transações
def adicionar_transacao(usuario, tipo, valor, descricao):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transacoes (usuario, tipo, valor, descricao, data) VALUES (?, ?, ?, ?, ?)",
                   (usuario, tipo, valor, descricao, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# Função para obter saldo
def obter_saldo(usuario):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END) FROM transacoes WHERE usuario=?", (usuario,))
    saldo = cursor.fetchone()[0] or 0.0
    conn.close()
    return saldo

# Interface Streamlit
st.title("Gestão Financeira - Programa Zelar")

menu = ["Login", "Registrar", "Supervisor"]
escolha = st.sidebar.selectbox("Menu", menu)

if escolha == "Registrar":
    st.subheader("Criar Conta")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")
    if st.button("Registrar"):
        conn = sqlite3.connect("financeiro.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nome, senha, tipo) VALUES (?, ?, 'colaborador')", (nome, senha))
            conn.commit()
            st.success("Conta criada com sucesso!")
        except:
            st.error("Usuário já existe!")
        conn.close()

elif escolha == "Login":
    st.subheader("Login")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = sqlite3.connect("financeiro.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE nome=? AND senha=?", (nome, senha))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            st.session_state["usuario"] = nome
            st.session_state["tipo"] = user[3]
        else:
            st.error("Usuário ou senha incorretos")
    
    if "usuario" in st.session_state:
        st.success(f"Bem-vindo, {st.session_state['usuario']}!")
        
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")
        if st.button("Adicionar Receita"):
            adicionar_transacao(st.session_state["usuario"], "entrada", valor, descricao)
            st.success("Receita adicionada!")
        if st.button("Adicionar Despesa"):
            adicionar_transacao(st.session_state["usuario"], "saida", valor, descricao)
            st.success("Despesa adicionada!")
        
        st.subheader("Saldo Atual")
        st.write(f"R$ {obter_saldo(st.session_state['usuario']):.2f}")
        
elif escolha == "Supervisor":
    st.subheader("Painel do Supervisor")
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT usuario, SUM(CASE WHEN tipo='entrada' THEN valor ELSE -valor END) as saldo FROM transacoes GROUP BY usuario")
    dados = cursor.fetchall()
    conn.close()
    
    for usuario, saldo in dados:
        st.write(f"{usuario}: R$ {saldo:.2f}")

# Inicializar banco de dados
init_db()
