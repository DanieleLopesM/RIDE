# Importações dos módulos do Flask.
from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import flash
from flask import send_file

# Importação do módulo que permite a entrada e saída de arquivos binários.
from io import BytesIO

# Importação da função de conexão com o banco de dados.
from application.models.connection import connect_to_database

# Cria o blueprint responsável pelas rotas de modelos de documentos.
document_model_blueprint = Blueprint('document_model', __name__)

# Rota que exibe todos os modelos de documentos cadastrados.
@document_model_blueprint.route('/models')
def list_models():

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Consulta os modelos de documentos com suas informações associadas.
    cursor.execute("""
        SELECT m.id_modelo_documento, m.titulo, m.descricao, m.data_envio,
               c.nome_categoria, u.nome AS nome_usuario
        FROM modelo_documento AS m
        INNER JOIN categoria_documento AS c ON c.id_categoria = m.id_categoria
        INNER JOIN usuario AS u ON u.id_usuario = m.id_usuario
        WHERE m.ativo = 1
        ORDER BY m.data_envio DESC
    """)
    models = cursor.fetchall()

    # Encerra a conexão com o banco de dados.
    cursor.close()
    connection.close()

    # Renderiza o HTML com a lista de modelos.
    return render_template('models.html', models=models, name=session['user_name'], role=session['user_role'])

