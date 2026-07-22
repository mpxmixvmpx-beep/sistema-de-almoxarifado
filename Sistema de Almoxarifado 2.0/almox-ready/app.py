from flask import Flask, render_template, request
import mysql.connector

def obter_conexao():
    return mysql.connector.connect(  
        host='localhost',
        port='3306',
        username='root',
        database='roger_partidaco',
        password='Bcm-0157'
    )

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("Login_page.html")

@app.route("/estoque")
def estoque():
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM objetos_do_roger")
    resultado = cursor.fetchall()

    return render_template('estoque.html', resultado=resultado)
    

@app.route("/cadastro")
def cadastro():
    return render_template('cadastro.html')

@app.route("/home")
def home():
    return render_template("Home.html")

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
    return render_template("cadastro_concluido.html")

@app.route("/adm")
def adm():
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM usuarios")
    resultado = cursor.fetchall()

    return render_template('adm_page.html', resultado=resultado)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)