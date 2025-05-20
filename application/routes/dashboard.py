# Importações dos módulos do Flask.
from flask import Blueprint
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for
from flask import flash

# Cria o blueprint do painel de gerenciamento.
dashboard_blueprint = Blueprint('dashboard', __name__)

# Rota principal da área administrativa.
@dashboard_blueprint.route('/dashboard')
def management_panel():

    # Verifica se o usuário está autenticado.
    if 'user_id' not in session:

        # Retorna uma mensagem de erro.
        flash("Faça login para prosseguir...", "danger")
        return redirect(url_for('authentication.login_user'))

    # Renderiza a tela do painel gerencial com os dados da sessão.
    return render_template('dashboard.html', name=session['user_name'], role=session['user_role'])