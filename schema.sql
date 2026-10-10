-- schema.sql — engendré par python -m pipeline.schema_gen depuis pipeline/registry.py.
-- Ne pas éditer à la main : une valeur absente d'une énumération n'existe pas (§0).

CREATE TYPE filing_status AS ENUM ('filed', 'furnished', 'submitted_draft', 'correspondence', 'unclassified');
CREATE TYPE assurance_level AS ENUM ('audited', 'reviewed', 'unaudited', 'not_applicable');
CREATE TYPE tier AS ENUM ('A', 'B', 'C', 'D', 'E', 'F');
CREATE TYPE stage AS ENUM ('intent_non_binding', 'signed', 'available', 'drawn_or_paid', 'delivered', 'recognized', 'settled', 'terminated', 'none');
CREATE TYPE doc_class AS ENUM ('financial_statements', 'notes', 'contract', 'narrative', 'marketing', 'pointer', 'governance', 'non_edgar', 'inventory', 'none');
CREATE TYPE resource_kind AS ENUM ('api_tickers', 'api_submissions', 'api_companyfacts', 'filing_index', 'sgml_header', 'xbrl_zip', 'instance', 'linkbase', 'schema', 'metalinks', 'filing_summary', 'primary_document', 'exhibit', 'taxonomy_package', 'dataset_archive', 'web_page');
CREATE TYPE parse_state AS ENUM ('parsed', 'parse_failed', 'not_parsed');
CREATE TYPE counterparty_evidence AS ENUM ('named', 'derivable', 'anonymous', 'none');
CREATE TYPE derivation_method AS ENUM ('contract_parties', 'dimension_member_label', 'exact_amount_match', 'explicit_cross_reference', 'none');
CREATE TYPE family AS ENUM ('financing', 'credit_support', 'commercial', 'customer_consideration', 'none');
CREATE TYPE edge_type AS ENUM ('equity_primary', 'convertible_or_safe', 'loan_or_facility', 'vendor_credit', 'noncash_investment', 'lease_financing', 'guarantee', 'backstop', 'residual_value_guarantee', 'credit_enhancement', 'revenue_recognized', 'purchase', 'purchase_commitment', 'capacity_lease', 'prepayment', 'equity_or_warrants_to_customer', 'credits_to_customer', 'cash_incentive_to_customer', 'none');
CREATE TYPE edge_evidence AS ENUM ('amount', 'relation', 'none');
CREATE TYPE link_kind AS ENUM ('edge', 'relation_between_amounts', 'sales_channel_chain');
CREATE TYPE relation_type AS ENUM ('same_measure', 'component_of', 'covers', 'overlaps', 'replaces', 'eliminated_with', 'transfers_to', 'none');
CREATE TYPE relation_resolution AS ENUM ('unresolved', 'resolved_rule', 'resolved_document', 'resolved_executor', 'none');
CREATE TYPE financed_status AS ENUM ('active', 'lapsed', 'never', 'unknown');
CREATE TYPE financing_policy AS ENUM ('exposure_outstanding', 'ever_financed', 'none');
CREATE TYPE edge_structure AS ENUM ('financing_only', 'commercial_only', 'commercial_and_financing', 'reciprocal_commercial', 'none');
CREATE TYPE linkage_evidence AS ENUM ('documented_link', 'searched_none_found', 'search_incomplete');
CREATE TYPE link_category AS ENUM ('L1', 'L2', 'L3', 'L4', 'L5', 'none');
CREATE TYPE relationship_conclusion AS ENUM ('documented_dependency', 'commercial_with_financing', 'reciprocal_commercial_only', 'causality_not_established');
CREATE TYPE amount_nature AS ENUM ('revenue_recognized_gross', 'revenue_recognized_net', 'purchase_expensed', 'purchase_capitalized', 'purchase_unspecified', 'prepayment', 'commitment_unexecuted', 'distributor_sale', 'management_estimate', 'financing_cash', 'financing_noncash', 'investment_carrying_amount', 'fair_value', 'guarantee_amount', 'lease_payment', 'fee', 'interest', 'consideration_payable_to_customer', 'noncash_consideration_received', 'capacity_commitment', 'other', 'none');
CREATE TYPE amount_origin AS ENUM ('tagged_reference', 'narrative_only', 'none');
CREATE TYPE amount_qualifier AS ENUM ('exact', 'approximately', 'at_least', 'more_than', 'up_to', 'at_most', 'range', 'none');
CREATE TYPE event_type AS ENUM ('commitment', 'signing', 'availability', 'drawdown', 'funding', 'secondary_purchase', 'delivery', 'recognition', 'repayment', 'conversion', 'amendment', 'expiry', 'guarantee_call', 'payment', 'purchase', 'commencement', 'impairment', 'observable_price_adjustment', 'measurement_change', 'disposal', 'termination', 'default', 'acceleration', 'noncash_contribution', 'warrant_vesting', 'none');
CREATE TYPE exposure_block AS ENUM ('recognized_liabilities', 'contractual_outflows', 'contingent_obligations', 'exposed_assets', 'none');
CREATE TYPE category_id AS ENUM ('debt', 'lease_liability', 'financing_obligation', 'supplier_finance_program', 'earnout', 'derivative_credit_support', 'debt_maturity', 'lease_operating_maturity', 'lease_finance_maturity', 'lease_not_commenced', 'purchase_obligation', 'purchase_obligation_supplier_financing', 'take_or_pay', 'uncalled_commitment', 'jv_funding_commitment', 'construction_commitment', 'power_purchase_agreement', 'guarantee', 'vie_unconsolidated', 'standby_lc', 'capacity_backstop', 'receivables_transferred', 'indemnification', 'loss_contingency', 'equity_investment', 'loan_receivable', 'other', 'none');
CREATE TYPE measurement_basis AS ENUM ('carrying_amount', 'principal', 'undiscounted', 'discounted', 'fair_value', 'cost', 'commitment_cap', 'maximum_exposure', 'notional', 'initial_cap', 'outstanding_balance', 'equity_method', 'none');
CREATE TYPE seniority AS ENUM ('senior_secured', 'senior_unsecured', 'subordinated', 'unknown', 'none');
CREATE TYPE recourse AS ENUM ('full_recourse', 'limited_recourse', 'non_recourse', 'unknown', 'none');
CREATE TYPE elimination_status AS ENUM ('eliminated', 'not_eliminated', 'not_applicable', 'unknown');
CREATE TYPE component_kind AS ENUM ('principal', 'interest', 'lease_payment', 'purchase', 'minimum_purchase', 'capacity_fee', 'termination_payment', 'guarantee_cap', 'residual_value_guarantee', 'support_commitment_contractual', 'support_noncontractual', 'interest_held', 'other', 'none');
CREATE TYPE conditionality AS ENUM ('firm', 'conditional', 'optional', 'none');
CREATE TYPE trigger_occurred AS ENUM ('yes', 'no', 'unknown', 'none');
CREATE TYPE disclosure_regime AS ENUM ('tabular', 'notes', 'narrative', 'absent', 'unknown');
CREATE TYPE recast_cause AS ENUM ('error_correction_restatement', 'error_correction_revision', 'accounting_change', 'common_control_combination', 'discontinued_operations', 'segment_change', 'presentation_reclassification', 'unknown', 'none');
CREATE TYPE standard_application AS ENUM ('prospective', 'retrospective', 'modified_retrospective', 'full_retrospective', 'not_adopted', 'unknown');
CREATE TYPE view AS ENUM ('as_known', 'revised', 'none');
CREATE TYPE period_type AS ENUM ('instant', 'duration');
CREATE TYPE framework AS ENUM ('us_gaap', 'ifrs', 'dei', 'srt', 'extension', 'other');
CREATE TYPE measure_status AS ENUM ('computed', 'bounded', 'partial', 'not_determinable', 'not_applicable', 'blocked_overlap');
CREATE TYPE coverage_state AS ENUM ('observed', 'explicit_zero', 'not_disclosed', 'not_applicable', 'redacted', 'not_collected', 'not_processed', 'parse_failed', 'conflicting', 'policy_excluded', 'unknown');
CREATE TYPE bound_basis AS ENUM ('rounding', 'asc280_major_customer_completeness', 'publication_rule', 'none');
CREATE TYPE period_kind AS ENUM ('quarter', 'fiscal_year', 'ytd', 'ttm', 'instant', 'event', 'window', 'none');
CREATE TYPE nd_reason AS ENUM ('not_processed', 'search_incomplete', 'non_filer', 'redacted', 'anonymous', 'channel_indirect', 'parse_failed', 'denominator_nonpositive', 'denominator_below_threshold', 'recast_boundary', 'history_left_censored', 'term_missing', 'not_disclosed', 'not_collected', 'concept_unresolved', 'conflicting', 'mixed_currency', 'end_offset_exceeded', 'no_effect_published', 'precondition_not_met', 'date_missing', 'interval_straddles_threshold', 'prior_period_missing', 'not_tagged', 'no_named_counterparty', 'no_financed_pair', 'unequal_period_length', 'annual_only', 'pending_entity', 'blocked_overlap', 'out_of_first_pass', 'mixed_framework', 'none');
CREATE TYPE control_status AS ENUM ('ok', 'mismatch', 'not_testable', 'tautological');
CREATE TYPE tolerance_basis AS ENUM ('declared', 'inferred', 'none');
CREATE TYPE entity_record AS ENUM ('entity', 'membership', 'alias');
CREATE TYPE consolidation_treatment AS ENUM ('parent', 'consolidated_subsidiary', 'vie_consolidated', 'vie_unconsolidated', 'equity_method', 'investment_only', 'undetermined', 'none');
CREATE TYPE combination_method AS ENUM ('acquisition', 'common_control', 'succession', 'reorganization', 'reverse_recapitalization', 'none');
CREATE TYPE entity_status AS ENUM ('confirmed', 'pending');
CREATE TYPE resolution_rule AS ENUM ('same_cik', 'ex21', 'name_jurisdiction_two_documents', 'formerly_known_as', 'notes_consolidated', 'succession_document', 'executor_decision', 'config_seed', 'none');
CREATE TYPE group_kind AS ENUM ('config_group', 'lab', 'counterparty_group', 'joint_venture', 'none');
CREATE TYPE source_perspective AS ENUM ('reporting_entity', 'counterparty', 'none');
CREATE TYPE reporting_scope AS ENUM ('as_reported', 'pro_forma', 'as_if_combined', 'legacy_only', 'legal_entity', 'parent_only', 'none');
CREATE TYPE obs_kind AS ENUM ('observation', 'abstention');
CREATE TYPE abstention_reason AS ENUM ('no_relevant_content', 'boilerplate_no_event', 'financial_parties_only', 'no_named_counterparty', 'no_amount', 'illegible', 'out_of_scope_content', 'duplicate_of_other_block', 'cannot_describe_in_schema', 'none');
CREATE TYPE block_kind AS ENUM ('related_party_note', 'item_404', 'item_9a', 'item_4_10q', 'going_concern', 'item_8k_101', 'item_8k_102', 'item_8k_303', 'item_8k_801', 'exhibit_header', 'exhibit_body', 'spacex_annual_note', 'investment_note', 'debt_note', 'lease_note', 'commitments_note', 'concentration_text', 'item_8k_201', 'item_8k_203', 'lever_note', 'revenue_note', 'discovery_note', 'discovery_exhibit_header', 'discovery_exhibit_body');
CREATE TYPE signal AS ENUM ('material_weakness', 'going_concern', 'covenant_amendment', 'covenant_waiver', 'covenant_breach', 'capacity_contract_termination', 'auditor_change', 'nonreliance', 'pledged_assets', 'contract_termination_other', 'none');
CREATE TYPE validation_state AS ENUM ('valid', 'rejected_schema', 'rejected_semantic');
CREATE TYPE price_setting_participation AS ENUM ('yes', 'no', 'unknown', 'none');
CREATE TYPE exclusion_reason AS ENUM ('announcement_only', 'not_public', 'validation_failed', 'invalid_aggregate', 'financial_parties_only', 'not_processed', 'not_collected', 'parse_failed', 'history_left_censored', 'unclassified_quarantine', 'out_of_scope', 'policy_excluded', 'conflicting', 'pending_entity', 'submitted_draft', 'superseded_by_tagged', 'egress_blocked');
CREATE TYPE item_kind AS ENUM ('filing', 'document', 'block', 'observation_line', 'fact', 'aggregate', 'entity', 'measure_cell', 'query', 'period', 'group');
CREATE TYPE temporal AS ENUM ('yes', 'no', 'unknown');
CREATE TYPE annex_e_outcome AS ENUM ('supported', 'not_supported', 'refuted', 'indeterminate', 'compatible', 'incompatible', 'descriptive');

