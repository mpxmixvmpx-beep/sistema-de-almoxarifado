from flask import Flask, jsonify, render_template, request, session, redirect, url_for, send_file  # MODIFICADO
import bcrypt
import mysql.connector
import csv
import io

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
    cursor.execute(
        "SELECT nome, senha, tipo FROM usuarios WHERE nome = %s",  # MODIFICADO
        (nome,)
    )
    resultado = cursor.fetchone()

    cursor.close()
    conexao.close()

    # fetchall() retorna lista vazia [] se não encontrar o usuário
    if not resultado:
        return None

    # Garante que a senha do banco esteja em formato bytes para o bcrypt
    senha_banco = resultado[1]
    if isinstance(senha_banco, str):
        senha_banco = senha_banco.encode('utf-8')

    if bcrypt.checkpw(senha.encode('utf-8'), senha_banco):
        return {'nome': resultado[0], 'tipo': resultado[2]}  # MODIFICADO
    return None


def item_para_json(item):
    item['preco'] = float(item['preco'])
    return item


# MODIFICADO: funcoes pequenas evitam repetir as mesmas verificacoes.
def usuario_logado():
    return 'usuario' in session


def usuario_admin():
    return session.get('tipo') == 'admin'


def buscar_estoque():
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute('SELECT * FROM objetos_do_roger')
    resultado = cursor.fetchall()
    cursor.close()
    conexao.close()
    return resultado

app = Flask(__name__)
app.secret_key = 'chave-do-sistema-de-almoxarifado'  # MODIFICADO: habilita a sessão de login

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
    # MODIFICADO: valida o login somente no envio do formulário.
    # Depois disso, o acesso por GET usa o usuário salvo na sessão.
    if request.method == 'POST':
        nome = request.form.get('nome')
        senha = request.form.get('senha')
        usuario = validar_login(nome, senha)  # MODIFICADO: guarda nome e tipo na sessão
        if not usuario:
            return render_template('login_incorreto.html')
        session['usuario'] = usuario['nome']  # MODIFICADO
        session['tipo'] = usuario['tipo']  # MODIFICADO
    elif not usuario_logado():  # MODIFICADO
        return render_template('Login_page.html')

    return render_template('estoque.html', resultado=buscar_estoque())  # MODIFICADO

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
    # MODIFICADO: somente administradores podem acessar a área ADM.
    if not usuario_admin():  # MODIFICADO
        return redirect(url_for('estoque'))

    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM usuarios")
    resultado = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('adm_page.html', resultado=resultado)

@app.route("/adicionar_user_concluido", methods=['POST'])
def adicionar_user_concluido():
    # MODIFICADO: protege também o envio direto do formulário.
    if not usuario_admin():  # MODIFICADO
        return redirect(url_for('estoque'))

    conexao = obter_conexao()
    cursor = conexao.cursor()

    nome = request.form.get('nome')
    senha = request.form.get('senha')
    tipo = request.form.get('selecao')

    hash_senha = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())  # MODIFICADO

    query = "INSERT INTO usuarios (nome, senha, tipo) VALUES (%s, %s, %s)"
    valores = (nome, hash_senha, tipo)

    cursor.execute(query, valores)
    conexao.commit()
    
    cursor.close()
    conexao.close()
    
    return render_template('adicionar_user_concluido.html')


# ========================= ESTOQUE: CSV E EXCLUSAO =========================
# MODIFICADO: exclui todos os itens somente para administrador.
@app.route('/estoque/excluir-todos', methods=['POST'])
def excluir_todos_itens():
    if not usuario_admin():
        return redirect(url_for('estoque'))

    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM objetos_do_roger')
    conexao.commit()
    cursor.close()
    conexao.close()
    return redirect(url_for('estoque'))


