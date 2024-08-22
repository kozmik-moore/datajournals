"""Update gamingdb interruption models

Revision ID: af0f1eb2d74e
Revises: 8980095e9428
Create Date: 2023-12-14 12:50:20.038850

"""

from datajournals import db
from datajournals.models import GamingSessionInterruption, GamingInterruptionTag

# revision identifiers, used by Alembic.
revision = 'af0f1eb2d74e'
down_revision = '8980095e9428'
branch_labels = None
depends_on = None


def upgrade():
    ip = db.session.query(GamingSessionInterruption).all()
    for i in ip:
        i.tags.append(db.session.query(GamingInterruptionTag).filter_by(id=i.tag_id).first())
        db.session.add(i)
    db.session.commit()


def downgrade():
    pass
