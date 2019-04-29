from app import db, models
from app.models import *
import json

with open("scripts/sync_official_accounts.json") as f:
    accounts = json.load(f)
    for account in accounts:
        a = OfficialAccount.query.filter_by(accountname=account['accountname']).one()
        a.page_url = account['page_url']
        db.session.add(a)
    db.session.commit()
