view: v_low_confidence_extractions {
  sql_table_name: `{project_id}.{dataset}.v_low_confidence_extractions` ;;
  
  dimension: document_id {
    type: string
    primary_key: no
    sql: ${TABLE}.document_id ;;
  }
  
  dimension: filename {
    type: string
    sql: ${TABLE}.filename ;;
  }
  
  dimension: document_type {
    type: string
    sql: ${TABLE}.document_type ;;
  }
  
  dimension: entity_type {
    type: string
    sql: ${TABLE}.entity_type ;;
    description: "Type of entity (stakeholder, deliverable, deadline, financial)"
  }
  
  dimension: entity_id {
    type: string
    sql: ${TABLE}.entity_id ;;
  }
  
  dimension: entity_name {
    type: string
    sql: ${TABLE}.entity_name ;;
  }
  
  dimension: stakeholder_type {
    type: string
    sql: ${TABLE}.stakeholder_type ;;
  }
  
  dimension: upload_timestamp {
    type: timestamp
    sql: ${TABLE}.upload_timestamp ;;
    convert_tz: no
    timeframes: [raw, date, week, month]
  }
  
  measure: count {
    type: count
    description: "Total number of low confidence extractions"
  }
  
  measure: avg_document_confidence {
    type: average
    sql: ${TABLE}.document_confidence ;;
    value_format_name: decimal_2
  }
  
  measure: avg_entity_confidence {
    type: average
    sql: ${TABLE}.entity_confidence ;;
    value_format_name: decimal_2
  }
  
  measure: count_by_entity_type {
    type: count
    group_by: entity_type
    description: "Count of low confidence extractions by entity type"
  }
}
