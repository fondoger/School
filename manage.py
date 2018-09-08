from app import create_app, db
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from app.models import *
from app import models
import sys
import os

server_type = None
try:
    server_type = os.environ['flask_server_type']
except:
    server_type = 'default'

app = create_app(server_type)
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, models=models,
                User=User, Status=Status, Topic=Topic,
                Group=Group, GroupMembership=GroupMembership,
                Activity=Activity, OfficialAccount=OfficialAccount,)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
