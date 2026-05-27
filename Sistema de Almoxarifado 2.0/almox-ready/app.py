from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("Login_page.html")

@app.route("/estoque")
def estoque():
    con = mysql.connector.connect(host='localhost', user='root', database='roger_partidaco', password='')
 
    cursor = con.cursor()
    cursor.execute("select database();")
    linha = cursor.fetchone()
    print("Conectado ao banco de dados", linha)
    

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
 