CREATE TABLE documents (
  doc_key VARCHAR NOT NULL,
  resource_kind resource_kind NOT NULL,
  url VARCHAR,
  cik VARCHAR,
  group_id VARCHAR,
  accession VARCHAR,
  document VARCHAR,
  sgml_type VARCHAR,
  sgml_description VARCHAR,
  form VARCHAR,
  items VARCHAR,
  filing_date DATE,
  acceptance_datetime TIMESTAMP,
  report_date DATE,
  knowledge_date DATE,
  filing_status filing_status,
  incorporated_by_reference BOOLEAN,
  doc_class doc_class,
  assurance_level assurance_level,
  tier tier,
  sha256 VARCHAR,
  size_bytes BIGINT,
  cache_path VARCHAR,
  fetched_as_of DATE,
  amends_accession VARCHAR,
  parse_state parse_state,
  normalizer_version VARCHAR,
  classification_note VARCHAR,
  PRIMARY KEY (doc_key)
);

CREATE TABLE facts (
  fact_key VARCHAR NOT NULL,
  source VARCHAR NOT NULL,
  cik VARCHAR,
  entity_id VARCHAR,
  group_id VARCHAR,
  accession VARCHAR,
  form VARCHAR,
  filing_date DATE,
  acceptance_datetime TIMESTAMP,
  doc_rank INTEGER,
  occ_rank INTEGER,
  concept VARCHAR NOT NULL,
  concept_ns VARCHAR,
  taxonomy_version VARCHAR,
  period_type period_type,
  period_start DATE,
  period_end DATE,
  unit VARCHAR,
  currency VARCHAR,
  dims VARCHAR,
  n_dims INTEGER,
  framework framework,
  reporting_scope reporting_scope,
  value DECIMAL(38,6),
  value_text VARCHAR,
  value_rounded BOOLEAN,
  decimals INTEGER,
  decimals_inf BOOLEAN,
  precision_known BOOLEAN,
  is_nil BOOLEAN,
  is_fixed_zero BOOLEAN,
  fact_id VARCHAR,
  locator VARCHAR,
  is_tagged BOOLEAN NOT NULL,
  tier tier,
  filing_status filing_status,
  assurance_level assurance_level,
  knowledge_date DATE,
  fy INTEGER,
  fp VARCHAR,
  model_quantity VARCHAR,
  conflict BOOLEAN,
  PRIMARY KEY (fact_key)
);

