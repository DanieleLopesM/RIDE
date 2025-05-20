# Importações dos módulos do Flask
from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import flash

# Importação da biblioteca utilizada para criptografar a senha do usuário.
import hashlib

# Importa a função responsável pela conexão com o banco de dados.
from application.models.connection import connect_to_database

# Cria o blueprint para as rotas relacionadas à autenticação de usuários.
authentication_blueprint = Blueprint(
    'authentication',
    __name__               
)
    
# Rota de login do usuário.
@authentication_blueprint.route('/', methods=['GET', 'POST'])
def login_user():

    # Verifica se o formulário foi enviado com método POST.
    if request.method == 'POST':

        # Recupera os dados digitados no formulário de login.
        cpf = request.form['cpf']
        password = request.form['senha']

        # Estabelece conexão com o banco de dados.
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)

        # Busca o usuário com CPF correspondente e que esteja ativo.
        cursor.execute("SELECT * FROM usuario WHERE cpf = %s AND ativo = 1", (cpf,))
        user_data = cursor.fetchone()

        # Verifica se o usuário existe.
        if user_data:

            # Criptografa a senha informada para comparação.
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Compara o hash da senha com o valor armazenado no banco.
            if user_data['senha'] == hashed_password:

                # Armazena as informações do usuário na sessão.
                session['user_id'] = user_data['id_usuario']
                session['user_name'] = user_data['nome']
                session['user_role'] = user_data['perfil']

                # Encerra a conexão com o banco.
                cursor.close()
                connection.close()

                # Redireciona para o painel de gerenciamento.
                return redirect(url_for('dashboard.management_panel'))
            else:
                # Fecha a conexão com o banco de dados..
                cursor.close()
                connection.close()

                # Exibe mensagem de erro ao usuário.
                flash("Suas informações não conferem!!!", "danger")
                return redirect(url_for('authentication.login_user'))
        else:
            # Fecha a conexão antes de exibir o erro.
            cursor.close()
            connection.close()

            # Exibe mensagem de erro ao usuário.
            flash("Suas informações não conferem.", "danger")
            return redirect(url_for('authentication.login_user'))

    # Se for GET, exibe o formulário de login.
    return render_template('index.html')

# Rota responsável por realizar o logout do usuário.
@authentication_blueprint.route('/logout')
def logout_user():

    # Limpa todos os dados salvos na sessão do navegador.
    session.clear()

    # Exibe mensagem de sucesso.
    flash("Logout realizado com sucesso!!!", "success")
    return redirect(url_for('authentication.login_user'))