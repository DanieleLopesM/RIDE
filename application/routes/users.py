# Importações dos módulos do Flask.
from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import flash

# Importa a biblioteca que gera o hash seguro das senhas.
import hashlib

# Importa a função que realiza a conexão com o banco de dados.
from application.models.connection import connect_to_database

# Cria o blueprint que agrupa todas as rotas de gerenciamento de usuários.
users_blueprint = Blueprint('users', __name__)

# Rota que exibe a lista de usuários ativos cadastrados.
@users_blueprint.route('/users')
def list_users():

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Abre conexão com o banco.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Consulta todos os usuários ativos.
    cursor.execute("SELECT id_usuario, nome, cpf, perfil FROM usuario WHERE ativo = 1")
    users = cursor.fetchall()

    # Encerra a conexão.
    cursor.close()
    connection.close()

    # Renderiza o template com os usuários.
    return render_template('users.html', users=users, name=session['user_name'], role=session['user_role'])

# Rota que exibe o formulário e realiza o cadastro de usuário.
@users_blueprint.route('/register_user', methods=['GET', 'POST'])
def register_user():

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Verifica o nível de permissão do usuário logado.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem autorização para executar esta operação...", "danger")
        return redirect(url_for('users.list_users'))

    # Processa o envio do formulário.
    if request.method == 'POST':

        # Campos com informações do usuário.
        name = request.form['nome']
        cpf = request.form['cpf']
        password = request.form['senha']
        confirm_password = request.form['confirmar_senha']
        role = request.form['perfil']

        # Verifica se a senha e a confirmação são iguais.
        if password != confirm_password:

            # Retorna uma mensagem de erro.
            flash("Senha e confirmação de senha não conferem...", "danger")
            return redirect(url_for('users.register_user'))

        # Criptografa a senha com SHA-256.
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Conecta ao banco de dados.
        connection = connect_to_database()
        cursor = connection.cursor()

        try:

            # Insere o novo usuário no banco de dados.
            cursor.execute("""
                INSERT INTO usuario (nome, cpf, senha, perfil, ativo)
                VALUES (%s, %s, %s, %s, 1)
            """, (name, cpf, hashed_password, role))

            # Confirma o sucesso da operação.
            connection.commit()
            flash("Usuário cadastrado com sucesso!!!", "success")
            return redirect(url_for('users.list_users'))
        
        except Exception:

            # Em caso de erro, desfaz a operação.
            connection.rollback()
            flash("Erro ao cadastrar usuário!!! Verifique se o CPF já está em uso...", "danger")
            return redirect(url_for('users.register_user'))
        
        finally:

            # Encerra a conexão com o banco de dados.
            cursor.close()
            connection.close()

    # Renderiza o formulário de cadastro de usuário.
    return render_template('register_user.html', name=session['user_name'], role=session['user_role'])