CREATE TABLE observations (
  obs_key VARCHAR NOT NULL,
  content_key VARCHAR NOT NULL,
  pass_as_of DATE NOT NULL,
  pass_id VARCHAR NOT NULL,
  line_no INTEGER NOT NULL,
  block_kind block_kind NOT NULL,
  doc_key VARCHAR,
  group_id VARCHAR,
  cik VARCHAR,
  accession VARCHAR,
  form VARCHAR,
  item VARCHAR,
  exhibit_type VARCHAR,
  knowledge_date DATE,
  filing_status filing_status,
  assurance_level assurance_level,
  tier tier,
  framework framework,
  kind obs_kind NOT NULL,
  abstention_reason abstention_reason,
  quote VARCHAR,
  locator VARCHAR,
  counterparty_name VARCHAR,
  counterparty_entity_id VARCHAR,
  counterparty_evidence counterparty_evidence,
  derivation_method derivation_method,
  payer VARCHAR,
  payee VARCHAR,
  amount DECIMAL(38,6),
  amount_lower DECIMAL(38,6),
  amount_upper DECIMAL(38,6),
  unit VARCHAR,
  currency VARCHAR,
  amount_nature amount_nature,
  amount_origin amount_origin,
  amount_qualifier amount_qualifier,
  candidate_fact_key VARCHAR,
  period_start DATE,
  period_end DATE,
  period_label VARCHAR,
  stage stage,
  event_type event_type,
  event_date DATE,
  instrument_key VARCHAR,
  family family,
  edge_type edge_type,
  link_category link_category,
  exposure_block exposure_block,
  category_id category_id,
  measurement_basis measurement_basis,
  component_kind component_kind,
  conditionality conditionality,
  trigger_description VARCHAR,
  trigger_occurred trigger_occurred,
  ultimate_obligor VARCHAR,
  seniority seniority,
  recourse recourse,
  is_ring_fenced BOOLEAN,
  signal signal,
  signal_present BOOLEAN,
  redacted BOOLEAN,
  judgment_sensitive BOOLEAN,
  price_setting_participation price_setting_participation,
  consolidation_treatment consolidation_treatment,
  party_role VARCHAR,
  party_is_financial_institution BOOLEAN,
  exhibit_title VARCHAR,
  note VARCHAR,
  validation_state validation_state NOT NULL,
  validation_error VARCHAR,
  PRIMARY KEY (obs_key)
);

