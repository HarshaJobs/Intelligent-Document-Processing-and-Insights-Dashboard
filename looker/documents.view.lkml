view: documents {
  sql_table_name: `{project_id}.{dataset}.documents` ;;
  
  dimension: document_id {
    type: string
    primary_key: yes
    sql: ${TABLE}.document_id ;;
  }
  
  dimension: filename {
    type: string
    sql: ${TABLE}.filename ;;
  }
  
  dimension: document_type {
    type: string
    sql: ${TABLE}.document_type ;;
    description: "Type of document (sow, contract, email, amendment, msa, other)"
  }
  
  dimension: structure_type {
    type: string
    sql: ${TABLE}.structure_type ;;
    description: "Document structure (structured, semi_structured, unstructured)"
  }
  
  dimension: processing_status {
    type: string
    sql: ${TABLE}.processing_status ;;
    description: "Processing status (pending, processing, completed, failed, review_required)"
  }
  
  dimension: upload_timestamp {
    type: timestamp
    sql: ${TABLE}.upload_timestamp ;;
    convert_tz: no
    timeframes: [raw, date, week, month, quarter, year]
  }
  
  dimension_group: processing {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.processing_started_at ;;
  }
  
  measure: count {
    type: count
    description: "Total number of documents"
  }
  
  measure: avg_confidence {
    type: average
    sql: ${TABLE}.overall_confidence ;;
    value_format_name: decimal_2
    description: "Average confidence score across documents"
  }
  
  measure: low_confidence_count {
    type: count
    filters: [overall_confidence: "<0.7"]
    description: "Number of documents with confidence below 0.7"
  }
  
  measure: review_required_count {
    type: count
    filters: [processing_status: "review_required"]
    description: "Number of documents requiring manual review"
  }
  
  measure: completed_count {
    type: count
    filters: [processing_status: "completed"]
    description: "Number of successfully processed documents"
  }
  
  measure: failed_count {
    type: count
    filters: [processing_status: "failed"]
    description: "Number of failed document processing attempts"
  }
  
  measure: total_text_length {
    type: sum
    sql: ${TABLE}.raw_text_length ;;
    description: "Total text length processed"
    value_format_name: decimal_0
  }
}
