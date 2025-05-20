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

# Cria o blueprint responsável pelas rotas de documentos preenchidos.
filled_document_blueprint = Blueprint('filled_document', __name__)

# Rota que exibe os documentos preenchidos enviados.
@filled_document_blueprint.route('/filled_documents')
def list_filled_documents():

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Verifica o perfil do usuário.
    user_id = session['user_id']
    user_role = session['user_role']

    # Diretores e gestores veem todos os documentos.
    if user_role in ['Diretor', 'Gestor']:

        # Busca todos os documentos preenchidos (todos os usuários).
        cursor.execute("""
            SELECT d.id_documento_preenchido, d.data_envio, u.nome AS nome_usuario,
                   m.titulo AS titulo_modelo, c.nome_categoria
            FROM documento_preenchido AS d
            INNER JOIN modelo_documento AS m ON m.id_modelo_documento = d.id_documento_modelo
            INNER JOIN categoria_documento AS c ON c.id_categoria = m.id_categoria
            INNER JOIN usuario AS u ON u.id_usuario = d.id_usuario
            WHERE d.ativo = 1
            ORDER BY d.data_envio DESC
        """)

    # Professores veem apenas seus próprios documentos.
    else:
        
        # Busca apenas documentos preenchidos pelo próprio usuário.
        cursor.execute("""
            SELECT d.id_documento_preenchido, d.data_envio, u.nome AS nome_usuario,
                   m.titulo AS titulo_modelo, c.nome_categoria
            FROM documento_preenchido AS d
            INNER JOIN modelo_documento AS m ON m.id_modelo_documento = d.id_documento_modelo
            INNER JOIN categoria_documento AS c ON c.id_categoria = m.id_categoria
            INNER JOIN usuario AS u ON u.id_usuario = d.id_usuario
            WHERE d.ativo = 1 AND d.id_usuario = %s
            ORDER BY d.data_envio DESC
        """, (user_id,))

    # Armazena os resultados.
    filled_documents = cursor.fetchall()

    # Encerra a conexão com o banco de dados.
    cursor.close()
    connection.close()

    # Renderiza o HTML com os documentos preenchidos.
    return render_template('filled_document.html', filled_documents=filled_documents, name=session['user_name'], role=session['user_role'])

# Rota para submissão de novo documento preenchido.
@filled_document_blueprint.route('/send_filled_document', methods=['GET', 'POST'])
def send_filled_document():

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Busca categorias ativas para exibir no formulário.
    cursor.execute("""
        SELECT id_categoria, nome_categoria
        FROM categoria_documento
        WHERE ativo = 1
        ORDER BY nome_categoria ASC
    """)
    categories = cursor.fetchall()

    # Processa o formulário enviado via POST.
    if request.method == 'POST':

        # Recupera os dados do formulário.
        category_id = request.form.get('categoria')
        model_id = request.form.get('modelo')
        file = request.files.get('arquivo')

        # Verifica se todos os campos obrigatórios foram preenchidos.
        if not category_id or not model_id or not file or file.filename == '':

            # Retorna uma mensagem de erro.
            flash("Todos os campos são obrigatórios. Verifique e tente novamente...", "danger")
            return redirect(url_for('filled_document.send_filled_document'))

        try:

            # Lê o conteúdo binário do arquivo.
            file_data = file.read()

            # Verifica se o arquivo é um PDF válido.
            if not file.filename.lower().endswith('.pdf'):

                # Retorna uma mensagem de erro.
                flash("O arquivo deve estar em formato de PDF...", "danger")
                return redirect(url_for('filled_document.send_filled_document'))

            # Insere o novo documento preenchido no banco de dados.
            cursor.execute("""
                INSERT INTO documento_preenchido (id_documento_modelo, id_usuario, arquivo)
                VALUES (%s, %s, %s)
            """, (model_id, session['user_id'], file_data))

            # Confirma a operação no banco de dados.
            connection.commit()

            # Retorna uma mensagem de sucesso.
            flash("Documento preenchido enviado com sucesso!!!", "success")
            return redirect(url_for('filled_document.list_filled_documents'))

        except Exception:

            # Desfaz a operação no banco de dados.
            connection.rollback()

            # Retorna uma mensagem de erro.
            flash("Erro ao enviar o documento preenchido...", "danger")
            return redirect(url_for('filled_document.send_filled_document'))

        finally:

            # Encerra a conexão com o banco de dados.
            cursor.close()
            connection.close()

    # Renderiza o HTML com o formulário do stepper.
    return render_template('send_filled_document.html', categories=categories, name=session['user_name'], role=session['user_role'])