CREATE TABLE entities (
  entity_id VARCHAR NOT NULL,
  record_kind entity_record NOT NULL,
  ref VARCHAR NOT NULL,
  valid_from VARCHAR NOT NULL,
  valid_to VARCHAR,
  name VARCHAR,
  normalized_name VARCHAR,
  cik VARCHAR,
  jurisdiction VARCHAR,
  is_filer BOOLEAN,
  is_financial_institution BOOLEAN,
  status entity_status,
  group_kind group_kind,
  consolidation_treatment consolidation_treatment,
  combination_method combination_method,
  common_control_start DATE,
  legal_date DATE,
  resolution_rule resolution_rule,
  evidence VARCHAR,
  PRIMARY KEY (entity_id, record_kind, ref, valid_from)
);

CREATE TABLE links (
  link_key VARCHAR NOT NULL,
  link_kind link_kind NOT NULL,
  family family,
  edge_type edge_type,
  edge_evidence edge_evidence,
  advance BOOLEAN,
  reciprocal_purchase BOOLEAN,
  from_entity VARCHAR,
  to_entity VARCHAR,
  from_group VARCHAR,
  to_group VARCHAR,
  amount DECIMAL(38,6),
  unit VARCHAR,
  currency VARCHAR,
  amount_nature amount_nature,
  stage stage,
  period_start DATE,
  period_end DATE,
  event_date DATE,
  relation_type relation_type,
  a_key VARCHAR,
  b_key VARCHAR,
  allocation DECIMAL(38,6),
  pair_id VARCHAR,
  resolution relation_resolution,
  resolution_ref VARCHAR,
  instrument_key VARCHAR,
  evidence_keys VARCHAR,
  tier tier,
  filing_status filing_status,
  source_perspective source_perspective,
  knowledge_date DATE,
  elimination_status elimination_status,
  PRIMARY KEY (link_key)
);

