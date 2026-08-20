from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Created empty here and attached to the app inside the factory.
# This avoids circular imports between the models and the app.
db = SQLAlchemy()
migrate = Migrate()