# Rota para cadastro de um novo modelo de documento.
@document_model_blueprint.route('/register_model', methods=['GET', 'POST'])
def register_model():

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Permite apenas Diretores e Gestores cadastrarem modelos.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem permissão para cadastrar modelos de documentos...", "danger")
        return redirect(url_for('document_model.list_models'))

    # Conecta-se ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Busca categorias de documentos ativas.
    cursor.execute("SELECT id_categoria, nome_categoria FROM categoria_documento WHERE ativo = 1 ORDER BY nome_categoria ASC")
    categories = cursor.fetchall()

    # Processa o envio do formulário.
    if request.method == 'POST':

        # Recupera os campos enviados pelo formulário.
        title = request.form['titulo']
        description = request.form['descricao']
        category_id = request.form['categoria']
        file = request.files['arquivo']

        # Verifica se o arquivo foi enviado.
        if file.filename == '':

            # Retorna uma mensagem de erro.
            flash("Por favor, selecione um arquivo para enviar...", "danger")
            return redirect(url_for('document_model.register_model'))

        try:

            # Lê o conteúdo binário do arquivo.
            file_data = file.read()

            # Insere o modelo de documento no banco de dados.
            cursor.execute("""
                INSERT INTO modelo_documento (titulo, descricao, arquivo, id_categoria, id_usuario)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, description, file_data, category_id, session['user_id']))

            # Confirma a operação no banco de dados.
            connection.commit()

            # Retorna uma mensagem de sucesso.
            flash("Modelo de documento cadastrado com sucesso!!!", "success")
            return redirect(url_for('document_model.list_models'))

        except Exception:

            # Desfaz qualquer alteração feita no banco de dados.
            connection.rollback()

            # Retorna uma mensagem de erro.
            flash("Erro ao cadastrar o modelo de documento...", "danger")
            return redirect(url_for('document_model.register_model'))

        finally:

            # Encerra a conexão com o banco de dados.
            cursor.close()
            connection.close()

    # Renderiza o HTML de cadastro de modelos de documentos.
    return render_template('register_model.html', categories=categories, name=session['user_name'], role=session['user_role'])

# Rota para edição de um modelo de documento existente.
@document_model_blueprint.route('/edit_model/<int:model_id>', methods=['GET', 'POST'])
def edit_model(model_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Verifica se o perfil do usuário tem permissão para editar modelos.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem autorização para editar modelos de documentos...", "danger")
        return redirect(url_for('document_model.list_models'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Busca os dados atuais do modelo.
    cursor.execute("SELECT * FROM modelo_documento WHERE id_modelo_documento = %s AND ativo = 1", (model_id,))
    model = cursor.fetchone()

    # Verifica se o modelo existe.
    if not model:

        # Retorna uma mensagem de erro.
        flash("Modelo de documento não encontrado...", "danger")

        # Encerra a conexão com o banco de dados.
        cursor.close()
        connection.close()

        # Redireciona o usuário para a tela de listagem de modelos.
        return redirect(url_for('document_model.list_models'))

    # Busca as categorias disponíveis para edição.
    cursor.execute("SELECT id_categoria, nome_categoria FROM categoria_documento WHERE ativo = 1 ORDER BY nome_categoria ASC")
    categories = cursor.fetchall()

    # Processa os dados enviados via formulário.
    if request.method == 'POST':

        # Recupera os dados do formulário.
        title = request.form['titulo']
        description = request.form['descricao']
        category_id = request.form['categoria']
        file = request.files['arquivo']

        try:
            # Verifica se foi enviado um novo arquivo.
            if file and file.filename != '':

                # Lê o conteúdo do novo arquivo.
                file_data = file.read()

                # Atualiza todos os dados, incluindo o arquivo.
                cursor.execute("""
                    UPDATE modelo_documento
                    SET titulo = %s, descricao = %s, arquivo = %s, id_categoria = %s
                    WHERE id_modelo_documento = %s
                """, (title, description, file_data, category_id, model_id))

            else:
                # Atualiza os dados sem alterar o arquivo atual.
                cursor.execute("""
                    UPDATE modelo_documento
                    SET titulo = %s, descricao = %s, id_categoria = %s
                    WHERE id_modelo_documento = %s
                """, (title, description, category_id, model_id))

            # Confirma a alteração no banco de dados.
            connection.commit()

            # Retorna uma mensagem de sucesso.
            flash("Modelo de documento atualizado com sucesso!!!", "success")
            return redirect(url_for('document_model.list_models'))

        except Exception:

            # Desfaz a operação em caso de erro.
            connection.rollback()

            # Retorna uma mensagem de erro.
            flash("Erro ao atualizar o modelo de documento...", "danger")
            return redirect(url_for('document_model.edit_model', model_id=model_id))

        finally:

            # Encerra a conexão com o banco de dados.
            cursor.close()
            connection.close()

    # Renderiza o formulário de edição com os dados atuais.
    return render_template('edit_model.html', model=model, categories=categories, name=session['user_name'], role=session['user_role'])

# Rota para download de um modelo de documento.
@document_model_blueprint.route('/download_model/<int:model_id>')
def download_model(model_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Busca o arquivo do modelo de documento com base em seu ID.
    cursor.execute("""
        SELECT titulo, arquivo
        FROM modelo_documento
        WHERE id_modelo_documento = %s AND ativo = 1
    """, (model_id,))
    model = cursor.fetchone()

    # Encerra a conexão com o banco.
    cursor.close()
    connection.close()

    # Verifica se o modelo de documento existe.
    if not model or not model['arquivo']:

        # Retorna uma mensagem de erro.
        flash("Modelo de documento não encontrado...", "danger")
        return redirect(url_for('document_model.list_models'))

    # Prepara o arquivo para download.
    return send_file(
        BytesIO(model['arquivo']),
        as_attachment=True,
        download_name=f"{model['titulo']}.docx",
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

# Rota para exclusão lógica de um modelo de documento.
@document_model_blueprint.route('/delete_model/<int:model_id>', methods=['POST'])
def delete_model(model_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Verifica se o perfil do usuário tem permissão para excluir modelos.
    if session['user_role'] not in ['Diretor', 'Gestor']:

        # Retorna uma mensagem de erro.
        flash("Você não tem autorização para executar esta operação...", "danger")
        return redirect(url_for('document_model.list_models'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor()

    try:

        # Atualiza o modelo para inativo (exclusão lógica).
        cursor.execute("UPDATE modelo_documento SET ativo = 0 WHERE id_modelo_documento = %s", (model_id,))

        # Confirma a operação.
        connection.commit()

        # Retorna uma mensagem de sucesso.
        flash("Modelo de documento excluído com sucesso!!!", "success")

    except Exception:

        # Desfaz a operação em caso de erro.
        connection.rollback()

        # Retorna uma mensagem de erro.
        flash("Erro ao excluir o modelo de documento...", "danger")

    finally:

        # Encerra a conexão com o banco de dados.
        cursor.close()
        connection.close()

    # Redireciona o usuário para a listagem de modelos.
    return redirect(url_for('document_model.list_models'))