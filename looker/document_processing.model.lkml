connection: "bigquery_document_processing"

# Include manifest of views
include: "*.view.lkml"

datagroup: document_processing_default_datagroup {
  sql_trigger: SELECT MAX(id) FROM etl_log;;
  max_cache_age: "1 hour"
}

persist_with: document_processing_default_datagroup

# Semantic model for Document Processing Dashboard
explore: documents {
  label: "Documents"
  description: "Document processing and extraction metrics"
  
  # Base explore
  from: documents {}
  
  # Joins to related views
  join: stakeholders {
    sql_on: ${documents.document_id} = ${stakeholders.document_id} ;;
    type: left_outer
    relationship: one_to_many
  }
  
  join: deliverables {
    sql_on: ${documents.document_id} = ${deliverables.document_id} ;;
    type: left_outer
    relationship: one_to_many
  }
  
  join: deadlines {
    sql_on: ${documents.document_id} = ${deadlines.document_id} ;;
    type: left_outer
    relationship: one_to_many
  }
  
  join: financials {
    sql_on: ${documents.document_id} = ${financials.document_id} ;;
    type: left_outer
    relationship: one_to_many
  }
  
  join: review_queue {
    sql_on: ${documents.document_id} = ${review_queue.document_id} ;;
    type: left_outer
    relationship: one_to_one
  }
  
  join: processing_summary {
    sql_on: ${documents.document_id} = ${processing_summary.document_id} ;;
    type: left_outer
    relationship: one_to_one
  }
}

explore: processing_volume {
  label: "Processing Volume"
  description: "Document processing volume and throughput metrics"
  
  from: v_document_processing_summary {}
}

explore: low_confidence_extractions {
  label: "Low Confidence Extractions"
  description: "Entities with low confidence scores requiring manual review"
  
  from: v_low_confidence_extractions {}
}

explore: review_queue_status {
  label: "Review Queue"
  description: "Documents and entities flagged for manual review"
  
  from: v_review_queue_status {}
  
  join: documents {
    sql_on: ${review_queue_status.document_id} = ${documents.document_id} ;;
    type: left_outer
    relationship: many_to_one
  }
}

explore: entity_extraction_stats {
  label: "Entity Extraction Statistics"
  description: "Statistics on extracted entities by type and date"
  
  from: v_entity_extraction_stats {}
}

explore: weekly_metrics {
  label: "Weekly Processing Metrics"
  description: "Weekly aggregated processing metrics and trends"
  
  from: v_weekly_processing_metrics {}
}

explore: stakeholder_analysis {
  label: "Stakeholder Analysis"
  description: "Analysis of extracted stakeholders across documents"
  
  from: v_stakeholder_analysis {}
}

explore: deadline_tracking {
  label: "Deadline Tracking"
  description: "Upcoming deadlines extracted from documents"
  
  from: v_deadline_tracking {}
}

explore: financial_summary {
  label: "Financial Summary"
  description: "Financial terms and amounts extracted from documents"
  
  from: v_financial_summary {}
}
