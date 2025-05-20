# Importa o Flask para criar a aplicação da web.
from flask import Flask

# Função responsável por criar e configurar a aplicação em Flask.
def create_application():

    # Instancia do objeto da aplicação em Flask.
    web_application = Flask(__name__)

    # Define a chave secreta usada para proteger sessões e cookies.
    web_application.config['SECRET_KEY'] = '42ba728957e22d69175bdfa4d08c634c'

    # Importa o blueprint de autenticação de usuário.
    from application.routes.authentication import authentication_blueprint
    web_application.register_blueprint(authentication_blueprint)

    # Importa o blueprint do painel gerencial.
    from application.routes.dashboard import dashboard_blueprint
    web_application.register_blueprint(dashboard_blueprint)

    # Importa o blueprint de usuários.
    from application.routes.users import users_blueprint
    web_application.register_blueprint(users_blueprint)

    # Importa o blueprint de categorias de documentos.
    from application.routes.document_category import category_blueprint
    web_application.register_blueprint(category_blueprint)

    # Importa o blueprint de modelos de documentos.
    from application.routes.document_model import document_model_blueprint
    web_application.register_blueprint(document_model_blueprint)

    # Importa o blueprint de documentos preenchidos.
    from application.routes.filled_document import filled_document_blueprint
    web_application.register_blueprint(filled_document_blueprint)

    # Retorna o objeto da aplicação da web já configurado.
    return web_application