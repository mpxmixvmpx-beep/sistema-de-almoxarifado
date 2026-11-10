from flask import Flask, render_template, request, session, redirect, url_for, send_file  # MODIFICADO
import bcrypt
import mysql.connector
import csv
import io
import math

def obter_conexao():
    return mysql.connector.connect(
        host='localhost',
        port=3306,
        user='root',
        database='roger_partidaco',
        password='Bcm-0157'
    )

def validar_login(nome, senha):
    if not nome or not senha:
        return False

    conexao = obter_conexao()
    cursor = conexao.cursor(buffered=True)
    cursor.execute(
        "SELECT nome, senha, tipo FROM usuarios WHERE nome = %s LIMIT 1",  # MODIFICADO
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

def renderizar_erro_formulario(template, mensagem):
    return render_template(template, mensagem_erro=mensagem), 400

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
    nome = (request.form.get('nome') or '').strip()
    qtd_texto = (request.form.get('qtd') or '').strip()
    selecao = request.form.get('selecao')

    if not nome or not qtd_texto or selecao not in ('1', '2'):
        return renderizar_erro_formulario(
            'movimentacao_nao_concluida.html',
            'Preencha o tipo, o nome do item e a quantidade.'
        )

    try:
        qtd = int(qtd_texto)
    except ValueError:
        return renderizar_erro_formulario(
            'movimentacao_nao_concluida.html',
            'Informe uma quantidade inteira válida.'
        )

    if qtd <= 0:
        return renderizar_erro_formulario(
            'movimentacao_nao_concluida.html',
            'A quantidade deve ser maior que zero.'
        )

    conexao = obter_conexao()
    cursor = conexao.cursor(buffered=True)

    query = "SELECT qtd FROM objetos_do_roger WHERE nome = %s"
    cursor.execute(query, (nome,))

    qtd_banco = cursor.fetchone()
    if not qtd_banco:
        cursor.close()
        conexao.close()
        return renderizar_erro_formulario(
            'movimentacao_nao_concluida.html',
            'O item informado não foi encontrado no estoque.'
        )

    qtd_atual = int(qtd_banco[0])
    nova_qtd = qtd_atual + qtd if selecao == '1' else qtd_atual - qtd
    if nova_qtd < 0:
        cursor.close()
        conexao.close()
        return renderizar_erro_formulario(
            'movimentacao_nao_concluida.html',
            'A saída solicitada é maior que a quantidade disponível.'
        )

    query_update = "UPDATE objetos_do_roger SET qtd = %s WHERE nome = %s;"
    cursor.execute(query_update, (nova_qtd, nome))
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
        nome = (request.form.get('nome') or '').strip()
        descricao = (request.form.get('descricao') or '').strip()
        qtd_texto = (request.form.get('qtd') or '').strip()
        preco_texto = (request.form.get('preco') or '').strip()
        imagem = (request.form.get('imagem') or '').strip()

        if not all((nome, descricao, qtd_texto, preco_texto, imagem)):
            return renderizar_erro_formulario(
                'cadastro_nao_concluido.html',
                'Preencha todos os campos para cadastrar o item.'
            )

        if len(nome) > 100 or len(descricao) > 50 or len(imagem) > 500:
            return renderizar_erro_formulario(
                'cadastro_nao_concluido.html',
                'Confira o tamanho do nome, da descrição e do link da imagem.'
            )

        try:
            qtd = int(qtd_texto)
            preco = float(preco_texto.replace(',', '.'))
        except ValueError:
            return renderizar_erro_formulario(
                'cadastro_nao_concluido.html',
                'Quantidade e preço precisam ser números válidos.'
            )

        if qtd < 0 or preco < 0 or not math.isfinite(preco):
            return renderizar_erro_formulario(
                'cadastro_nao_concluido.html',
                'Quantidade e preço não podem ser negativos.'
            )

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

    nome = (request.form.get('nome') or '').strip()
    senha = request.form.get('senha') or ''
    tipo = request.form.get('selecao')

    if not nome or not senha or tipo not in ('admin', 'user'):
        return renderizar_erro_formulario(
            'adicionar_usuario_nao_concluido.html',
            'Preencha nome, senha e selecione um tipo de permissão.'
        )

    if len(nome) > 100 or len(senha) > 72:
        return renderizar_erro_formulario(
            'adicionar_usuario_nao_concluido.html',
            'O nome deve ter até 100 caracteres e a senha até 72.'
        )

    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute('SELECT id FROM usuarios WHERE nome = %s LIMIT 1', (nome,))
    if cursor.fetchone():
        cursor.close()
        conexao.close()
        return renderizar_erro_formulario(
            'adicionar_usuario_nao_concluido.html',
            'Já existe um usuário com esse nome.'
        )

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)