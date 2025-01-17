"""0001 Initial migration

Revision ID: c2287780f66c
Revises: 
Create Date: 2024-03-17 13:52:06.917914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2287780f66c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('roles',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('oauth_accounts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('oauth_name', sa.String(), nullable=False),
    sa.Column('access_token', sa.String(), nullable=False),
    sa.Column('expires_at', sa.Integer(), nullable=True),
    sa.Column('refresh_token', sa.String(), nullable=True),
    sa.Column('account_id', sa.String(), nullable=False),
    sa.Column('account_email', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'oauth_name')
    )
    op.create_index(op.f('ix_oauth_accounts_account_id'), 'oauth_accounts', ['account_id'], unique=False)
    op.create_index(op.f('ix_oauth_accounts_oauth_name'), 'oauth_accounts', ['oauth_name'], unique=False)
    op.create_table('user_role',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('role_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='cascade'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('visits',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('user_agent', sa.String(), nullable=False),
    sa.Column('device_type', sa.String(), nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id', 'device_type'),
    sa.UniqueConstraint('id', 'device_type'),
    postgresql_partition_by='LIST (device_type)'
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS "visits_smart" PARTITION OF "visits" FOR VALUES IN ('smart')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS "visits_mobile" PARTITION OF "visits" FOR VALUES IN ('mobile')
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS "visits_web" PARTITION OF "visits" FOR VALUES IN ('web')
    """)

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###

    op.execute("DROP TABLE IF EXISTS visits_smart")
    op.execute("DROP TABLE IF EXISTS visits_mobile")
    op.execute("DROP TABLE IF EXISTS visits_web")

    op.drop_table('visits')
    op.drop_table('user_role')
    op.drop_index(op.f('ix_oauth_accounts_oauth_name'), table_name='oauth_accounts')
    op.drop_index(op.f('ix_oauth_accounts_account_id'), table_name='oauth_accounts')
    op.drop_table('oauth_accounts')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
    # ### end Alembic commands ###
