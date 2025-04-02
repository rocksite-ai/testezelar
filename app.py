import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuração do Google Sheets
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_file("service_account.json", scopes=SCOPE)
CLIENT = gspread.authorize(CREDS)
SHEET = CLIENT.open_by_key("11C6rq54LPcSZuTQ0t-JH0zSRByVVvXX85tgFY9tl0qA").sheet1

def adicionar_usuario(nome, senha):
    usuarios = SHEET.get_all_records()
    if any(user['nome'] == nome for user in usuarios):
        return False
    SHEET.append_row([nome, senha, "colaborador"])
    return True

def verificar_usuario(nome, senha):
    usuarios = SHEET.get_all_records()
    for user in usuarios:
        if user['nome'] == nome and user['senha'] == senha:
            return user['tipo']
    return None

def adicionar_transacao(usuario, tipo, valor, descricao, perfil, data):
    SHEET.append_row([usuario, tipo, valor, descricao, perfil, data])

def obter_transacoes_usuario(usuario):
    transacoes = SHEET.get_all_records()
    return [t for t in transacoes if t['usuario'] == usuario]

def obter_saldo(usuario):
    transacoes = obter_transacoes_usuario(usuario)
    saldo = sum(t['valor'] if t['tipo'] == 'entrada' else -t['valor'] for t in transacoes)
    return saldo

st.title("Gestão Financeira - Programa Zelar")

menu = ["Login", "Registrar", "Supervisor"]
escolha = st.sidebar.selectbox("Menu", menu)

if escolha == "Registrar":
    st.subheader("Criar Conta")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")
    if st.button("Registrar"):
        if adicionar_usuario(nome, senha):
            st.success("Conta criada com sucesso!")
        else:
            st.error("Usuário já existe!")

elif escolha == "Login":
    st.subheader("Login")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        tipo_usuario = verificar_usuario(nome, senha)
        if tipo_usuario:
            st.session_state["usuario"] = nome
            st.session_state["tipo"] = tipo_usuario
        else:
            st.error("Usuário ou senha incorretos")
    
    if "usuario" in st.session_state:
        st.success(f"Bem-vindo, {st.session_state['usuario']}!")
        perfil = st.selectbox("Perfil da Transação", ["Café da Manhã", "Almoço", "Janta", "Outros Serviços", "Caixa"])
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")
        data = st.date_input("Data da transação", value=datetime.today())
        hora = st.time_input("Hora da transação", value=datetime.now().time())
        data_hora = datetime.combine(data, hora).strftime('%Y-%m-%d %H:%M:%S')
        tipo_transacao = "entrada" if perfil == "Caixa" else "saida"
        
        if st.button("Adicionar Transação"):
            adicionar_transacao(st.session_state["usuario"], tipo_transacao, valor, descricao, perfil, data_hora)
            st.success("Transação adicionada!")
        
        st.subheader("Minhas Transações")
        transacoes = obter_transacoes_usuario(st.session_state["usuario"])
        for t in transacoes:
            st.write(f"{t['data']} - {t['tipo'].capitalize()}: R$ {t['valor']:.2f} - {t['descricao']} - Perfil: {t['perfil']}")
        
        st.subheader("Saldo Atual")
        st.write(f"R$ {obter_saldo(st.session_state['usuario']):.2f}")

elif escolha == "Supervisor":
    st.subheader("Painel do Supervisor")
    usuarios = set(t['usuario'] for t in SHEET.get_all_records())
    for usuario in usuarios:
        st.write(f"{usuario}: R$ {obter_saldo(usuario):.2f}")
