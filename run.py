# Importação das bibliotecas para rodar softwares da web.
from flask import Flask 
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import flash
from flask import get_flashed_messages

# Importação da biblioteca de criptografia de dados sensíveis.
import hashlib

# Importação da função de conexão com o banco de dados.
from database_connect import database_connection

# Configuração do software da web.
application = Flask(__name__)
application.config['SECRET_KEY'] = '42ba728957e22d69175bdfa4d08c634c'

# Rota para a pagina inicial (login de usuário).
@application.route('/', methods=['GET', 'POST'])
def login():

    # Processa os dados de usuário vindos do formulário. 
    if request.method == 'POST':

        # Dados recuperados do formulário.
        cpf = request.form['cpf']
        senha = request.form['senha']

        # Abre uma conexão com o banco de dados.
        connect = database_connection()
        cursor = connect.cursor(dictionary=True)

        # Verifica se as informações digitadas existem no banco de dados.
        cursor.execute("SELECT * FROM usuario WHERE cpf = %s AND ativo = 1", (cpf,))
        usuario = cursor.fetchone()

        # Verifica se o usuário existe.
        if usuario:

            # Gera o hash (SHA-256) da senha digitada no formulário.
            senha_hash = hashlib.sha256(senha.encode()).hexdigest()

            # Verifica se a senha do usuário esta correta.
            if usuario['senha'] == senha_hash:

                # Caso o usuario exista salva suas informações na sessão do navegador.
                session['id_usuario'] = usuario['id_usuario']
                session['nome'] = usuario['nome']
                session['perfil'] = usuario['perfil']

                # Fecha conexão com o banco de dados.
                cursor.close()
                connect.close()

                # Redireciona o usuário para a tela central de gerenciamento (dashboard).
                return redirect(url_for('dashboard'))
            else:

                # Fecha conexão com o banco de dados.
                cursor.close()
                connect.close()

                # Mensagem de erro, com redirecionamento, devido a senha incorreta. 
                flash("Suas informações não conferem!!!", "danger")
                return redirect(url_for('login'))
        else:
            
            # Fecha conexão com o banco de dados.
            cursor.close()
            connect.close()

            # Mensagem de erro, com redirecionamento, devido a senha incorreta. 
            flash("Suas informações não conferem!!!", "danger")
            return redirect(url_for('login'))

    else:

        # Renderiza a tela de login do usuário.
        return render_template('index.html')

# Rota para o painel central de gerenciamento (dashboard).
@application.route('/dashboard')
def dashboard():

    # Verifica se o usuário esta logado. 
    if 'id_usuario' not in session:

        # Mensagem de erro, com redirecionamento, devido a usuário não logado. 
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('login'))

    # Renderiza a tela do painel central de gerenciamento (dashboard).
    return render_template('dashboard.html', nome=session['nome'], perfil=session['perfil'])

# Rota para exibir os usuário cadastrados.
@application.route('/usuarios')
def usuarios():

    # Verifica se o usuário esta logado. 
    if 'id_usuario' not in session:

        # Mensagem de erro, com redirecionamento, devido a usuário não logado. 
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('login'))

    # Abre uma conexão com o banco de dados.
    connect = database_connection()
    cursor = connect.cursor(dictionary=True)

    # Busca todos os usuário ativos cadastrados no banco de dados.
    cursor.execute("SELECT id_usuario, nome, cpf, perfil FROM usuario WHERE ativo = 1")
    usuarios = cursor.fetchall()

    # Fecha a conexão com o banco de dados.
    cursor.close()
    connect.close()

    # Renderiza a tela que exibe os usuários cadastrados no banco de dados.
    return render_template('usuarios.html', usuarios=usuarios, nome=session['nome'], perfil=session['perfil'])

# Rota para cadastrar um novo usuário.
@application.route('/novo_usuario', methods=['GET', 'POST'])
def novo_usuario():

    # Verifica se o usuário esta logado. 
    if 'id_usuario' not in session:

        # Mensagem de erro, com redirecionamento, devido a usuário não logado. 
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('login'))
    
    # Verifica o nível de acesso do usuário.
    if session['perfil'] not in ['Diretor', 'Gestor']:

        # Mensagem de erro, com redirecionamento, devido a controle de acesso. 
        flash("Você não tem autorização para executar está operação!!!", "danger")
        return redirect(url_for('usuarios'))
    
    # Processa os dados de usuário vindos do formulário. 
    if request.method == 'POST':

        # Recupera as informações digitadas no formulário.
        nome = request.form['nome']
        cpf = request.form['cpf']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']
        perfil = request.form['perfil']

        # Verifica se as senhas são iguais.
        if senha != confirmar_senha:

            # Mensagem de erro, com redirecionamento, devido a senha. 
            flash("Senha e confirmação de senha não conferem!!!", "danger")
            return redirect(url_for('novo_usuario'))
    
        # Criptografa a senha do usuário.
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()

        # Abre a conexão com o banco de dados.
        connect = database_connection()
        cursor = connect.cursor()

        # Faz a tentativa de cadastro do usuário no banco de dados.
        try:

            # SQL de cadastro das informações.
            cursor.execute("""
                INSERT INTO usuario (nome, cpf, senha, perfil, ativo)
                VALUES (%s, %s, %s, %s, 1)
            """, (nome, cpf, senha_hash, perfil))

            # Envio das informações de cadastro para o banco de dados.
            connect.commit()

            # Mensagem de sucesso, com redirecionamento, devido ao cadastro de usuário. 
            flash("Usuário cadastrado com sucesso!!!", "success")
            return redirect(url_for('usuarios'))

        # Captura qualquer tipo de erro no cadastro do usuário.
        except Exception as erro:

            # Desfaz qualquer alteração que foi feita no banco de dados.
            connect.rollback()

            # Mensagem de erro, com redirecionamento, devido a cadastro de usuário inválido. 
            flash("Não foi possível cadastrar o usuário. Verifique se o CPF já está cadastrado!!!", "danger")
            return redirect(url_for('novo_usuario'))

        # Encerra a conexão com o banco de dados.
        finally:
            cursor.close()
            connect.close()

    # Renderiza a tela de cadastro de usuário.
    return render_template('cadastrar-usuario.html', nome=session['nome'], perfil=session['perfil'])

# Rota para o logout de usuário.
@application.route('/logout')
def logout():

    # Limpa os dados da sessão de usuário.
    session.clear()

    # Mensagem de sucesso, com redirecionamento, devido ao logout do usuário. 
    flash("Logout realizado com sucesso!!!", "success")
    return redirect(url_for('login'))

# Executa o software da web.
if (__name__ == '__main__'):

    # Modo de depuração ativo.
    application.run(debug=True)