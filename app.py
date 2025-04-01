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
def adicionar_transacao(usuario, tipo, valor, descricao, data):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transacoes (usuario, tipo, valor, descricao, data) VALUES (?, ?, ?, ?, ?)",
                   (usuario, tipo, valor, descricao, data))
    conn.commit()
    conn.close()

# Função para atualizar transação
def atualizar_transacao(transacao_id, novo_valor, nova_descricao, nova_data):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE transacoes SET valor=?, descricao=?, data=? WHERE id=?", (novo_valor, nova_descricao, nova_data, transacao_id))
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

# Função para obter transações mensais
def obter_transacoes_mensais(usuario, mes, ano):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, data, tipo, valor, descricao FROM transacoes WHERE usuario=? AND strftime('%m', data)=? AND strftime('%Y', data)=?", (usuario, f"{mes:02d}", str(ano)))
    transacoes = cursor.fetchall()
    conn.close()
    return transacoes

# Função para obter transações do usuário
def obter_transacoes_usuario(usuario):
    conn = sqlite3.connect("financeiro.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, data, tipo, valor, descricao FROM transacoes WHERE usuario=? ORDER BY data DESC", (usuario,))
    transacoes = cursor.fetchall()
    conn.close()
    return transacoes

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
        
        perfil = st.selectbox("Perfil da Transação", ["Café da Manhã", "Almoço", "Janta", "Outros Serviços", "Caixa"])
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")
        data = st.date_input("Data da transação", value=datetime.today())
        
        # A hora agora vai ser preservada após a primeira seleção
        hora_default = datetime.now().time()
        hora = st.time_input("Hora da transação", value=hora_default)

        data_hora = datetime.combine(data, hora).strftime('%Y-%m-%d %H:%M:%S')
        
        tipo_transacao = "entrada" if perfil == "Caixa" else "saida"
        
        if st.button("Adicionar Transação"):
            adicionar_transacao(st.session_state["usuario"], tipo_transacao, valor, descricao, data_hora)
            st.success("Transação adicionada!")
        
        st.subheader("Minhas Transações")
        transacoes = obter_transacoes_usuario(st.session_state["usuario"])
        for t in transacoes:
            with st.expander(f"{t[1]} - {t[2].capitalize()}: R$ {t[3]:.2f} - {t[4]}"):
                novo_valor = st.number_input("Novo Valor", min_value=0.0, value=t[3], format="%.2f", key=f"valor_{t[0]}")
                nova_descricao = st.text_input("Nova Descrição", value=t[4], key=f"desc_{t[0]}")
                nova_data = st.text_input("Nova Data e Hora (AAAA-MM-DD HH:MM:SS)", value=t[1], key=f"data_{t[0]}")
                if st.button("Atualizar", key=f"update_{t[0]}"):
                    atualizar_transacao(t[0], novo_valor, nova_descricao, nova_data)
                    st.success("Transação atualizada!")
        
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
    
    st.subheader("Relatório Mensal")
    usuario_selecionado = st.selectbox("Selecionar Colaborador", [d[0] for d in dados])
    mes = st.selectbox("Mês", list(range(1, 13)))
    ano = st.selectbox("Ano", list(range(2023, datetime.today().year + 1)))
    
    if st.button("Gerar Relatório"):
        transacoes = obter_transacoes_mensais(usuario_selecionado, mes, ano)
        if transacoes:
            for t in transacoes:
                st.write(f"{t[1]} - {t[2].capitalize()}: R$ {t[3]:.2f} - {t[4]}")
        else:
            st.write("Nenhuma transação encontrada para o período.")

# Inicializar banco de dados
init_db()