CREATE TABLE measures (
  measure VARCHAR NOT NULL,
  subject VARCHAR NOT NULL,
  counterparty VARCHAR NOT NULL,
  period_start VARCHAR NOT NULL,
  period_end VARCHAR NOT NULL,
  view view NOT NULL,
  as_of VARCHAR NOT NULL,
  term VARCHAR NOT NULL,
  breakdown_key VARCHAR NOT NULL,
  financing_policy financing_policy NOT NULL,
  constant_perimeter VARCHAR NOT NULL,
  variant VARCHAR NOT NULL,
  rank SMALLINT,
  period_kind period_kind,
  value DECIMAL(38,6),
  value_text VARCHAR,
  value_lower DECIMAL(38,6),
  value_upper DECIMAL(38,6),
  bound_basis bound_basis,
  numerator DECIMAL(38,6),
  denominator DECIMAL(38,6),
  unit VARCHAR,
  currency VARCHAR,
  status measure_status NOT NULL,
  nd_reason nd_reason,
  coverage_state coverage_state,
  evidence_profile VARCHAR,
  lineage VARCHAR,
  knowledge_date VARCHAR,
  is_tagged BOOLEAN,
  flags VARCHAR,
  PRIMARY KEY (measure, subject, counterparty, period_start, period_end, view, as_of, term, breakdown_key, financing_policy, constant_perimeter, variant),
  CHECK (measure IN ('financed_status', 'documented_revenue_dependency', 'investor_customer_revenue_share', 'noncash_revenue_from_investees', 'consideration_to_customer', 'documented_backlog_dependency', 'relationship_conclusion', 'named_edge_coverage', 'documented_pair_coverage', 'customer_concentration_anonymous', 'supplier_concentration', 'visible_pairs_count', 'revenue_growth', 'gross_margin', 'operating_margin', 'segment_revenue', 'segment_profit', 'segment_significant_expenses', 'capex_to_revenue', 'working_capital', 'liq_cash_to_12m_outflows', 'liq_undrawn_committed_facilities', 'liq_principal_due_to_cash', 'lev_debt_and_leases_to_operating_income_plus_da', 'cov_interest_coverage', 'cov_pik_interest', 'fcf_basic', 'fcf_after_finance_leases', 'fcf_after_counterparty_financing', 'fcf_after_sbc', 'sig_going_concern', 'sig_material_weakness', 'sig_auditor_change_or_nonreliance', 'sig_late_filing', 'sig_distress_8k_items', 'sig_covenant_events', 'sig_pledged_assets', 'eq_equity_and_accumulated_deficit', 'eq_diluted_share_count_change', 'counterparty_exposure', 'exposure_matrix', 'lease_not_commenced_bridge', 'capex_cash', 'capex_accrual', 'finance_lease_additions', 'vendor_financed_additions', 'stock_paid_additions', 'operating_lease_rou_additions', 'contract_coverage', 'earnings_bridge_pretax', 'earnings_bridge_share', 'depreciation_life_published', 'depreciation_life_change_effect', 'implied_useful_life', 'cip_share', 'cfo_net_income_gap', 'sbc_to_cfo', 'receivables_collection_period', 'customer_advances', 'capitalized_interest', 'rpo_total', 'rpo_beyond_12m', 'capex_to_cfo', 'lever_restatement', 'bdc_fv_to_cost', 'bdc_pik_share', 'bdc_non_accrual_share', 'documented_path', 'form_d_offering_amount', 'annex_e_outcome', 'fragility_event')),
  CHECK ((measure || ':' || term) IN ('financed_status:none', 'documented_revenue_dependency:none', 'investor_customer_revenue_share:none', 'noncash_revenue_from_investees:none', 'consideration_to_customer:none', 'documented_backlog_dependency:total', 'documented_backlog_dependency:beyond_12m', 'relationship_conclusion:none', 'named_edge_coverage:named', 'named_edge_coverage:anonymous', 'named_edge_coverage:residual', 'documented_pair_coverage:numerator', 'documented_pair_coverage:denominator', 'documented_pair_coverage:combinations', 'customer_concentration_anonymous:none', 'supplier_concentration:none', 'visible_pairs_count:none', 'revenue_growth:yoy', 'revenue_growth:ttm', 'gross_margin:none', 'operating_margin:none', 'segment_revenue:none', 'segment_profit:none', 'segment_significant_expenses:none', 'capex_to_revenue:none', 'working_capital:receivables', 'working_capital:inventories', 'working_capital:payables', 'working_capital:contract_liabilities', 'working_capital:net', 'working_capital:change', 'liq_cash_to_12m_outflows:with', 'liq_cash_to_12m_outflows:without', 'liq_undrawn_committed_facilities:none', 'liq_principal_due_to_cash:horizon_12m', 'liq_principal_due_to_cash:horizon_24m', 'lev_debt_and_leases_to_operating_income_plus_da:debt', 'lev_debt_and_leases_to_operating_income_plus_da:leases', 'cov_interest_coverage:with', 'cov_interest_coverage:without', 'cov_pik_interest:none', 'fcf_basic:none', 'fcf_after_finance_leases:none', 'fcf_after_counterparty_financing:none', 'fcf_after_sbc:none', 'sig_going_concern:none', 'sig_material_weakness:none', 'sig_auditor_change_or_nonreliance:none', 'sig_late_filing:none', 'sig_distress_8k_items:none', 'sig_covenant_events:none', 'sig_pledged_assets:none', 'eq_equity_and_accumulated_deficit:equity', 'eq_equity_and_accumulated_deficit:accumulated_deficit', 'eq_diluted_share_count_change:none', 'counterparty_exposure:none', 'exposure_matrix:none', 'lease_not_commenced_bridge:opening', 'lease_not_commenced_bridge:additions', 'lease_not_commenced_bridge:commenced', 'lease_not_commenced_bridge:closing', 'capex_cash:none', 'capex_accrual:none', 'finance_lease_additions:none', 'vendor_financed_additions:none', 'stock_paid_additions:none', 'operating_lease_rou_additions:none', 'contract_coverage:none', 'earnings_bridge_pretax:investment_gain_loss', 'earnings_bridge_pretax:dilution_gain', 'earnings_bridge_pretax:equity_method_income', 'earnings_bridge_pretax:investment_impairment', 'earnings_bridge_pretax:estimate_change_effect', 'earnings_bridge_pretax:capitalized_interest', 'earnings_bridge_pretax:bridge_total', 'earnings_bridge_share:none', 'depreciation_life_published:lower', 'depreciation_life_published:upper', 'depreciation_life_published:point', 'depreciation_life_change_effect:none', 'implied_useful_life:none', 'cip_share:none', 'cfo_net_income_gap:none', 'sbc_to_cfo:none', 'receivables_collection_period:none', 'customer_advances:none', 'capitalized_interest:none', 'rpo_total:none', 'rpo_beyond_12m:none', 'capex_to_cfo:with', 'capex_to_cfo:without', 'lever_restatement:published', 'lever_restatement:restated', 'lever_restatement:difference', 'bdc_fv_to_cost:none', 'bdc_pik_share:none', 'bdc_non_accrual_share:none', 'documented_path:none', 'form_d_offering_amount:none', 'annex_e_outcome:none', 'fragility_event:none'))
);

