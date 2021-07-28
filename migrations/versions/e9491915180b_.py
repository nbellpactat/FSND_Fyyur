"""empty message

Revision ID: e9491915180b
Revises: a1a849b13f89
Create Date: 2021-07-28 13:09:00.289254

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e9491915180b'
down_revision = 'a1a849b13f89'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Show')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Show',
    sa.Column('id', sa.INTEGER(), server_default=sa.text('nextval(\'"Show_id_seq"\'::regclass)'), autoincrement=True, nullable=False),
    sa.Column('artist_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('venue_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('start_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='Show_pkey')
    )
    # ### end Alembic commands ###
