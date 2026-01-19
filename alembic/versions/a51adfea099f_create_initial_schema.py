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

    # TRIGGER FUNCTION: Esta função automatiza o campo 'updated_at'.
    # Ela garante que a marca temporal de modificação seja atualizada pelo Banco de Dados,
    # independente se a alteração veio do código da aplicação ou de um comando SQL manual.
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
        # AUDITORIA: created_at e updated_at permitem rastrear o ciclo de vida do cliente.
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        # SOFT DELETE: deleted_at permite "excluir" o cliente da visão do usuário sem apagar os dados.
        # Isso é vital para manter a integridade de relatórios financeiros e históricos de anos anteriores.
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )

    # 3. Tabela: contracts
    op.create_table(
        'contracts',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('customer_id', sa.UUID(), sa.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        # SOFT DELETE: Usado aqui para que o encerramento de um contrato não quebre a relação
        # com as leituras de consumo já registradas.
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
    )

    # 4. Tabela: readings
    # NOTA DE DESIGN: Esta tabela NÃO possui updated_at ou deleted_at.
    # Leituras são "fatos imutáveis": uma vez que o medidor registrou um valor em uma data,
    # esse registro não muda. Se houver erro, insere-se uma nova leitura de correção.
    # A ausência dessas colunas economiza espaço em disco em tabelas que podem ter milhões de linhas.
    op.create_table(
        'readings',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('contract_id', sa.UUID(), sa.ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ref_date', sa.Date(), nullable=False),
        sa.Column('reading_kwh', sa.Numeric(12, 4), nullable=False),
        # CONSTRAINT: Regra de negócio no banco para impedir erros de inserção de consumo negativo.
        sa.CheckConstraint('reading_kwh >= 0', name='check_positive_kwh')
    )

    # 5. Triggers de Auditoria
    # Vincula a função de trigger às tabelas de cadastro que permitem edição.
    for table in ['customers', 'contracts']:
        op.execute(
            f"CREATE TRIGGER trg_update_{table}_at BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();")

    # 6. Segurança: Roles, RLS e Least Privilege (Menor Privilégio)
    # ROLE: Criamos um usuário específico para o n8n. Ele não tem acesso a outras tabelas do sistema.
    op.execute("CREATE ROLE n8n_api_user WITH LOGIN PASSWORD 'n8n_secure_pass';")

    for table in ['customers', 'contracts', 'readings']:
        # ROW LEVEL SECURITY (RLS): Ativa o isolamento de dados no nível do Banco de Dados.
        # Isso garante segurança mesmo que a query do n8n venha sem filtros adequados.
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"GRANT SELECT, INSERT ON {table} TO n8n_api_user;")

    # POLÍTICA 1: O n8n só consegue "enxergar" contratos que NÃO foram marcados como deletados.
    # O filtro 'deleted_at IS NULL' é injetado automaticamente em qualquer SELECT feito por esse usuário.
    op.execute("""
        CREATE POLICY n8n_filter_active_data ON contracts
        FOR SELECT TO n8n_api_user
        USING (deleted_at IS NULL);
    """)

    # POLÍTICA 2: Segurança Hierárquica. O usuário só vê as leituras (readings) cujos contratos
    # pai passaram no filtro da POLÍTICA 1. Se o contrato está oculto, suas leituras também estão.
    op.execute("""
        CREATE POLICY n8n_filter_readings ON readings
        FOR SELECT TO n8n_api_user
        USING (contract_id IN (SELECT id FROM contracts));
    """)


def downgrade() -> None:
    # DOWNGRADE: Ordem reversa de remoção para evitar erros de dependência (Foreign Keys).
    op.execute('DROP POLICY IF EXISTS n8n_filter_readings ON readings')
    op.execute('DROP POLICY IF EXISTS n8n_filter_active_data ON contracts')

    op.execute('REVOKE ALL PRIVILEGES ON TABLE readings FROM n8n_api_user')
    op.execute('REVOKE ALL PRIVILEGES ON TABLE contracts FROM n8n_api_user')
    op.execute('REVOKE ALL PRIVILEGES ON TABLE customers FROM n8n_api_user')

    op.execute("DROP ROLE IF EXISTS n8n_api_user;")
    op.drop_table('readings')
    op.drop_table('contracts')
    op.drop_table('customers')
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
