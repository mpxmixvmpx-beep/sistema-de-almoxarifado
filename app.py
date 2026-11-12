from flask import Flask, render_template, request, session, redirect, url_for, send_file
import bcrypt, csv, io, math, mysql.connector
from datetime import timedelta

# Centraliza a conexão com o banco para não repetir a mesma configuração em cada rota.

def obter_conexao():
    return mysql.connector.connect(
        host='mysql',
        port='3306',
        user='root',
        database='roger_partidaco',
        password='root'
    )

# Valida login: busca o usuário pelo nome e confirma a senha com bcrypt.
def login_user(nome, senha):
    if not nome or not senha:
        return False

    conn = obter_conexao()
    cur = conn.cursor(buffered=True)
    cur.execute('SELECT nome, senha, tipo FROM usuarios WHERE nome = %s LIMIT 1', (nome,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return None

    hash_db = user[1].encode('utf-8') if isinstance(user[1], str) else user[1]
    if bcrypt.checkpw(senha.encode('utf-8'), hash_db):
        return {'nome': user[0], 'tipo': user[2]}
    return None

# Helpers simples da sessão: checam se o usuário está logado e se é administrador.
def logged():
    return 'usuario' in session


def admin():
    return session.get('tipo') == 'admin'

# Busca o estoque atual para renderizar na tela.
def stock():
    conn = obter_conexao()
    cur = conn.cursor()
    cur.execute('SELECT * FROM objetos_do_roger')
    data = cur.fetchall()
    cur.close(); conn.close()
    return data

# Busca o histórico de movimentações do estoque.
def historico_movimentacao():
    conn = obter_conexao(); cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS historico_movimentacao (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            qtd INT NOT NULL,
            data DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cur.execute('SELECT id, nome, tipo, qtd, data FROM historico_movimentacao ORDER BY id DESC')
    dados = []
    for linha in cur.fetchall():
        item = list(linha)
        if item[4]:
            item[4] = item[4] - timedelta(hours=3)
        dados.append(tuple(item))
    cur.close(); conn.close(); return dados

# Resposta padronizada para erro de formulário: renderiza a página correta e retorna 400.
def error_page(template, message):
    return render_template(template, mensagem_erro=message), 400


app = Flask(__name__)
app.secret_key = 'chave-do-sistema-de-almoxarifado'

# Rotas principais do sistema: páginas de login, estoque e cadastro.


@app.route('/login_incorreto')
def login_incorreto():
    return render_template('login_incorreto.html')


@app.route('/')
def index():
    return render_template('Login_page.html')


@app.route('/movimentacao')
def movimentacao():
    return render_template('movimentacao.html', historico=historico_movimentacao())

# Atualiza a quantidade do item: soma se for entrada, subtrai se for saída.
@app.route('/movimentacao_concluida', methods=['POST'])
def movimentacao_concluida():
    nome = (request.form.get('nome') or '').strip()
    qtd_texto = (request.form.get('qtd') or '').strip()
    tipo = request.form.get('selecao')

    if not nome or not qtd_texto or tipo not in ('1', '2'):
        return error_page('movimentacao_nao_concluida.html', 'Preencha o tipo, o nome do item e a quantidade.')

    try:
        qtd = int(qtd_texto)
    except ValueError:
        return error_page('movimentacao_nao_concluida.html', 'Informe uma quantidade inteira válida.')

    if qtd <= 0:
        return error_page('movimentacao_nao_concluida.html', 'A quantidade deve ser maior que zero.')

    conn = obter_conexao(); cur = conn.cursor(buffered=True)
    cur.execute('SELECT qtd FROM objetos_do_roger WHERE nome = %s', (nome,))
    item = cur.fetchone()
    if not item:
        cur.close(); conn.close()
        return error_page('movimentacao_nao_concluida.html', 'O item informado não foi encontrado no estoque.')

    nova_qtd = int(item[0]) + qtd if tipo == '1' else int(item[0]) - qtd
    if nova_qtd < 0:
        cur.close(); conn.close()
        return error_page('movimentacao_nao_concluida.html', 'A saída solicitada é maior que a quantidade disponível.')

    tipo_mov = 'Entrada' if tipo == '1' else 'Saída'
    cur.execute('INSERT INTO historico_movimentacao (nome, tipo, qtd) VALUES (%s, %s, %s)', (nome, tipo_mov, qtd))

    if tipo == '2' and nova_qtd == 0:
        cur.execute('DELETE FROM objetos_do_roger WHERE nome = %s', (nome,))
    else:
        cur.execute('UPDATE objetos_do_roger SET qtd = %s WHERE nome = %s', (nova_qtd, nome))
    conn.commit(); cur.close(); conn.close()

    return render_template('movimentacao_concluida.html')

# Ao fazer login, salva usuário e tipo na sessão; ao abrir a página, exige login ativo.
@app.route('/estoque', methods=['POST', 'GET'])
def estoque():
    if request.method == 'POST':
        usuario = login_user(request.form.get('nome'), request.form.get('senha'))
        if not usuario:
            return render_template('login_incorreto.html')
        session['usuario'] = usuario['nome']
        session['tipo'] = usuario['tipo']
    elif not logged():
        return render_template('Login_page.html')

    return render_template('estoque.html', resultado=stock())


@app.route('/cadastro')
def cadastro():
    return render_template('cadastro.html')


@app.route('/home')
def home():
    return render_template('Home.html')

# Cadastra item no estoque com validações simples de campos e valores numéricos.
@app.route('/cadastro_concluido', methods=['GET', 'POST'])
def cadastro_concluido():
    if request.method != 'POST':
        return render_template('cadastro.html')

    nome = (request.form.get('nome') or '').strip()
    descricao = (request.form.get('descricao') or '').strip()
    qtd_texto = (request.form.get('qtd') or '').strip()
    preco_texto = (request.form.get('preco') or '').strip()
    imagem = (request.form.get('imagem') or '').strip()

    if not all((nome, descricao, qtd_texto, preco_texto)):
        return error_page('cadastro_nao_concluido.html', 'Preencha nome, descrição, quantidade e preço.')

    if imagem and len(imagem) > 500:
        return error_page('cadastro_nao_concluido.html', 'O link da imagem deve ter até 500 caracteres.')

    if len(nome) > 100 or len(descricao) > 50:
        return error_page('cadastro_nao_concluido.html', 'Confira o tamanho do nome e da descrição.')

    if imagem:
        imagem = imagem.strip()

    try:
        qtd = int(qtd_texto)
        preco = float(preco_texto.replace(',', '.'))
    except ValueError:
        return error_page('cadastro_nao_concluido.html', 'Quantidade e preço precisam ser números válidos.')

    if qtd < 0 or preco < 0 or not math.isfinite(preco):
        return error_page('cadastro_nao_concluido.html', 'Quantidade e preço não podem ser negativos.')

    conn = obter_conexao(); cur = conn.cursor()
    cur.execute('INSERT INTO objetos_do_roger (nome, descricao, qtd, preco, imagem) VALUES (%s, %s, %s, %s, %s)', (nome, descricao, qtd, preco, imagem or ''))
    conn.commit(); cur.close(); conn.close()
    return render_template('cadastro_concluido.html')

# Área administrativa: só entra quem possui permissão de administrador.
@app.route('/adm')
def adm():
    if not admin():
        return redirect(url_for('estoque'))

    conn = obter_conexao(); cur = conn.cursor(); cur.execute('SELECT * FROM usuarios'); result = cur.fetchall(); cur.close(); conn.close()
    return render_template('adm_page.html', resultado=result)

# Cria um novo usuário com senha criptografada e validação de duplicidade.
@app.route('/adicionar_user_concluido', methods=['POST'])
def adicionar_user_concluido():
    if not admin():
        return redirect(url_for('estoque'))

    nome = (request.form.get('nome') or '').strip()
    senha = request.form.get('senha') or ''
    tipo = request.form.get('selecao')

    if not nome or not senha or tipo not in ('admin', 'user'):
        return error_page('adicionar_usuario_nao_concluido.html', 'Preencha nome, senha e selecione um tipo de permissão.')

    if len(nome) > 100 or len(senha) > 72:
        return error_page('adicionar_usuario_nao_concluido.html', 'O nome deve ter até 100 caracteres e a senha até 72.')

    conn = obter_conexao(); cur = conn.cursor()
    cur.execute('SELECT id FROM usuarios WHERE nome = %s LIMIT 1', (nome,))
    if cur.fetchone():
        cur.close(); conn.close()
        return error_page('adicionar_usuario_nao_concluido.html', 'Já existe um usuário com esse nome.')

    hash_senha = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
    cur.execute('INSERT INTO usuarios (nome, senha, tipo) VALUES (%s, %s, %s)', (nome, hash_senha, tipo))
    conn.commit(); cur.close(); conn.close()
    return render_template('adicionar_user_concluido.html')

# Exclui tudo do estoque; só administrador pode executar essa ação.
@app.route('/estoque/excluir-todos', methods=['POST'])
def excluir_todos_itens():
    if not admin():
        return redirect(url_for('estoque'))

    conn = obter_conexao(); cur = conn.cursor(); cur.execute('DELETE FROM objetos_do_roger'); conn.commit(); cur.close(); conn.close()
    return redirect(url_for('estoque'))

# Exporta o estoque em CSV para download em Excel ou planilha.
@app.route('/estoque/exportar-csv')
def exportar_csv():
    if not logged():
        return redirect(url_for('index'))

    conn = obter_conexao(); cur = conn.cursor(); cur.execute('SELECT id, nome, descricao, qtd, preco, imagem FROM objetos_do_roger'); itens = cur.fetchall(); cur.close(); conn.close()
    arquivo = io.StringIO(); writer = csv.writer(arquivo, delimiter=';')
    writer.writerow(['id', 'nome', 'descricao', 'qtd', 'preco', 'imagem'])
    writer.writerows(itens)
    arquivo.seek(0)
    return send_file(io.BytesIO(arquivo.getvalue().encode('utf-8-sig')), mimetype='text/csv', as_attachment=True, download_name='estoque.csv')

# Importa itens em lote a partir de um CSV enviado pelo usuário logado.
@app.route('/estoque/importar-csv', methods=['POST'])
def importar_csv():
    if not logged():
        return redirect(url_for('index'))

    arquivo = request.files.get('arquivo_csv')
    if arquivo is None or arquivo.filename == '':
        return redirect(url_for('estoque'))

    reader = csv.DictReader(io.TextIOWrapper(arquivo.stream, encoding='utf-8-sig'), delimiter=';')
    conn = obter_conexao(); cur = conn.cursor()
    for linha in reader:
        cur.execute('INSERT INTO objetos_do_roger (nome, descricao, qtd, preco, imagem) VALUES (%s, %s, %s, %s, %s)', (linha['nome'], linha['descricao'], int(linha['qtd']), float(linha['preco']), linha['imagem']))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for('estoque'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
