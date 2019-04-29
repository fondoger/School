from app import db, models
from app.models import *
from .generate_fake_users import generate_fake_users
from .generate_groups import generate_private_groups, generate_public_groups
from .generate_fake_activities import generate_fake_activities
from .generate_fake_statuses import generate_fake_statuses
from .generate_official_accounts import generate_official_accounts

def initialize_database():
    db.drop_all()
    db.create_all()


    generate_fake_users()
    generate_private_groups()
    generate_public_groups()
    generate_fake_statuses()
    generate_fake_activities()
    generate_official_accounts()
