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

def validar_login(nome, senha):
    if not nome or not senha:
        return False

    conexao = obter_conexao()
    cursor = conexao.cursor()

    query = "SELECT nome, senha FROM usuarios WHERE nome = %s"
    nome_tuple = (nome,)

    cursor.execute(query, nome_tuple)
    resultado = cursor.fetchall()

    cursor.close()
    conexao.close()

    # fetchall() retorna lista vazia [] se não encontrar o usuário
    if not resultado:
        return False

    # Garante que a senha do banco esteja em formato bytes para o bcrypt
    senha_banco = resultado[0][1]
    if isinstance(senha_banco, str):
        senha_banco = senha_banco.encode('utf-8')

    # Corrigido de 'enconde' para 'encode'
    validacao = bcrypt.checkpw(senha.encode('utf-8'), senha_banco)

    if resultado[0][0] == nome and validacao:
        login_valido = True
    else:
        login_valido = False
    return login_valido

app = Flask(__name__)

@app.route("/login_incorreto")
def login_incorreto():
    return render_template("login_incorreto.html")

@app.route("/")
def index():
    return render_template("Login_page.html")

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

    query = "SELECT qtd FROM objetos_do_roger WHERE nome = %s"
    cursor.execute(query, (nome,))

    qtd_banco = cursor.fetchone() 
    
    if qtd_banco:
        qtd_banco = int(qtd_banco[0])
        qtd = int(qtd)

        if selecao == '1': # AUMENTAR A QUANTIDADE DE ITENS NO ESTOQUE
            qtd = qtd_banco + qtd
        elif selecao == '2': # DIMINUIR A QUANTIDADE DE ITENS NO ESTOQUE
            qtd = qtd_banco - qtd

        query_update = "UPDATE objetos_do_roger SET qtd = %s WHERE nome = %s;"
        cursor.execute(query_update, (qtd, nome))
        conexao.commit()

    cursor.close()
    conexao.close()

    return render_template("movimentacao_concluida.html")

@app.route("/estoque", methods=['POST', 'GET'])
def estoque():
    # Pega os dados tanto via POST (formulário) quanto via GET (URL)
    if request.method == 'POST':
        nome = request.form.get('nome')
        senha = request.form.get('senha')
    else:
        nome = request.args.get('nome')
        senha = request.args.get('senha')

    # Valida o login (se não preencheu 'nome' ou 'senha', a função retorna False)
    login_validado = validar_login(nome, senha)

    # Se a senha/usuario estiver errada OU se não colocou nada:
    if not login_validado:
        return render_template('login_incorreto.html')

    # Se o login deu certo, busca o estoque:
    conexao = obter_conexao()
    cursor = conexao.cursor()
    query = ("SELECT * FROM objetos_do_roger")
    cursor.execute(query)

    resultado = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template('estoque.html', resultado=resultado)

@app.route("/cadastro")
def cadastro():
    return render_template('cadastro.html')

@app.route("/home")
def home():
    return render_template("Home.html")

@app.route("/cadastro_concluido", methods=['GET', 'POST'])
def cadastro_concluido():
    if request.method == 'POST':
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
    
    return render_template("cadastro.html")

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
    conexao = obter_conexao()
    cursor = conexao.cursor()

    nome = request.form.get('nome')
    senha = request.form.get('senha')
    tipo = request.form.get('selecao')

    bytes_senha = senha.encode('utf-8')
    hash_senha = bcrypt.hashpw(bytes_senha, bcrypt.gensalt())

    query = "INSERT INTO usuarios (nome, senha, tipo) VALUES (%s, %s, %s)"
    valores = (nome, hash_senha, tipo)

    cursor.execute(query, valores)
    conexao.commit()
    
    cursor.close()
    conexao.close()
    
    return render_template('adicionar_user_concluido.html')

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)