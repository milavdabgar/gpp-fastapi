"""Add feedback analysis model

Revision ID: 84dc168a62c7
Revises: 
Create Date: 2025-05-05 22:23:52.171526

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '84dc168a62c7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('feedback_analysis',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('term', sa.String(length=20), nullable=False),
    sa.Column('branch', sa.String(length=50), nullable=False),
    sa.Column('semester', sa.Integer(), nullable=False),
    sa.Column('term_start', sa.DateTime(), nullable=True),
    sa.Column('term_end', sa.DateTime(), nullable=True),
    sa.Column('subject_code', sa.String(length=20), nullable=False),
    sa.Column('subject_name', sa.String(length=200), nullable=False),
    sa.Column('faculty_name', sa.String(length=100), nullable=False),
    sa.Column('q1_score', sa.Float(), nullable=False),
    sa.Column('q2_score', sa.Float(), nullable=False),
    sa.Column('q3_score', sa.Float(), nullable=False),
    sa.Column('q4_score', sa.Float(), nullable=False),
    sa.Column('q5_score', sa.Float(), nullable=False),
    sa.Column('q6_score', sa.Float(), nullable=False),
    sa.Column('q7_score', sa.Float(), nullable=False),
    sa.Column('q8_score', sa.Float(), nullable=False),
    sa.Column('q9_score', sa.Float(), nullable=False),
    sa.Column('q10_score', sa.Float(), nullable=False),
    sa.Column('q11_score', sa.Float(), nullable=False),
    sa.Column('q12_score', sa.Float(), nullable=False),
    sa.Column('total_responses', sa.Integer(), nullable=False),
    sa.Column('average_score', sa.Float(), nullable=False),
    sa.Column('report_data', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_index('flyway_schema_history_s_idx', table_name='flyway_schema_history')
    op.drop_table('flyway_schema_history')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('flyway_schema_history',
    sa.Column('installed_rank', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('version', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(length=200), autoincrement=False, nullable=False),
    sa.Column('type', sa.VARCHAR(length=20), autoincrement=False, nullable=False),
    sa.Column('script', sa.VARCHAR(length=1000), autoincrement=False, nullable=False),
    sa.Column('checksum', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('installed_by', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('installed_on', postgresql.TIMESTAMP(), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('execution_time', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('success', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('installed_rank', name='flyway_schema_history_pk')
    )
    op.create_index('flyway_schema_history_s_idx', 'flyway_schema_history', ['success'], unique=False)
    op.drop_table('feedback_analysis')
    # ### end Alembic commands ###
