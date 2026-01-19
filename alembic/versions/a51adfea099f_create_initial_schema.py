"""create_initial_schema

Revision ID: a51adfea099f
Revises: 
Create Date: 2026-01-16 13:10:02.350291

"""
from alembic import op
import sqlalchemy as sa

revision = 'a51adfea099f'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Extensões e Funções Globais (Auditoria)
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute("""
               CREATE
               OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
               BEGIN
            NEW.updated_at
               = CURRENT_TIMESTAMP;
               RETURN NEW;
               END;
        $$
               language 'plpgsql';
               """)

    # 2. Tabela: customers
    op.create_table(
        'customers',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)  # Soft Delete
    )

    # 3. Tabela: contracts
    op.create_table(
        'contracts',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('customer_id', sa.UUID(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )

    # 4. Tabela: readings
    op.create_table(
        'readings',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('contract_id', sa.UUID(), sa.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ref_date', sa.Date(), nullable=False),
        sa.Column('reading_kwh', sa.Numeric(12, 4), nullable=False),
        sa.CheckConstraint('reading_kwh >= 0', name='check_positive_kwh')  # Check Constraint
    )

    # 5. Triggers de Auditoria
    for table in ['customers', 'contracts']:
        op.execute(
            f"CREATE TRIGGER trg_update_{table}_at BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();")

    # 6. Segurança: Roles, RLS e Least Privilege
    # Nota: Senha deve ser gerenciada via variável de ambiente em produção
    op.execute("CREATE ROLE n8n_api_user WITH LOGIN PASSWORD 'n8n_secure_pass';")

    for table in ['customers', 'contracts', 'readings']:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"GRANT SELECT, INSERT, READ ON {table} TO n8n_api_user;")

    # Política RLS: Impedir que o n8n veja dados "deletados" ou contratos inativos
    op.execute("""
        CREATE POLICY n8n_filter_active_data ON contracts
        FOR SELECT TO n8n_api_user
        USING (deleted_at IS NULL);
    """)

    # Política RLS para Leituras: Só vê leituras de contratos que passaram na política acima
    op.execute("""
        CREATE POLICY n8n_filter_readings ON readings
        FOR SELECT TO n8n_api_user
        USING (contract_id IN (SELECT id FROM contracts));
    """)


def downgrade() -> None:
    # 1. Remover as Políticas de Segurança (RLS) primeiro
    op.execute('DROP POLICY IF EXISTS n8n_filter_readings ON readings')
    op.execute('DROP POLICY IF EXISTS n8n_filter_active_data ON contracts')

    # 2. Revogar as permissões explicitamente
    op.execute('REVOKE ALL PRIVILEGES ON TABLE readings FROM n8n_api_user')
    op.execute('REVOKE ALL PRIVILEGES ON TABLE contracts FROM n8n_api_user')
    op.execute('REVOKE ALL PRIVILEGES ON TABLE customers FROM n8n_api_user')

    # Ordem reversa para evitar erro de Foreign Key
    op.execute("DROP ROLE IF EXISTS n8n_api_user;")
    op.drop_table('readings')
    op.drop_table('contracts')
    op.drop_table('customers')
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