CREATE TABLE controls (
  control VARCHAR NOT NULL,
  subject VARCHAR NOT NULL,
  period_start VARCHAR NOT NULL,
  period_end VARCHAR NOT NULL,
  view view NOT NULL,
  as_of VARCHAR NOT NULL,
  breakdown_key VARCHAR NOT NULL,
  mapping_variant VARCHAR NOT NULL,
  accession VARCHAR,
  status control_status NOT NULL,
  explanation_code VARCHAR,
  not_testable_reason VARCHAR,
  lhs DECIMAL(38,6),
  rhs DECIMAL(38,6),
  difference DECIMAL(38,6),
  tolerance DECIMAL(38,6),
  tolerance_basis tolerance_basis,
  evidence VARCHAR,
  PRIMARY KEY (control, subject, period_start, period_end, view, as_of, breakdown_key, mapping_variant)
);

CREATE TABLE exclusions (
  exclusion_key VARCHAR NOT NULL,
  item_kind item_kind NOT NULL,
  item_key VARCHAR NOT NULL,
  reason exclusion_reason NOT NULL,
  detail VARCHAR,
  group_id VARCHAR,
  accession VARCHAR,
  content_key VARCHAR,
  invariant VARCHAR,
  raw VARCHAR,
  as_of VARCHAR,
  PRIMARY KEY (exclusion_key)
);
