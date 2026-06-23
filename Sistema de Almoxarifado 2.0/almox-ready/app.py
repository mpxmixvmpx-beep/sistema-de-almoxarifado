from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("Login_page.html")

@app.route("/estoque")
def estoque():
    conexao= mysql.connector.connect(  
        host='localhost',
        port='3306',
        username='root',
        database='roger_partidaco',
        password=''
    )
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM objetos_do_roger")
    resultado = cursor.fetchall()

    return render_template('estoque.html', resultado=resultado)
    

@app.route("/add_item")
def add_item():
    nome = request.form.get('nome')
    nome = request.form.get('nome')
    nome = request.form.get('nome')
    nome = request.form.get('nome')

    banco= mysql.connector.connect(  
        host='localhost',
        port='3306',
        username='root',
        database='roger_partidaco',
        password=''
    )
    cursor = banco.cursor()
    query = "INSERT INTO objetos_do_roger"
    cursor.execute("SELECT * FROM objetos_do_roger")
    resultado = cursor.fetchall()git commit -m "ajustes na rota add_item"


    INSERT INTO objetos_do_roger (nome, qtd, preco, situacao, imagem)
    VALUES ('chave_de_fenda', 78, 'R$67,00', 'disponivel', 'nada');

    return render_template('add_item.html')

@app.route("/home")
def home():
    return render_template("Home.html")

@app.route("/adm")
def adm():
    conexao= mysql.connector.connect(  
        host='localhost',
        port='3306',
        username='root',
        database='roger_partidaco',
        password=''
    )
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM usuarios")
    resultado = cursor.fetchall()

    return render_template('adm_page.html', resultado=resultado)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
