"""Manual initial migration

Revision ID: 84ab844ee6fe
Revises: 
Create Date: 2026-01-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '84ab844ee6fe'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ticket table
    op.create_table('ticket',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='ticketstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 2. Create ticketattribute table
    op.create_table('ticketattribute',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('ticket_id', sa.Uuid(), nullable=False),
        sa.Column('key', sqlmodel.AutoString(), nullable=False),
        sa.Column('value', sqlmodel.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['ticket_id'], ['ticket.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket_id', 'key', name='ticketattribute_ticket_id_key_key')
    )
    op.create_index(op.f('ix_ticketattribute_key'), 'ticketattribute', ['key'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ticketattribute_key'), table_name='ticketattribute')
    op.drop_table('ticketattribute')
    op.drop_table('ticket')
    sa.Enum(name='ticketstatus').drop(op.get_bind())
