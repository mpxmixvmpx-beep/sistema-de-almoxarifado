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

    return render_template('estoque.html', resultado=resultado)
    

@app.route("/add_item")
def add_item():
    return render_template("add_item.html")

@app.route("/ret_item")
def ret_item():
    return render_template("ret_item.html")

@app.route("/home")
def home():
    return render_template("Home.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
