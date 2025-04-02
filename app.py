import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# Configurar acesso ao Google Sheets
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = "credenciais.json"
SPREADSHEET_ID = "11C6rq54LPcSZuTQ0t-JH0zSRByVVvXX85tgFY9tl0qA"

# Autenticação com Google Sheets
def get_worksheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

# Função para adicionar transação
def adicionar_transacao(usuario, tipo, valor, descricao, perfil, data):
    sheet = get_worksheet()
    sheet.append_row([usuario, tipo, valor, descricao, perfil, data])

# Função para obter transações de um usuário
def obter_transacoes_usuario(usuario):
    sheet = get_worksheet()
    registros = sheet.get_all_records()
    df = pd.DataFrame(registros)
    return df[df['usuario'] == usuario] if not df.empty else pd.DataFrame()

# Função para obter saldo de um usuário
def obter_saldo(usuario):
    transacoes = obter_transacoes_usuario(usuario)
    if transacoes.empty:
        return 0.0
    return transacoes.apply(lambda x: x['valor'] if x['tipo'] == 'entrada' else -x['valor'], axis=1).sum()

# Interface Streamlit
st.title("Gestão Financeira - Programa Zelar")
menu = ["Login", "Registrar", "Supervisor"]
escolha = st.sidebar.selectbox("Menu", menu)

if escolha == "Login":
    st.subheader("Login")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        st.session_state["usuario"] = nome
        st.success(f"Bem-vindo, {nome}!")

    if "usuario" in st.session_state:
        perfil = st.selectbox("Perfil da Transação", ["Café da Manhã", "Almoço", "Janta", "Outros Serviços","Devolução de Caixa", "Caixa"])
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
        if not transacoes.empty:
            st.dataframe(transacoes[['data', 'tipo', 'valor', 'descricao', 'perfil']])
        else:
            st.write("Nenhuma transação registrada.")

        st.subheader("Saldo Atual")
        st.write(f"R$ {obter_saldo(st.session_state['usuario']):.2f}")

elif escolha == "Supervisor":
    st.subheader("Painel do Supervisor")
    sheet = get_worksheet()
    registros = sheet.get_all_records()
    df = pd.DataFrame(registros)

    if not df.empty:
        st.dataframe(df)
    else:
        st.write("Nenhuma transação encontrada.")