# Rota para edição de dados de um usuário existente.
@users_blueprint.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Verifica a permissão de acesso do perfil logado.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem autorização para executar esta operação...", "danger")
        return redirect(url_for('users.list_users'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Processa os dados enviados por formulário.
    if request.method == 'POST':

        # Campos com informações do usuário.
        name = request.form['nome']
        cpf = request.form['cpf']
        role = request.form['perfil']

        try:

            # Atualiza os dados do usuário.
            cursor.execute("""
                UPDATE usuario SET nome = %s, cpf = %s, perfil = %s
                WHERE id_usuario = %s
            """, (name, cpf, role, user_id))

            # Informa o sucesso da operação.
            connection.commit()
            flash("Usuário atualizado com sucesso!!!", "success")
            return redirect(url_for('users.list_users'))
        
        except Exception:

            # Retorna uma mensagem de erro.
            connection.rollback()
            flash("Erro ao atualizar as informações do usuário...", "danger")
            return redirect(url_for('users.edit_user', user_id=user_id))
        
        finally:

            # Encerra a conexão com o banco de dados.
            cursor.close()
            connection.close()

    # Busca os dados do usuário para exibir no formulário.
    cursor.execute("SELECT * FROM usuario WHERE id_usuario = %s AND ativo = 1", (user_id,))
    user = cursor.fetchone()

    # Encerra a conxão com o banco de dados.
    cursor.close()
    connection.close()

    # Verifica se o usuário existe.
    if not user:

        # Retorna uma mensagem de erro.
        flash("Usuário não encontrado...", "danger")
        return redirect(url_for('users.list_users'))

    # Renderiza o HTML de edição de usuário.
    return render_template('edit_user.html', user=user, name=session['user_name'], role=session['user_role'])

# Rota para edição do perfil do próprio usuário.
@users_blueprint.route('/edit_user_profile', methods=['GET', 'POST'])
def edit_user_profile():

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Processa os dados enviados pelo formulário.
    if request.method == 'POST':

        # Recupera os campos enviados pelo formulário.
        name = request.form['nome']
        cpf = request.form['cpf']
        current_password = request.form.get('senha_atual')
        new_password = request.form.get('senha')
        confirm_password = request.form.get('confirmar_senha')

        try:
            # Verifica se o usuário existe e está ativo.
            cursor.execute("SELECT senha FROM usuario WHERE id_usuario = %s AND ativo = 1", (session['user_id'],))
            user_data = cursor.fetchone()

            # Se não encontrar o usuário, desfaz a operação.
            if not user_data:

                # Retorna uma mensagem de erro.
                flash("Usuário não encontrado...", "danger")
                return redirect(url_for('dashboard.management_panel'))

            # Se o campo de nova senha estiver preenchido, tenta realizar a alteração.
            if new_password:

                # Verifica se a senha atual foi preenchida.
                if not current_password:

                    # Retorna uma mensagem de erro.
                    flash("Informe a senha atual para alterar sua senha...", "danger")
                    return redirect(url_for('users.edit_user_profile'))

                # Criptografa a senha atual com SHA-256.
                current_password_hash = hashlib.sha256(current_password.encode()).hexdigest()

                # Compara com o SHA-256 da senha armazenada.
                if current_password_hash != user_data['senha']:

                    # Retorna uma mensagem de erro.
                    flash("Senha atual incorreta...", "danger")
                    return redirect(url_for('users.edit_user_profile'))

                # Verifica se a nova senha e a confirmação coincidem.
                if new_password != confirm_password:

                    # Retorna uma mensagem de erro.
                    flash("Nova senha e confirmação de senha não conferem...", "danger")
                    return redirect(url_for('users.edit_user_profile'))

                # Criptografa a senha com SHA-256.
                new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()

                # Atualiza os dados com a nova senha.
                cursor.execute("""
                    UPDATE usuario SET nome = %s, cpf = %s, senha = %s
                    WHERE id_usuario = %s
                """, (name, cpf, new_password_hash, session['user_id']))

            else:

                # Atualiza apenas o nome e CPF do usuário.
                cursor.execute("""
                    UPDATE usuario SET nome = %s, cpf = %s
                    WHERE id_usuario = %s
                """, (name, cpf, session['user_id']))

            # Confirma as alterações no banco de dados.
            connection.commit()

            # Atualiza o nome salvo na sessão de usuário.
            session['user_name'] = name

            # Retorna uma mensagem de sucesso.
            flash("Perfil atualizado com sucesso!!!", "success")
            return redirect(url_for('dashboard.management_panel'))

        except Exception:

            # Desfaz as alterações alterações no banco de dados.
            connection.rollback()

            # Retorna uma mensagem de erro.
            flash("Erro ao atualizar suas informações...", "danger")
            return redirect(url_for('users.edit_user_profile'))

        finally:

            # Fecha a conexão com o banco de dados.
            cursor.close()
            connection.close()

    # Busca as informações atuais do usuário para preencher o formulário.
    cursor.execute("SELECT * FROM usuario WHERE id_usuario = %s AND ativo = 1", (session['user_id'],))
    user = cursor.fetchone()

    # Fecha a conexão com o banco de dados.
    cursor.close()
    connection.close()

    # Verifica se encontrou o usuário.
    if not user:

        # Retorna uma mensagem de erro.
        flash("Usuário não encontrado...", "danger")
        return redirect(url_for('dashboard.management_panel'))

    # Renderiza o formulário de edição de perfil com os dados do usuário.
    return render_template('edit_user_profile.html', user=user, name=session['user_name'], role=session['user_role'])

# Rota para redefinição de senha de um usuário.
@users_blueprint.route('/reset_password/<int:user_id>', methods=['POST'])
def reset_password(user_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Permite acesso apenas para Diretores e Gestores.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem autorização para executar esta operação...", "danger")
        return redirect(url_for('users.list_users'))

    # Recupera os campos enviados pelo formulário.
    password = request.form['senha']
    confirm_password = request.form['confirmar_senha']

    # Verifica se as senhas coincidem.
    if password != confirm_password:

        # Retorna uma mensagem de erro.
        flash("Senha e confirmação de senha não conferem...", "danger")
        return redirect(url_for('users.list_users'))

    # Criptografa a nova senha.
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor()

    try:

        # Atualiza a senha no banco de dados.
        cursor.execute("UPDATE usuario SET senha = %s WHERE id_usuario = %s", (hashed_password, user_id))
        connection.commit()
        flash("Senha redefinida com sucesso!!!", "success")

    except Exception:

        # Retorna uma mensagem de erro.
        connection.rollback()
        flash("Erro ao redefinir a senha do usuário...", "danger")

    finally:

        # Encerra a conexão com o banco de dados.
        cursor.close()
        connection.close()

    # Redireciona o usuário para a listagem de usuários.
    return redirect(url_for('users.list_users'))

# Rota para realizar a exclusão lógica de um usuário.
@users_blueprint.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Verifica se o perfil de usuário possui autorização para executar a operação.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem autorização para executar esta operação...", "danger")
        return redirect(url_for('users.list_users'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor()

    try:

        # Atualiza o campo do banco de dados para desativar o usuário.
        cursor.execute("UPDATE usuario SET ativo = 0 WHERE id_usuario = %s", (user_id,))
        connection.commit()
        flash("Usuário excluído com sucesso!!!", "success")

    except Exception:

        # Retorna uma mensagem de erro.
        connection.rollback()
        flash("Erro ao excluir o usuário...", "danger")

    finally:

        # Encerra a conexão com o banco de dados.
        cursor.close()
        connection.close()

    # Redireciona o usuário para a listagem de usuários.
    return redirect(url_for('users.list_users'))