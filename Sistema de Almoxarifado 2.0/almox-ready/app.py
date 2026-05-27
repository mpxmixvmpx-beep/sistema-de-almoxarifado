from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("Login_page.html")

@app.route("/estoque")
def estoque():
    return render_template("estoque.html")

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


   
