"""Add file storage tables (migrated from file-based to database)

Revision ID: 001_file_storage
Revises: 
Create Date: 2025-02-02 20:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_file_storage'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Policy Workspace Tables
    op.create_table(
        'policy_assumptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assumption_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('range_json', postgresql.JSONB(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_policy_assumptions_tenant_id', 'policy_assumptions', ['tenant_id'])
    op.create_index('ix_policy_assumptions_policy_id', 'policy_assumptions', ['policy_id'])
    op.create_index('ix_policy_assumptions_tenant_policy', 'policy_assumptions', ['tenant_id', 'policy_id'])
    op.create_index('ix_policy_assumptions_type', 'policy_assumptions', ['assumption_type'])
    op.create_index('ix_policy_assumptions_created_at', 'policy_assumptions', ['created_at'])
    
    op.create_table(
        'policy_guardrails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('threshold_type', sa.String(), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('action', sa.String(), nullable=False, server_default='alert'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('triggered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_policy_guardrails_tenant_id', 'policy_guardrails', ['tenant_id'])
    op.create_index('ix_policy_guardrails_policy_id', 'policy_guardrails', ['policy_id'])
    op.create_index('ix_policy_guardrails_tenant_policy', 'policy_guardrails', ['tenant_id', 'policy_id'])
    op.create_index('ix_policy_guardrails_metric', 'policy_guardrails', ['metric_name'])
    op.create_index('ix_policy_guardrails_triggered', 'policy_guardrails', ['triggered'])
    op.create_index('ix_policy_guardrails_last_checked_at', 'policy_guardrails', ['last_checked_at'])
    op.create_index('ix_policy_guardrails_created_at', 'policy_guardrails', ['created_at'])
    
    op.create_table(
        'policy_changelog',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entry_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changed_at', sa.DateTime(), nullable=False),
        sa.Column('changes_json', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_policy_changelog_tenant_id', 'policy_changelog', ['tenant_id'])
    op.create_index('ix_policy_changelog_policy_id', 'policy_changelog', ['policy_id'])
    op.create_index('ix_policy_changelog_tenant_policy', 'policy_changelog', ['tenant_id', 'policy_id'])
    op.create_index('ix_policy_changelog_type', 'policy_changelog', ['entry_type'])
    op.create_index('ix_policy_changelog_changed_by', 'policy_changelog', ['changed_by'])
    op.create_index('ix_policy_changelog_changed_at', 'policy_changelog', ['changed_at'])
    
    # Analytics Tables
    op.create_table(
        'policy_predicted_impacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metrics_json', postgresql.JSONB(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('predicted_at', sa.DateTime(), nullable=False),
        sa.Column('prediction_method', sa.String(), nullable=True),
        sa.Column('baseline_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('data_period_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'policy_id', 'predicted_at', name='uq_predicted_impact_tenant_policy_date'),
    )
    op.create_index('ix_predicted_impact_tenant_policy', 'policy_predicted_impacts', ['tenant_id', 'policy_id'])
    op.create_index('ix_predicted_impact_predicted_at', 'policy_predicted_impacts', ['predicted_at'])
    op.create_index('ix_predicted_impact_baseline_id', 'policy_predicted_impacts', ['baseline_id'])
    op.create_index('ix_predicted_impact_data_period_id', 'policy_predicted_impacts', ['data_period_id'])
    op.create_index('ix_predicted_impact_created_at', 'policy_predicted_impacts', ['created_at'])
    # Add foreign key for baseline_id after baselines table is created
    # op.create_foreign_key('fk_predicted_impact_baseline', 'policy_predicted_impacts', 'baselines', ['baseline_id'], ['id'], ondelete='SET NULL')
    
    op.create_table(
        'baselines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('baseline_id', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('baseline_type', sa.String(), nullable=False),
        sa.Column('window_start_date', sa.DateTime(), nullable=False),
        sa.Column('window_end_date', sa.DateTime(), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parent_baseline_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('data_period_ids_json', postgresql.JSONB(), nullable=True),
        sa.Column('baseline_metrics_json', postgresql.JSONB(), nullable=False),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('computed_by', sa.String(), nullable=True),
        sa.Column('shift_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shift_summary_json', postgresql.JSONB(), nullable=True),
        sa.Column('refresh_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('baseline_id', name='uq_baselines_baseline_id'),
    )
    op.create_index('ix_baselines_tenant_id', 'baselines', ['tenant_id'])
    op.create_index('ix_baselines_baseline_id', 'baselines', ['baseline_id'])
    op.create_index('ix_baselines_tenant_policy', 'baselines', ['tenant_id', 'policy_id'])
    op.create_index('ix_baselines_type', 'baselines', ['baseline_type'])
    op.create_index('ix_baselines_window', 'baselines', ['window_start_date', 'window_end_date'])
    op.create_index('ix_baselines_shift_detected', 'baselines', ['shift_detected'])
    op.create_index('ix_baselines_computed_at', 'baselines', ['computed_at'])
    op.create_index('ix_baselines_created_at', 'baselines', ['created_at'])
    op.create_foreign_key('fk_baselines_parent', 'baselines', 'baselines', ['parent_baseline_id'], ['id'], ondelete='SET NULL')
    
    # Now add foreign key for predicted_impact.baseline_id
    op.create_foreign_key('fk_predicted_impact_baseline', 'policy_predicted_impacts', 'baselines', ['baseline_id'], ['id'], ondelete='SET NULL')
    
    op.create_table(
        'observations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('observation_id', sa.String(), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('policy_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('baseline_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('data_period_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('data_period_ids_json', postgresql.JSONB(), nullable=True),
        sa.Column('observation_type', sa.String(), nullable=False),
        sa.Column('observation_period_start', sa.DateTime(), nullable=False),
        sa.Column('observation_period_end', sa.DateTime(), nullable=False),
        sa.Column('metrics_json', postgresql.JSONB(), nullable=False),
        sa.Column('comparisons_json', postgresql.JSONB(), nullable=True),
        sa.Column('behavioral_explanation_json', postgresql.JSONB(), nullable=True),
        sa.Column('computed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['baseline_version_id'], ['baselines.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['prediction_id'], ['policy_predicted_impacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('observation_id', name='uq_observations_observation_id'),
    )
    op.create_index('ix_observations_tenant_id', 'observations', ['tenant_id'])
    op.create_index('ix_observations_observation_id', 'observations', ['observation_id'])
    op.create_index('ix_observations_tenant_policy', 'observations', ['tenant_id', 'policy_id'])
    op.create_index('ix_observations_period', 'observations', ['observation_period_start', 'observation_period_end'])
    op.create_index('ix_observations_type', 'observations', ['observation_type'])
    op.create_index('ix_observations_computed_at', 'observations', ['computed_at'])
    op.create_index('ix_observations_created_at', 'observations', ['created_at'])
    
    # Scenario Tables
    op.create_table(
        'scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assumptions_json', postgresql.JSONB(), nullable=False),
        sa.Column('results_json', postgresql.JSONB(), nullable=True),
        sa.Column('scenario_type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('scenario_id', name='uq_scenarios_scenario_id'),
    )
    op.create_index('ix_scenarios_tenant_id', 'scenarios', ['tenant_id'])
    op.create_index('ix_scenarios_scenario_id', 'scenarios', ['scenario_id'])
    op.create_index('ix_scenarios_tenant_policy', 'scenarios', ['tenant_id', 'policy_id'])
    op.create_index('ix_scenarios_name', 'scenarios', ['name'])
    op.create_index('ix_scenarios_status', 'scenarios', ['status'])
    op.create_index('ix_scenarios_created_at', 'scenarios', ['created_at'])
    
    op.create_table(
        'scenario_accuracy',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actual_vs_predicted_json', postgresql.JSONB(), nullable=False),
        sa.Column('metrics_json', postgresql.JSONB(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(), nullable=False),
        sa.Column('evaluation_period_start', sa.DateTime(), nullable=True),
        sa.Column('evaluation_period_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_scenario_accuracy_tenant_id', 'scenario_accuracy', ['tenant_id'])
    op.create_index('ix_scenario_accuracy_scenario_id', 'scenario_accuracy', ['scenario_id'])
    op.create_index('ix_scenario_accuracy_tenant_scenario', 'scenario_accuracy', ['tenant_id', 'scenario_id'])
    op.create_index('ix_scenario_accuracy_evaluated_at', 'scenario_accuracy', ['evaluated_at'])
    
    # Pipeline Tables
    op.create_table(
        'pipelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pipeline_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('steps_json', postgresql.JSONB(), nullable=False),
        sa.Column('schedule_json', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('pipeline_type', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('pipeline_id', name='uq_pipelines_pipeline_id'),
    )
    op.create_index('ix_pipelines_tenant_id', 'pipelines', ['tenant_id'])
    op.create_index('ix_pipelines_pipeline_id', 'pipelines', ['pipeline_id'])
    op.create_index('ix_pipelines_tenant_name', 'pipelines', ['tenant_id', 'name'])
    op.create_index('ix_pipelines_status', 'pipelines', ['status'])
    op.create_index('ix_pipelines_enabled', 'pipelines', ['enabled'])
    op.create_index('ix_pipelines_created_at', 'pipelines', ['created_at'])
    
    op.create_table(
        'pipeline_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pipeline_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('logs_uri', sa.String(), nullable=True),
        sa.Column('metrics_json', postgresql.JSONB(), nullable=True),
        sa.Column('error_details_json', postgresql.JSONB(), nullable=True),
        sa.Column('triggered_by', sa.String(), nullable=True),
        sa.Column('triggered_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('run_id', name='uq_pipeline_runs_run_id'),
    )
    op.create_index('ix_pipeline_runs_tenant_id', 'pipeline_runs', ['tenant_id'])
    op.create_index('ix_pipeline_runs_pipeline_id', 'pipeline_runs', ['pipeline_id'])
    op.create_index('ix_pipeline_runs_run_id', 'pipeline_runs', ['run_id'])
    op.create_index('ix_pipeline_runs_tenant_pipeline', 'pipeline_runs', ['tenant_id', 'pipeline_id'])
    op.create_index('ix_pipeline_runs_status', 'pipeline_runs', ['status'])
    op.create_index('ix_pipeline_runs_started_at', 'pipeline_runs', ['started_at'])
    op.create_index('ix_pipeline_runs_created_at', 'pipeline_runs', ['created_at'])
    
    # Risk Table
    op.create_table(
        'risks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_id', sa.String(), nullable=False),
        sa.Column('risk_driver', sa.String(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('impact', sa.String(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mitigation_json', postgresql.JSONB(), nullable=True),
        sa.Column('impact_details_json', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='OPEN'),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('mitigated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('risk_id', name='uq_risks_risk_id'),
    )
    op.create_index('ix_risks_tenant_id', 'risks', ['tenant_id'])
    op.create_index('ix_risks_policy_id', 'risks', ['policy_id'])
    op.create_index('ix_risks_risk_id', 'risks', ['risk_id'])
    op.create_index('ix_risks_tenant_policy', 'risks', ['tenant_id', 'policy_id'])
    op.create_index('ix_risks_driver', 'risks', ['risk_driver'])
    op.create_index('ix_risks_status', 'risks', ['status'])
    op.create_index('ix_risks_created_at', 'risks', ['created_at'])
    
    # Forecast Table
    op.create_table(
        'forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('forecast_id', sa.String(), nullable=False),
        sa.Column('projections_json', postgresql.JSONB(), nullable=False),
        sa.Column('confidence_intervals_json', postgresql.JSONB(), nullable=True),
        sa.Column('forecast_date', sa.DateTime(), nullable=False),
        sa.Column('forecast_horizon', sa.String(), nullable=True),
        sa.Column('forecast_method', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('forecast_id', name='uq_forecasts_forecast_id'),
    )
    op.create_index('ix_forecasts_tenant_id', 'forecasts', ['tenant_id'])
    op.create_index('ix_forecasts_forecast_id', 'forecasts', ['forecast_id'])
    op.create_index('ix_forecasts_tenant_policy', 'forecasts', ['tenant_id', 'policy_id'])
    op.create_index('ix_forecasts_forecast_date', 'forecasts', ['forecast_date'])
    op.create_index('ix_forecasts_created_at', 'forecasts', ['created_at'])
    
    # Data Period Table
    op.create_table(
        'data_periods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('period_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('period_start_date', sa.DateTime(), nullable=False),
        sa.Column('period_end_date', sa.DateTime(), nullable=False),
        sa.Column('data_snapshot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['data_snapshot_id'], ['dataset_snapshots.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'period_id', name='uq_data_period_tenant_period'),
    )
    op.create_index('ix_data_periods_tenant_id', 'data_periods', ['tenant_id'])
    op.create_index('ix_data_periods_period_id', 'data_periods', ['period_id'])
    op.create_index('ix_data_periods_period', 'data_periods', ['period_start_date', 'period_end_date'])
    op.create_index('ix_data_periods_created_at', 'data_periods', ['created_at'])
    
    # Learning Tables
    op.create_table(
        'elasticity_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.Column('model_type', sa.String(), nullable=False),
        sa.Column('parameters_json', postgresql.JSONB(), nullable=False),
        sa.Column('accuracy_metrics_json', postgresql.JSONB(), nullable=True),
        sa.Column('trained_at', sa.DateTime(), nullable=False),
        sa.Column('training_data_period_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model_version', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('model_id', name='uq_elasticity_models_model_id'),
    )
    op.create_index('ix_elasticity_models_tenant_id', 'elasticity_models', ['tenant_id'])
    op.create_index('ix_elasticity_models_model_id', 'elasticity_models', ['model_id'])
    op.create_index('ix_elasticity_models_tenant_policy', 'elasticity_models', ['tenant_id', 'policy_id'])
    op.create_index('ix_elasticity_models_type', 'elasticity_models', ['model_type'])
    op.create_index('ix_elasticity_models_status', 'elasticity_models', ['status'])
    op.create_index('ix_elasticity_models_trained_at', 'elasticity_models', ['trained_at'])
    op.create_index('ix_elasticity_models_created_at', 'elasticity_models', ['created_at'])
    
    op.create_table(
        'model_accuracy_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metrics_json', postgresql.JSONB(), nullable=False),
        sa.Column('evaluation_date', sa.DateTime(), nullable=False),
        sa.Column('evaluation_data_period_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['elasticity_models.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_model_accuracy_tenant_id', 'model_accuracy_history', ['tenant_id'])
    op.create_index('ix_model_accuracy_model_id', 'model_accuracy_history', ['model_id'])
    op.create_index('ix_model_accuracy_tenant_model', 'model_accuracy_history', ['tenant_id', 'model_id'])
    op.create_index('ix_model_accuracy_evaluation_date', 'model_accuracy_history', ['evaluation_date'])
    
    # Behavior Tables (clusters first, then profiles with FK)
    op.create_table(
        'behavior_clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cluster_id', sa.String(), nullable=False),
        sa.Column('cluster_type', sa.String(), nullable=False),
        sa.Column('members_json', postgresql.JSONB(), nullable=False),
        sa.Column('characteristics_json', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('cluster_id', name='uq_behavior_clusters_cluster_id'),
    )
    op.create_index('ix_behavior_clusters_tenant_id', 'behavior_clusters', ['tenant_id'])
    op.create_index('ix_behavior_clusters_cluster_id', 'behavior_clusters', ['cluster_id'])
    op.create_index('ix_behavior_clusters_tenant_type', 'behavior_clusters', ['tenant_id', 'cluster_type'])
    op.create_index('ix_behavior_clusters_created_at', 'behavior_clusters', ['created_at'])
    
    op.create_table(
        'behavior_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('behavior_type', sa.String(), nullable=False),
        sa.Column('member_id', sa.String(), nullable=True),
        sa.Column('provider_id', sa.String(), nullable=True),
        sa.Column('signals_json', postgresql.JSONB(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('confidence', sa.String(), nullable=True),
        sa.Column('cluster_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['cluster_id'], ['behavior_clusters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('profile_id', name='uq_behavior_profiles_profile_id'),
    )
    op.create_index('ix_behavior_profiles_tenant_id', 'behavior_profiles', ['tenant_id'])
    op.create_index('ix_behavior_profiles_profile_id', 'behavior_profiles', ['profile_id'])
    op.create_index('ix_behavior_profiles_tenant_member', 'behavior_profiles', ['tenant_id', 'member_id'])
    op.create_index('ix_behavior_profiles_tenant_provider', 'behavior_profiles', ['tenant_id', 'provider_id'])
    op.create_index('ix_behavior_profiles_type', 'behavior_profiles', ['behavior_type'])
    op.create_index('ix_behavior_profiles_detected_at', 'behavior_profiles', ['detected_at'])
    op.create_index('ix_behavior_profiles_created_at', 'behavior_profiles', ['created_at'])
    
    # Alert Tables
    op.create_table(
        'alert_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('condition_json', postgresql.JSONB(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('action_config_json', postgresql.JSONB(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('rule_id', name='uq_alert_rules_rule_id'),
    )
    op.create_index('ix_alert_rules_tenant_id', 'alert_rules', ['tenant_id'])
    op.create_index('ix_alert_rules_rule_id', 'alert_rules', ['rule_id'])
    op.create_index('ix_alert_rules_tenant', 'alert_rules', ['tenant_id'])
    op.create_index('ix_alert_rules_enabled', 'alert_rules', ['enabled'])
    op.create_index('ix_alert_rules_created_at', 'alert_rules', ['created_at'])
    
    op.create_table(
        'alert_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('details_json', postgresql.JSONB(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['alert_rules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('event_id', name='uq_alert_events_event_id'),
    )
    op.create_index('ix_alert_events_tenant_id', 'alert_events', ['tenant_id'])
    op.create_index('ix_alert_events_rule_id', 'alert_events', ['rule_id'])
    op.create_index('ix_alert_events_event_id', 'alert_events', ['event_id'])
    op.create_index('ix_alert_events_tenant_rule', 'alert_events', ['tenant_id', 'rule_id'])
    op.create_index('ix_alert_events_policy', 'alert_events', ['policy_id'])
    op.create_index('ix_alert_events_severity', 'alert_events', ['severity'])
    op.create_index('ix_alert_events_triggered_at', 'alert_events', ['triggered_at'])
    op.create_index('ix_alert_events_resolved', 'alert_events', ['resolved_at'])
    op.create_index('ix_alert_events_created_at', 'alert_events', ['created_at'])
    
    # Collaboration Tables
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_comments_tenant_id', 'comments', ['tenant_id'])
    op.create_index('ix_comments_user', 'comments', ['user_id'])
    op.create_index('ix_comments_tenant_resource', 'comments', ['tenant_id', 'resource_type', 'resource_id'])
    op.create_index('ix_comments_created_at', 'comments', ['created_at'])
    
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assigned_to_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='OPEN'),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_tasks_tenant_id', 'tasks', ['tenant_id'])
    op.create_index('ix_tasks_assigned_to', 'tasks', ['assigned_to_user_id'])
    op.create_index('ix_tasks_tenant_resource', 'tasks', ['tenant_id', 'resource_type', 'resource_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('ix_tasks_created_at', 'tasks', ['created_at'])
    
    op.create_table(
        'approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('requested_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_approvals_tenant_id', 'approvals', ['tenant_id'])
    op.create_index('ix_approvals_requested_by', 'approvals', ['requested_by_user_id'])
    op.create_index('ix_approvals_approved_by', 'approvals', ['approved_by_user_id'])
    op.create_index('ix_approvals_tenant_resource', 'approvals', ['tenant_id', 'resource_type', 'resource_id'])
    op.create_index('ix_approvals_status', 'approvals', ['status'])
    op.create_index('ix_approvals_requested_at', 'approvals', ['requested_at'])
    op.create_index('ix_approvals_approved_at', 'approvals', ['approved_at'])
    
    op.create_table(
        'activity_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('details_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_activity_events_tenant_id', 'activity_events', ['tenant_id'])
    op.create_index('ix_activity_events_user', 'activity_events', ['user_id'])
    op.create_index('ix_activity_events_tenant_resource', 'activity_events', ['tenant_id', 'resource_type', 'resource_id'])
    op.create_index('ix_activity_events_action', 'activity_events', ['action'])
    op.create_index('ix_activity_events_created_at', 'activity_events', ['created_at'])
    
    # Evidence Table
    op.create_table(
        'evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('evidence_id', sa.String(), nullable=False),
        sa.Column('evidence_type', sa.String(), nullable=False),
        sa.Column('uri', sa.String(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('evidence_id', name='uq_evidence_evidence_id'),
    )
    op.create_index('ix_evidence_tenant_id', 'evidence', ['tenant_id'])
    op.create_index('ix_evidence_evidence_id', 'evidence', ['evidence_id'])
    op.create_index('ix_evidence_tenant_resource', 'evidence', ['tenant_id', 'resource_type', 'resource_id'])
    op.create_index('ix_evidence_type', 'evidence', ['evidence_type'])
    op.create_index('ix_evidence_created_at', 'evidence', ['created_at'])
    
    # Schedule Table
    op.create_table(
        'schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schedule_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('schedule_type', sa.String(), nullable=False),
        sa.Column('cron_expression', sa.String(), nullable=True),
        sa.Column('interval_seconds', sa.Integer(), nullable=True),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('schedule_id', name='uq_schedules_schedule_id'),
    )
    op.create_index('ix_schedules_tenant_id', 'schedules', ['tenant_id'])
    op.create_index('ix_schedules_schedule_id', 'schedules', ['schedule_id'])
    op.create_index('ix_schedules_tenant', 'schedules', ['tenant_id'])
    op.create_index('ix_schedules_enabled', 'schedules', ['enabled'])
    op.create_index('ix_schedules_next_run', 'schedules', ['next_run_at'])
    op.create_index('ix_schedules_created_at', 'schedules', ['created_at'])
    
    # Export Template Tables
    op.create_table(
        'export_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(), nullable=False),
        sa.Column('configuration_json', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('template_id', name='uq_export_templates_template_id'),
    )
    op.create_index('ix_export_templates_tenant_id', 'export_templates', ['tenant_id'])
    op.create_index('ix_export_templates_template_id', 'export_templates', ['template_id'])
    op.create_index('ix_export_templates_tenant', 'export_templates', ['tenant_id'])
    op.create_index('ix_export_templates_type', 'export_templates', ['template_type'])
    op.create_index('ix_export_templates_created_at', 'export_templates', ['created_at'])
    
    op.create_table(
        'export_packs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('pack_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('exports_json', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('pack_id', name='uq_export_packs_pack_id'),
    )
    op.create_index('ix_export_packs_tenant_id', 'export_packs', ['tenant_id'])
    op.create_index('ix_export_packs_pack_id', 'export_packs', ['pack_id'])
    op.create_index('ix_export_packs_created_at', 'export_packs', ['created_at'])


def downgrade():
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('export_packs')
    op.drop_table('export_templates')
    op.drop_table('schedules')
    op.drop_table('evidence')
    op.drop_table('activity_events')
    op.drop_table('approvals')
    op.drop_table('tasks')
    op.drop_table('comments')
    op.drop_table('alert_events')
    op.drop_table('alert_rules')
    op.drop_table('behavior_profiles')
    op.drop_table('behavior_clusters')
    op.drop_table('model_accuracy_history')
    op.drop_table('elasticity_models')
    op.drop_table('data_periods')
    op.drop_table('forecasts')
    op.drop_table('risks')
    op.drop_table('pipeline_runs')
    op.drop_table('pipelines')
    op.drop_table('scenario_accuracy')
    op.drop_table('scenarios')
    op.drop_table('observations')
    op.drop_table('baselines')
    op.drop_table('policy_predicted_impacts')
    op.drop_table('policy_changelog')
    op.drop_table('policy_guardrails')
    op.drop_table('policy_assumptions')

