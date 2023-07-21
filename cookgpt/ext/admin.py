from flask_admin import Admin
from flask_admin.base import AdminIndexView
from flask_admin.contrib import sqla

from cookgpt.ext.database import db
from cookgpt.user.models import User

# Proteck admin with login / Monkey Patch
AdminIndexView._handle_view = AdminIndexView._handle_view
sqla.ModelView._handle_view = sqla.ModelView._handle_view
admin = Admin()


def init_app(app):
    admin.name = app.config.TITLE
    admin.template_mode = app.config.FLASK_ADMIN_TEMPLATE_MODE
    admin.init_app(app)

    # Add admin page for User
    admin.add_view(sqla.ModelView(User, db.session, name="admin_user"))