# Rota que retorna os modelos de documentos de uma determinada categoria (usada via AJAX).
@filled_document_blueprint.route('/get_models_by_category/<int:category_id>')
def get_models_by_category(category_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna um código (HTTP) de erro.
        return {"error": "Unauthorized"}, 401

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    try:

        # Busca os modelos de documentos ativos da categoria informada.
        cursor.execute("""
            SELECT id_modelo_documento, titulo
            FROM modelo_documento
            WHERE ativo = 1 AND id_categoria = %s
            ORDER BY titulo ASC
        """, (category_id,))

        # Armazena os resultados.
        models = cursor.fetchall()

        # Retorna os modelos em formato de JSON (semiestruturado).
        return {"models": models}

    except Exception:

        # Retorna um código (HTTP) de erro.
        return {"error": "Erro ao buscar modelos da categoria..."}, 500

    finally:

        # Encerra a conexão com o banco de dados.
        cursor.close()
        connection.close()

# Rota para download de um documento preenchido.
@filled_document_blueprint.route('/download_filled_document/<int:filled_id>')
def download_filled_document(filled_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor(dictionary=True)

    # Consulta o documento preenchido com base no seu ID.
    cursor.execute("""
        SELECT m.titulo, d.arquivo
        FROM documento_preenchido AS d
        INNER JOIN modelo_documento AS m ON m.id_modelo_documento = d.id_documento_modelo
        WHERE d.id_documento_preenchido = %s AND d.ativo = 1
    """, (filled_id,))
    document = cursor.fetchone()

    # Encerra a conexão com o banco de dados.
    cursor.close()
    connection.close()

    # Verifica se o documento existe.
    if not document or not document['arquivo']:

        # Retorna uma mensagem de error.
        flash("Documento preenchido não encontrado...", "danger")
        return redirect(url_for('filled_document.list_filled_documents'))

    # Prepara o arquivo para download.
    return send_file(
        BytesIO(document['arquivo']),
        as_attachment=True,
        download_name=f"{document['titulo']}.pdf",
        mimetype='application/pdf'
    )

# Rota para exclusão lógica de um documento preenchido.
@filled_document_blueprint.route('/delete_filled_document/<int:filled_id>', methods=['POST'])
def delete_filled_document(filled_id):

    # Verifica se o usuário está logado.
    if 'user_id' not in session:

        # Retorna uma mensgem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Conecta ao banco de dados.
    connection = connect_to_database()
    cursor = connection.cursor()

    try:

        # Realiza a exclusão lógica.
        cursor.execute("UPDATE documento_preenchido SET ativo = 0 WHERE id_documento_preenchido = %s", (filled_id,))
        connection.commit()

        # Retorna uma mensagem de sucesso.
        flash("Documento preenchido excluído com sucesso!!!", "success")

    except Exception:

        # Desfaz as alterações no banco de dados.
        connection.rollback()

        # Retorna uma mensagem de erro.
        flash("Erro ao excluir o documento preenchido...", "danger")

    finally:

        # Encerra a conexão com o banco de dados.
        cursor.close()
        connection.close()

    # Redireciona o usuário para a tela de listagem de documentos preenchidos.
    return redirect(url_for('filled_document.list_filled_documents'))