# MODIFICADO: exporta todos os itens em CSV, que abre no Excel.
@app.route('/estoque/exportar-csv')
def exportar_csv():
    # MODIFICADO: somente usuarios logados podem exportar o estoque.
    if not usuario_logado():
        return redirect(url_for('index'))

    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute('SELECT id, nome, descricao, qtd, preco, imagem FROM objetos_do_roger')
    itens = cursor.fetchall()
    cursor.close()
    conexao.close()

    arquivo = io.StringIO()
    escritor = csv.writer(arquivo, delimiter=';')
    escritor.writerow(['id', 'nome', 'descricao', 'qtd', 'preco', 'imagem'])
    escritor.writerows(itens)
    arquivo.seek(0)
    return send_file(
        io.BytesIO(arquivo.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='estoque.csv'
    )


# MODIFICADO: importa um CSV e adiciona os itens na tabela atual.
@app.route('/estoque/importar-csv', methods=['POST'])
def importar_csv():
    # MODIFICADO: somente usuarios logados podem importar arquivos.
    if not usuario_logado():
        return redirect(url_for('index'))

    arquivo = request.files.get('arquivo_csv')
    if arquivo is None or arquivo.filename == '':
        return redirect(url_for('estoque'))

    leitor = csv.DictReader(io.TextIOWrapper(arquivo.stream, encoding='utf-8-sig'), delimiter=';')
    conexao = obter_conexao()
    cursor = conexao.cursor()
    for linha in leitor:
        cursor.execute(
            'INSERT INTO objetos_do_roger (nome, descricao, qtd, preco, imagem) '
            'VALUES (%s, %s, %s, %s, %s)',
            (linha['nome'], linha['descricao'], int(linha['qtd']), float(linha['preco']), linha['imagem'])
        )
    conexao.commit()
    cursor.close()
    conexao.close()
    return redirect(url_for('estoque'))


# ========================= API REST =========================
# MODIFICADO: as rotas abaixo foram adicionadas para trabalhar com JSON.

@app.route('/api/itens', methods=['GET'])
def api_listar_itens():
    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute('SELECT id, nome, descricao, qtd, preco, imagem FROM objetos_do_roger')
    itens = [item_para_json(item) for item in cursor.fetchall()]
    cursor.close()
    conexao.close()
    return jsonify(itens)


@app.route('/api/itens/<int:item_id>', methods=['GET'])
def api_obter_item(item_id):
    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute(
        'SELECT id, nome, descricao, qtd, preco, imagem '
        'FROM objetos_do_roger WHERE id = %s',
        (item_id,)
    )
    item = cursor.fetchone()
    cursor.close()
    conexao.close()

    if item is None:
        return jsonify({'erro': 'Item não encontrado'}), 404
    return jsonify(item_para_json(item))


@app.route('/api/itens', methods=['POST'])
def api_criar_item():
    dados = request.get_json(silent=True) or {}
    campos_obrigatorios = ('nome', 'descricao', 'qtd', 'preco', 'imagem')
    if any(campo not in dados for campo in campos_obrigatorios):
        return jsonify({'erro': 'Envie nome, descricao, qtd, preco e imagem'}), 400

    try:
        qtd = int(dados['qtd'])
        preco = float(dados['preco'])
    except (TypeError, ValueError):
        return jsonify({'erro': 'qtd deve ser inteiro e preco deve ser numero'}), 400

    if qtd < 0 or preco < 0:
        return jsonify({'erro': 'qtd e preco nao podem ser negativos'}), 400

    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute(
        'INSERT INTO objetos_do_roger (nome, descricao, qtd, preco, imagem) '
        'VALUES (%s, %s, %s, %s, %s)',
        (dados['nome'], dados['descricao'], qtd, preco, dados['imagem'])
    )
    conexao.commit()
    item_id = cursor.lastrowid
    cursor.close()
    conexao.close()
    return jsonify({'id': item_id, 'mensagem': 'Item criado'}), 201


@app.route('/api/movimentacoes', methods=['POST'])
def api_movimentar_item():
    dados = request.get_json(silent=True) or {}
    if not all(campo in dados for campo in ('item_id', 'tipo', 'quantidade')):
        return jsonify({'erro': 'Envie item_id, tipo (entrada ou saida) e quantidade'}), 400

    try:
        item_id = int(dados['item_id'])
        quantidade = int(dados['quantidade'])
    except (TypeError, ValueError):
        return jsonify({'erro': 'item_id e quantidade devem ser inteiros'}), 400

    if dados['tipo'] not in ('entrada', 'saida') or quantidade <= 0:
        return jsonify({'erro': 'tipo invalido ou quantidade nao positiva'}), 400

    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute(
        'SELECT qtd FROM objetos_do_roger WHERE id = %s FOR UPDATE',
        (item_id,)
    )
    item = cursor.fetchone()
    if item is None:
        cursor.close()
        conexao.close()
        return jsonify({'erro': 'Item não encontrado'}), 404

    nova_qtd = item['qtd'] + quantidade if dados['tipo'] == 'entrada' else item['qtd'] - quantidade
    if nova_qtd < 0:
        cursor.close()
        conexao.close()
        return jsonify({'erro': 'Estoque insuficiente'}), 409

    cursor.execute(
        'UPDATE objetos_do_roger SET qtd = %s WHERE id = %s',
        (nova_qtd, item_id)
    )
    conexao.commit()
    cursor.close()
    conexao.close()
    return jsonify({'item_id': item_id, 'quantidade_atual': nova_qtd})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)