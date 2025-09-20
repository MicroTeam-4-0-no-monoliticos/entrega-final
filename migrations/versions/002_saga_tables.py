"""Add SAGA tables

Revision ID: 002_saga_tables
Revises: 001_initial_migration
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_saga_tables'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla saga_log
    op.create_table('saga_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tipo', sa.String(length=100), nullable=False),
        sa.Column('estado', sa.String(length=50), nullable=False),
        sa.Column('pasos', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('compensaciones', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('datos_iniciales', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('fecha_inicio', sa.DateTime(), nullable=False),
        sa.Column('fecha_fin', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('timeout_minutos', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear tabla saga_pasos
    op.create_table('saga_pasos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('saga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tipo_paso', sa.String(length=100), nullable=False),
        sa.Column('datos', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('resultado', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('compensacion', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('exitoso', sa.Boolean(), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('fecha_ejecucion', sa.DateTime(), nullable=False),
        sa.Column('fecha_fin', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear tabla saga_compensaciones
    op.create_table('saga_compensaciones',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('saga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('paso_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tipo_compensacion', sa.String(length=100), nullable=False),
        sa.Column('datos', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('resultado', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('exitoso', sa.Boolean(), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('fecha_ejecucion', sa.DateTime(), nullable=False),
        sa.Column('fecha_fin', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear tabla saga_events
    op.create_table('saga_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('saga_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evento_tipo', sa.String(length=100), nullable=False),
        sa.Column('evento_datos', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('topic', sa.String(length=200), nullable=False),
        sa.Column('procesado', sa.Boolean(), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
        sa.Column('fecha_procesamiento', sa.DateTime(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('reintentos', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear índices para mejorar performance
    op.create_index('ix_saga_log_estado', 'saga_log', ['estado'])
    op.create_index('ix_saga_log_tipo', 'saga_log', ['tipo'])
    op.create_index('ix_saga_log_fecha_inicio', 'saga_log', ['fecha_inicio'])
    op.create_index('ix_saga_pasos_saga_id', 'saga_pasos', ['saga_id'])
    op.create_index('ix_saga_compensaciones_saga_id', 'saga_compensaciones', ['saga_id'])
    op.create_index('ix_saga_events_saga_id', 'saga_events', ['saga_id'])
    op.create_index('ix_saga_events_procesado', 'saga_events', ['procesado'])


def downgrade():
    # Eliminar índices
    op.drop_index('ix_saga_events_procesado', table_name='saga_events')
    op.drop_index('ix_saga_events_saga_id', table_name='saga_events')
    op.drop_index('ix_saga_compensaciones_saga_id', table_name='saga_compensaciones')
    op.drop_index('ix_saga_pasos_saga_id', table_name='saga_pasos')
    op.drop_index('ix_saga_log_fecha_inicio', table_name='saga_log')
    op.drop_index('ix_saga_log_tipo', table_name='saga_log')
    op.drop_index('ix_saga_log_estado', table_name='saga_log')
    
    # Eliminar tablas
    op.drop_table('saga_events')
    op.drop_table('saga_compensaciones')
    op.drop_table('saga_pasos')
    op.drop_table('saga_log')
