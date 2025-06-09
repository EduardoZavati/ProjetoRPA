import requests
import sqlite3
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def apagar_banco():
    arquivo_db = "projeto_rpa.db"
    if os.path.exists(arquivo_db):
        os.remove(arquivo_db)
        print(f"Arquivo {arquivo_db} apagado para recriação do banco.")
    else:
        print(f"Arquivo {arquivo_db} não existe. Criando novo banco.")

def coletar_dados():
    url = "https://rickandmortyapi.com/api/character"
    personagens = []

    while url:
        resposta = requests.get(url)
        if resposta.status_code != 200:
            print("Erro ao acessar a API.")
            break
        dados = resposta.json()
        personagens.extend(dados['results'])
        url = dados['info']['next']

    return personagens

def armazenar_em_sqlite(personagens):
    conn = sqlite3.connect("projeto_rpa.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE personagens (
            id INTEGER PRIMARY KEY,
            nome TEXT,
            status TEXT,
            especie TEXT,
            genero TEXT,
            origem TEXT
        )
    ''')

    for p in personagens:
        cursor.execute('''
            INSERT INTO personagens (id, nome, status, especie, genero, origem)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (p['id'], p['name'], p['status'], p['species'], p['gender'], p['origin']['name']))

    conn.commit()
    conn.close()

def processar_com_regex():
    conn = sqlite3.connect("projeto_rpa.db")
    cursor = conn.cursor()

    cursor.execute("SELECT nome FROM personagens")
    nomes = cursor.fetchall()

    nomes_compostos = [nome[0] for nome in nomes if re.search(r"\b\w+\s\w+\b", nome[0])]

    cursor.execute('''
        CREATE TABLE dados_processados (
            nome TEXT
        )
    ''')

    for nome in nomes_compostos:
        cursor.execute("INSERT INTO dados_processados (nome) VALUES (?)", (nome,))

    conn.commit()
    conn.close()

    return nomes_compostos

def enviar_email(resumo):
    remetente = input("Digite seu e-mail Gmail: ")
    senha = input("Digite sua senha (senha de app do Gmail): ")
    destinatario = input("Digite o e-mail do destinatário: ")

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = "Relatório - Rick and Morty API"

    corpo = f"""
Olá!

Aqui está o resumo do projeto Rick and Morty RPA:

✅ Total de personagens coletados: {resumo['total']}
🧠 Personagens com nome composto (regex): {resumo['compostos']}

Att,
Projeto RPA com Python
"""
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(msg)
            print("✅ E-mail enviado com sucesso!")
    except smtplib.SMTPAuthenticationError:
        print("❌ Erro de autenticação: verifique e-mail e senha (use senha de app do Gmail).")
    except Exception as e:
        print(f"❌ Erro no envio: {e}")

if __name__ == "__main__":
    apagar_banco()

    print("🔄 Coletando dados da API Rick and Morty...")
    personagens = coletar_dados()

    if personagens:
        print("💾 Armazenando personagens no banco de dados...")
        armazenar_em_sqlite(personagens)

        print("🔍 Processando nomes com regex...")
        nomes_compostos = processar_com_regex()

        resumo = {
            "total": len(personagens),
            "compostos": len(nomes_compostos)
        }

        print("📧 Enviando relatório por e-mail...")
        enviar_email(resumo)
    else:
        print("❌ Não foi possível coletar os dados da API.")
