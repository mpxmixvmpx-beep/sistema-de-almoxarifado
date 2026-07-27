from flask import Flask, render_template, request
import bcrypt
import mysql.connector

def obter_conexao():
    return mysql.connector.connect(  
        host='localhost',
        port='3306',
        user='root',
        database='roger_partidaco',
        password=''
    )

def validar_login(user, password):
    if not user or not password:
        return False

    conexao = obter_conexao()
    cursor = conexao.cursor()

    query = "SELECT nome, senha FROM usuarios WHERE nome = %s"
    cursor.execute(query, (user,))
    resultado = cursor.fetchone()  # Traz apenas o usuário encontrado ou None

    cursor.close()
    conexao.close()

    # Se não encontrou o usuário
    if not resultado:
        return False

    senha_banco = resultado[1]

    # Prepara as senhas para verificação em bytes
    bytes_senha = password.encode('utf-8')
    if isinstance(senha_banco, str):
        senha_banco = senha_banco.encode('utf-8')

    # Valida o hash com bcrypt
    try:
        if bcrypt.checkpw(bytes_senha, senha_banco):
            return True
    except Exception:
        # Fallback caso a senha no banco esteja em texto puro
        if resultado[1] == password:
            return True

    return False

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("Login_page.html")

@app.route("/login_incorreto")
def login_incorreto():
    return render_template("login_incorreto.html")

@app.route("/home")
def home():
    return render_template("Home.html")

@app.route("/estoque", methods=['POST', 'GET'])
def estoque():
    user = request.form.get('user')
    password = request.form.get('password')

    # Valida login se for enviado formulário via POST
    if request.method == 'POST':
        login_validado = validar_login(user, password)
        if not login_validado:
            return render_template('login_incorreto.html')

    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM objetos_do_roger")
    resultado = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('estoque.html', resultado=resultado)

@app.route("/movimentacao")
def movimentacao():
    return render_template("movimentacao.html")

@app.route("/movimentacao_concluida", methods=['POST'])
def movimentacao_concluida():
    nome = request.form.get('nome')
    qtd = request.form.get('qtd')
    selecao = request.form.get('selecao')

    conexao = obter_conexao()
    cursor = conexao.cursor(buffered=True)

    # Removidas as aspas simples de '%s'
    query = "SELECT qtd FROM objetos_do_roger WHERE nome = %s"
    cursor.execute(query, (nome,))

    qtd_banco = cursor.fetchone() 
    if qtd_banco:
        qtd_banco = int(qtd_banco[0])
        qtd = int(qtd)

        if selecao == '1':   # AUMENTAR A QUANTIDADE
            nova_qtd = qtd_banco + qtd
        elif selecao == '2': # DIMINUIR A QUANTIDADE
            nova_qtd = qtd_banco - qtd
        else:
            nova_qtd = qtd_banco

        query_update = "UPDATE objetos_do_roger SET qtd = %s WHERE nome = %s;"
        cursor.execute(query_update, (nova_qtd, nome))
        conexao.commit()

    cursor.close()
    conexao.close()

    return render_template("movimentacao_concluida.html")

@app.route("/cadastro")
def cadastro():
    return render_template('cadastro.html')

@app.route("/cadastro_concluido", methods=['GET', 'POST'])
def cadastro_concluido():
    nome = request.form.get('nome')
    descricao = request.form.get('descricao')
    qtd = request.form.get('qtd')
    preco = request.form.get('preco')
    imagem = request.form.get('imagem')

    conexao = obter_conexao()
    cursor = conexao.cursor()
    
    query = "INSERT INTO objetos_do_roger (nome, descricao, qtd, preco, imagem) VALUES (%s, %s, %s, %s, %s);"
    cursor.execute(query, (nome, descricao, qtd, preco, imagem))
    conexao.commit()

    cursor.close()
    conexao.close()

    return render_template("cadastro_concluido.html")

@app.route("/adm")
def adm():
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM usuarios")
    resultado = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('adm_page.html', resultado=resultado)

@app.route("/adicionar_user_concluido", methods=['POST'])
def adicionar_user_concluido():
    nome = request.form.get('nome')
    senha = request.form.get('senha')
    tipo = request.form.get('selecao')

    bytes_senha = senha.encode('utf-8')
    hash_senha = bcrypt.hashpw(bytes_senha, bcrypt.gensalt()).decode('utf-8')

    conexao = obter_conexao()
    cursor = conexao.cursor()

    query = "INSERT INTO usuarios (nome, senha, tipo) VALUES (%s, %s, %s);"
    cursor.execute(query, (nome, hash_senha, tipo))
    conexao.commit()

    cursor.close()
    conexao.close()
    
    return render_template('adicionar_user_concluido.html')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)