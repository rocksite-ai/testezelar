import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

# Configuração do Google Sheets
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Verificar se o arquivo de credenciais existe
if not os.path.exists("credenciais.json"):
    st.error("Arquivo de credenciais não encontrado. Verifique se o arquivo 'credenciais.json' está na pasta do projeto.")
    st.stop()

try:
    CREDS = Credentials.from_service_account_file("credenciais.json", scopes=SCOPE)
    CLIENT = gspread.authorize(CREDS)
    
    # Tentar abrir a planilha para verificar a conexão
    SHEET_ID = "11C6rq54LPcSZuTQ0t-JH0zSRByVVvXX85tgFY9tl0qA"
    try:
        SHEET = CLIENT.open_by_key(SHEET_ID).sheet1
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Planilha com ID {SHEET_ID} não encontrada. Verifique o ID da planilha.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound:
        st.error("Planilha encontrada, mas a primeira aba (sheet1) não existe.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao acessar a planilha: {str(e)}")
        st.error("Verifique se a conta de serviço tem permissão para acessar esta planilha.")
        st.stop()
        
except Exception as e:
    st.error(f"Erro na autenticação com o Google Sheets: {str(e)}")
    st.stop()

# Função para verificar se as colunas necessárias existem na planilha
def verificar_colunas():
    try:
        headers = SHEET.row_values(1)
        colunas_necessarias = ["nome", "senha", "tipo", "usuario", "valor", "descricao", "perfil", "data"]
        colunas_faltantes = [col for col in colunas_necessarias if col not in headers]
        
        if colunas_faltantes:
            if len(headers) == 0:
                # Planilha vazia, adicionar cabeçalhos
                SHEET.append_row(["nome", "senha", "tipo", "usuario", "valor", "descricao", "perfil", "data"])
                return True
            else:
                st.error(f"Colunas necessárias faltando na planilha: {', '.join(colunas_faltantes)}")
                return False
        return True
    except Exception as e:
        st.error(f"Erro ao verificar colunas da planilha: {str(e)}")
        return False

# Verifique a estrutura da planilha antes de continuar
if not verificar_colunas():
    st.stop()

def adicionar_usuario(nome, senha):
    try:
        usuarios = SHEET.get_all_records()
        if any(user.get('nome') == nome for user in usuarios):
            return False
        SHEET.append_row([nome, senha, "colaborador", "", "", "", "", ""])
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar usuário: {str(e)}")
        return False

def verificar_usuario(nome, senha):
    try:
        usuarios = SHEET.get_all_records()
        for user in usuarios:
            if user.get('nome') == nome and user.get('senha') == senha:
                return user.get('tipo', 'colaborador')
        return None
    except Exception as e:
        st.error(f"Erro ao verificar usuário: {str(e)}")
        return None

def adicionar_transacao(usuario, tipo, valor, descricao, perfil, data):
    try:
        # Adicionar em nova linha
        SHEET.append_row(["", "", "", usuario, valor, descricao, perfil, data])
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar transação: {str(e)}")
        return False

def obter_transacoes_usuario(usuario):
    try:
        transacoes = SHEET.get_all_records()
        return [t for t in transacoes if t.get('usuario') == usuario]
    except Exception as e:
        st.error(f"Erro ao obter transações: {str(e)}")
        return []

def obter_saldo(usuario):
    try:
        transacoes = obter_transacoes_usuario(usuario)
        saldo = sum(float(t.get('valor', 0)) if t.get('tipo') == 'entrada' else -float(t.get('valor', 0)) for t in transacoes)
        return saldo
    except Exception as e:
        st.error(f"Erro ao calcular saldo: {str(e)}")
        return 0.0

st.title("Gestão Financeira - Programa Zelar")

menu = ["Login", "Registrar", "Supervisor"]
escolha = st.sidebar.selectbox("Menu", menu)

if escolha == "Registrar":
    st.subheader("Criar Conta")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")
    if st.button("Registrar"):
        if nome and senha:
            if adicionar_usuario(nome, senha):
                st.success("Conta criada com sucesso!")
            else:
                st.error("Usuário já existe ou ocorreu um erro ao registrar!")
        else:
            st.warning("Por favor, preencha todos os campos!")

elif escolha == "Login":
    st.subheader("Login")
    nome = st.text_input("Nome")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if nome and senha:
            tipo_usuario = verificar_usuario(nome, senha)
            if tipo_usuario:
                st.session_state["usuario"] = nome
                st.session_state["tipo"] = tipo_usuario
                st.success(f"Bem-vindo, {st.session_state['usuario']}!")
            else:
                st.error("Usuário ou senha incorretos")
        else:
            st.warning("Por favor, preencha todos os campos!")
    
    if "usuario" in st.session_state:
        perfil = st.selectbox("Perfil da Transação", ["Café da Manhã", "Almoço", "Janta", "Outros Serviços", "Caixa"])
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        descricao = st.text_input("Descrição")
        data = st.date_input("Data da transação", value=datetime.today())
        hora = st.time_input("Hora da transação", value=datetime.now().time())
        data_hora = datetime.combine(data, hora).strftime('%Y-%m-%d %H:%M:%S')
        tipo_transacao = "entrada" if perfil == "Caixa" else "saida"
        
        if st.button("Adicionar Transação"):
            if valor > 0 and descricao:
                if adicionar_transacao(st.session_state["usuario"], tipo_transacao, valor, descricao, perfil, data_hora):
                    st.success("Transação adicionada com sucesso!")
                else:
                    st.error("Erro ao adicionar transação. Tente novamente.")
            else:
                st.warning("Por favor, preencha todos os campos corretamente!")
        
        try:
            st.subheader("Minhas Transações")
            transacoes = obter_transacoes_usuario(st.session_state["usuario"])
            if transacoes:
                for t in transacoes:
                    tipo_display = t.get('tipo', '-').capitalize()
                    valor_display = float(t.get('valor', 0))
                    descricao_display = t.get('descricao', '-')
                    perfil_display = t.get('perfil', '-')
                    data_display = t.get('data', '-')
                    st.write(f"{data_display} - {tipo_display}: R$ {valor_display:.2f} - {descricao_display} - Perfil: {perfil_display}")
            else:
                st.info("Você ainda não possui transações registradas.")
            
            st.subheader("Saldo Atual")
            st.write(f"R$ {obter_saldo(st.session_state['usuario']):.2f}")
        except Exception as e:
            st.error(f"Erro ao exibir informações: {str(e)}")

elif escolha == "Supervisor":
    st.subheader("Painel do Supervisor")
    try:
        todos_registros = SHEET.get_all_records()
        usuarios = set(t.get('usuario') for t in todos_registros if t.get('usuario'))
        if usuarios:
            for usuario in usuarios:
                st.write(f"{usuario}: R$ {obter_saldo(usuario):.2f}")
        else:
            st.info("Não há usuários com transações registradas.")
    except Exception as e:
        st.error(f"Erro ao carregar painel do supervisor: {str(e)}")
