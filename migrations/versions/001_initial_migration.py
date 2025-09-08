from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pagos table
    op.create_table('pagos',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('id_afiliado', sa.String(length=255), nullable=False),
    sa.Column('monto', sa.Float(), nullable=False),
    sa.Column('moneda', sa.String(length=3), nullable=False),
    sa.Column('estado', sa.String(length=20), nullable=False),
    sa.Column('referencia_pago', sa.String(length=255), nullable=False),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
    sa.Column('fecha_actualizacion', sa.DateTime(), nullable=False),
    sa.Column('fecha_procesamiento', sa.DateTime(), nullable=True),
    sa.Column('mensaje_error', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('referencia_pago')
    )
    
    # Create outbox table
    op.create_table('outbox',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('tipo_evento', sa.String(length=100), nullable=False),
    sa.Column('datos_evento', sa.Text(), nullable=False),
    sa.Column('procesado', sa.Boolean(), nullable=False),
    sa.Column('fecha_creacion', sa.DateTime(), nullable=False),
    sa.Column('fecha_procesamiento', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('outbox')
    op.drop_table('pagos')
