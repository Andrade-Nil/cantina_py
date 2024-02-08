from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import json  # Adicione esta linha
import sys  # Adicione esta linha
sys.stdout.flush()

app = Flask(__name__)

# Dados de usuário para validar
usuario_valido = 'admin'
senha_valida = '123'

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    usuario_digitado = request.form.get('usuario')
    senha_digitada = request.form.get('senha')

    if usuario_digitado == usuario_valido and senha_digitada == senha_valida:
        # Se as credenciais são válidas, redireciona para a página principal
        return redirect(url_for('pagina_principal'))
    else:
        # Se as credenciais são inválidas, exibe uma mensagem de erro
        return render_template('login.html', erro='Credenciais inválidas. Tente novamente.')

@app.route('/principal')
def pagina_principal():
    create_table()
    # Consultar dados dos alunos no banco de dados
    with sqlite3.connect(DATABASE) as con:
        con.row_factory = sqlite3.Row  # Para acessar as colunas pelo nome
        cur = con.cursor()
        cur.execute('SELECT id, nome, ano, credito FROM alunos ORDER BY ano, nome')
        alunos = cur.fetchall()

    # Organizar os alunos por ano
    alunos_por_ano = {}
    for aluno in alunos:
        ano = aluno['ano']
        if ano not in alunos_por_ano:
            alunos_por_ano[ano] = []
        alunos_por_ano[ano].append(aluno)

    return render_template('principal.html', alunos_por_ano=alunos_por_ano)


# Configurações do SQLite
DATABASE = 'alunos.db'

# Função para criar a tabela se ela não existir
def create_table():
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                turno TEXT,
                ano TEXT,
                responsavel TEXT,
                contato TEXT,
                credito TEXT,
                segunda TEXT DEFAULT '0,00',
                terca TEXT DEFAULT '0,00',
                quarta TEXT DEFAULT '0,00',
                quinta TEXT DEFAULT '0,00',
                sexta TEXT DEFAULT '0,00'
            )
        ''')


# Rota para lidar com o envio do formulário
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    create_table()
    if request.method == 'POST':
        nome = request.form['nome']
        turno = request.form['turno']
        ano = request.form['ano']
        responsavel = request.form['responsavel']
        contato = request.form['contato']
        credito = request.form['credito']
        segunda = '0,00'
        terca = '0,00'
        quarta = '0,00'
        quinta = '0,00'
        sexta = '0,00'

        # Inserir dados no banco de dados
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            cur.execute('INSERT INTO alunos (nome, turno, ano, responsavel, contato, credito, segunda, terca, quarta, quinta, sexta) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (nome, turno, ano, responsavel, contato, credito, segunda, terca, quarta, quinta, sexta))
            con.commit()

    # Redirecionar para a página de cadastro
    return render_template('cadastro.html', success_message='Cadastro realizado com sucesso!')


# Rota para exibir a lista de alunos
@app.route('/lista_alunos')
def lista_alunos():
    # Consultar dados dos alunos no banco de dados ordenados pelo nome
    with sqlite3.connect(DATABASE) as con:
        con.row_factory = sqlite3.Row  # Para acessar as colunas pelo nome
        cur = con.cursor()
        cur.execute('SELECT id, nome, turno, ano, responsavel, contato, credito FROM alunos ORDER BY nome')
        alunos = cur.fetchall()

    return render_template('lista_alunos.html', alunos=alunos)


# Rota para editar alunos
@app.route('/editar_aluno/<int:aluno_id>', methods=['GET', 'POST'])
def editar_aluno(aluno_id):
    if request.method == 'GET':
        # Consultar dados do aluno pelo ID e passar para o template
        with sqlite3.connect(DATABASE) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute('SELECT * FROM alunos WHERE id = ?', (aluno_id,))
            aluno = cur.fetchone()

        return render_template('editar_aluno.html', aluno=aluno)
    elif request.method == 'POST':
        # Obter os dados atualizados do formulário
        nome = request.form.get('nome')
        ano = request.form.get('ano')
        turno = request.form.get('turno')
        responsavel = request.form.get('responsavel')
        contato = request.form.get('contato')
        credito = request.form.get('credito')

        # Atualizar os dados no banco de dados
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            cur.execute('''
                UPDATE alunos
                SET nome=?, ano=?, turno=?, responsavel=?, contato=?, credito=?
                WHERE id=?
            ''', (nome, ano, turno, responsavel, contato, credito, aluno_id))


        # Redirecionar para a lista de alunos após a edição
        return redirect(url_for('lista_alunos'))


@app.route('/subtrair_credito', methods=['POST'])
def subtrair_credito():
    try:
        # Carrega os dados JSON recebidos
        data = json.loads(request.data)
        print(f'Dados recebidos para atualização de crédito: {data}')

        # Percorre os dados enviados pelo frontend
        for aluno_id, consumo_total in data.items():
            aluno_id = int(aluno_id)
            consumo_total = float(str(consumo_total).replace(',', '.'))  # Converte para float e substitui a vírgula por ponto

            # Consulta o crédito atual do aluno no banco de dados
            with sqlite3.connect(DATABASE) as con:
                cur = con.cursor()
                cur.execute('SELECT credito FROM alunos WHERE id = ?', (aluno_id,))
                result = cur.fetchone()
                credito_atual = float(str(result[0]).replace(',', '.')) if result else 0.0
                print(f'Crédito atual do aluno {aluno_id}: {credito_atual}')


            # Calcula o novo crédito
            novo_credito = credito_atual - consumo_total
            print(f'Novo crédito do aluno {aluno_id}: {novo_credito}')

            # Atualiza o crédito do aluno no banco de dados
            with sqlite3.connect(DATABASE) as con:
                cur = con.cursor()

                # Convertendo novo_credito de float para string com vírgula
                credito= '{:.2f}'.format(novo_credito).replace('.', ',')

                cur.execute('UPDATE alunos SET credito = ? WHERE id = ?', (credito, aluno_id))
                con.commit()


        return jsonify({'success': True})
    except Exception as e:
        print(f"Erro interno: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/realizar_pagamento', methods=['POST'])
def realizar_pagamento():
    try:
        data = json.loads(request.data)
        aluno_id = int(data['alunoId'])
        valor_pagamento = float(data['valorPagamento'].replace(',', '.'))

        # Consultar crédito atual do aluno no banco de dados
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            cur.execute('SELECT credito FROM alunos WHERE id = ?', (aluno_id,))
            result = cur.fetchone()
            credito_atual = float(result[0].replace(',', '.')) if result else 0.0

        # Calcular novo crédito
        novo_credito = credito_atual + valor_pagamento

        # Atualizar crédito no banco de dados
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            cur.execute('UPDATE alunos SET credito = ? WHERE id = ?', ('{:.2f}'.format(novo_credito).replace('.', ','), aluno_id))
            con.commit()

        return jsonify({'success': True, 'novoCredito': '{:.2f}'.format(novo_credito).replace('.', ',')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Adicione esta rota para lidar com a exclusão do aluno
@app.route('/excluir_aluno/<int:aluno_id>', methods=['GET'])
def excluir_aluno(aluno_id):
    try:
        # Execute a lógica para excluir o aluno do banco de dados
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            cur.execute('DELETE FROM alunos WHERE id = ?', (aluno_id,))
            con.commit()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True)
