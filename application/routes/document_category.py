# Importações dos módulos do Flask.
from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import flash

# Importa a função de conexão com o banco de dados.
from application.models.connection import connect_to_database

# Cria o blueprint responsável pelas rotas de categorias de documentos.
category_blueprint = Blueprint('document_category', __name__)

# Rota que exibe todas as categorias cadastradas.
@category_blueprint.route('/categories')
def list_categories():

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Permite apenas Diretor e Gestor acessarem esta funcionalidade.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem permissão para acessar as categorias de documentos...", "danger")
        return redirect(url_for('dashboard.management_panel'))

    # Faz a conexão com o banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Recupera todos os cadastros ativos.
    cursor.execute("""
        SELECT c.id_categoria, c.nome_categoria, c.data_criacao, u.nome AS criado_por
        FROM categoria_documento AS c
        INNER JOIN usuario AS u ON u.id_usuario = c.id_usuario
        WHERE c.ativo = 1
        ORDER BY c.data_criacao DESC
    """)
    categories = cursor.fetchall()

    # Encerra a conexão com o banco de dados.
    cursor.close()
    connection.close()

    # Renderiza a tela com a lista de categorias.
    return render_template('categories.html', categories=categories, name=session['user_name'], role=session['user_role'])

# Rota para cadastrar uma nova categoria de documento.
@category_blueprint.route('/register_category', methods=['GET', 'POST'])
def register_category():

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('user_authentication.login_user'))

    # Apenas Diretor e Gestor podem cadastrar categorias.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem permissão para cadastrar categorias...", "danger")
        return redirect(url_for('document_category.list_categories'))

    # Processa o envio do formulário.
    if request.method == 'POST':

        # Recupera o nome da categoria.
        category_name = request.form['nome']

        # Faz a conexão com o banco de dados.
        connection = connect_to_database()
        cursor = connection.cursor()

        try:

            # Insere a nova categoria no banco de dados.
            cursor.execute("""
                INSERT INTO categoria_documento (nome_categoria, id_usuario)
                VALUES (%s, %s)
            """, (category_name, session['user_id']))

            # Retorna uma mensagem de sucesso.
            connection.commit()
            flash("Categoria cadastrada com sucesso!!!", "success")
            return redirect(url_for('document_category.list_categories'))
        
        except Exception:

            # Retorna uma mensagem de erro.
            connection.rollback()
            flash("Erro ao cadastrar a categoria!!! Verifique se já existe uma com o mesmo nome...", "danger")
            return redirect(url_for('document_category.register_category'))
        
        finally:

            # Encerra a conexão com o banco de dados.
            cursor.close()
            connection.close()

    # Exibe o formulário de cadastro.
    return render_template('register_category.html', name=session['user_name'], role=session['user_role'])

# Rota para edição de uma categoria de documento.
@category_blueprint.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Verifica se o perfil do usuário tem permissão.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem autorização para executar esta operação...", "danger")
        return redirect(url_for('document_category.list_categories'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Processa o envio do formulário.
    if request.method == 'POST':

        # Recupera o nome informado no formulário.
        name = request.form['nome']

        try:

            # Atualiza o nome da categoria no banco de dados.
            cursor.execute("""
                UPDATE categoria_documento SET nome_categoria = %s
                WHERE id_categoria = %s
            """, (name, category_id))

            # Confirma a alteração.
            connection.commit()
            flash("Categoria atualizada com sucesso!!!", "success")
            return redirect(url_for('document_category.list_categories'))

        except Exception:

            # Desfaz alterações em caso de erro.
            connection.rollback()
            flash("Erro ao atualizar a categoria...", "danger")
            return redirect(url_for('document_category.edit_category', category_id=category_id))

        finally:

            # Encerra a conexão com o banco de dados.
            cursor.close()
            connection.close()

    # Busca os dados da categoria no banco de dados.
    cursor.execute("SELECT * FROM categoria_documento WHERE id_categoria = %s AND ativo = 1", (category_id,))
    category = cursor.fetchone()

    # Encerra a conexão com o banco de dados.
    cursor.close()
    connection.close()

    # Verifica se a categoria existe.
    if not category:

        # Retorna uma mensagem de erro.
        flash("Categoria não encontrada...", "danger")
        return redirect(url_for('document_category.list_categories'))

    # Renderiza o formulário de edição com os dados atuais.
    return render_template('edit_category.html', category=category, name=session['user_name'], role=session['user_role'])

# Rota para realizar a exclusão lógica de um usuário.
@category_blueprint.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):

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

        # Atualiza o campo do banco de dados para desativar a categoria.
        cursor.execute("UPDATE categoria_documento SET ativo = 0 WHERE id_categoria = %s", (category_id,))
        connection.commit()
        flash("Categoria de documento excluída com sucesso!!!", "success")

    except Exception:

        # Retorna uma mensagem de erro.
        connection.rollback()
        flash("Erro ao excluir a categoria de documento...", "danger")

    finally:

        # Encerra a conexão com o banco de dados.
        cursor.close()
        connection.close()

    # Redireciona o usuário para a listagem de usuários.
    return redirect(url_for('document_category.list_categories'))