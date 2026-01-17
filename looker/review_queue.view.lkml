view: v_review_queue_status {
  sql_table_name: `{project_id}.{dataset}.v_review_queue_status` ;;
  
  dimension: queue_id {
    type: string
    primary_key: yes
    sql: ${TABLE}.queue_id ;;
  }
  
  dimension: document_id {
    type: string
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
  
  dimension: reason {
    type: string
    sql: ${TABLE}.reason ;;
    description: "Reason for review (low_confidence, ambiguous_extraction, etc.)"
  }
  
  dimension: severity {
    type: string
    sql: ${TABLE}.severity ;;
    description: "Severity level (low, medium, high)"
  }
  
  dimension: review_status {
    type: string
    sql: ${TABLE}.review_status ;;
    description: "Review status (pending, in_progress, completed, dismissed)"
  }
  
  dimension: assigned_reviewer {
    type: string
    sql: ${TABLE}.assigned_reviewer ;;
  }
  
  dimension: created_at {
    type: timestamp
    sql: ${TABLE}.created_at ;;
    convert_tz: no
    timeframes: [raw, date, week, month]
  }
  
  dimension: hours_pending {
    type: number
    sql: ${TABLE}.hours_pending ;;
    value_format_name: decimal_1
    description: "Hours since item was added to review queue"
  }
  
  measure: count {
    type: count
    description: "Total items in review queue"
  }
  
  measure: pending_count {
    type: count
    filters: [review_status: "pending"]
    description: "Number of pending review items"
  }
  
  measure: in_progress_count {
    type: count
    filters: [review_status: "in_progress"]
    description: "Number of items currently under review"
  }
  
  measure: avg_hours_pending {
    type: average
    sql: ${TABLE}.hours_pending ;;
    value_format_name: decimal_1
    description: "Average hours pending in review queue"
  }
  
  measure: high_severity_count {
    type: count
    filters: [severity: "high"]
    description: "Number of high severity review items"
  }
}
