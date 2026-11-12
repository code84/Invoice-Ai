// Shared TypeScript types matching backend Pydantic schemas

export interface Vendor {
  id: string;
  vendor_id: string;
  legal_name: string;
  aliases: string[];
  tax_id: string | null;
  status: string;
  is_approved: boolean;
  currency: string;
  country: string;
}

export interface LineItem {
  description: string;
  quantity: number | null;
  unit_price: number | null;
  amount: number | null;
}

export interface InvoiceSummary {
  id: string;
  filename: string;
  upload_time: string;
  vendor_name: string | null;
  invoice_number: string | null;
  invoice_date: string | null;
  po_number: string | null;
  currency: string | null;
  total: number | null;
  final_status: string | null;
  is_duplicate: boolean;
}

export interface InvoiceDetail extends InvoiceSummary {
  file_path: string | null;
  file_size: number | null;
  due_date: string | null;
  subtotal: number | null;
  tax: number | null;
  tax_rate: number | null;
  tax_id: string | null;
  billing_address: string | null;
  payment_terms: string | null;
  line_items: LineItem[];
  pdf_type: string | null;
  extraction_confidence: number | null;
  missing_fields: string[];
  matched_po_id: string | null;
  matched_vendor_id: string | null;
  decision_explanation: string | null;
  recommended_action: string | null;
  duplicate_of_id: string | null;
}

export interface ProcessingStage {
  id: string;
  stage_name: string;
  stage_label: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string | null;
  completed_at: string | null;
  output_summary: string | null;
  error_message: string | null;
  order_index: number;
}

export interface ValidationResult {
  id: string;
  check_name: string;
  result: 'passed' | 'failed' | 'warning' | 'review';
  observed_value: string | null;
  expected_value: string | null;
  message: string;
  created_at: string;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  description: string;
  event_metadata: Record<string, unknown>;
  created_at: string;
}

export interface ProcessingRunSummary {
  id: string;
  run_id: string;
  invoice_id: string;
  status: 'running' | 'completed' | 'failed';
  current_stage: string | null;
  started_at: string;
  completed_at: string | null;
  error_message: string | null;
}

export interface ProcessingRunDetail extends ProcessingRunSummary {
  stages: ProcessingStage[];
  validation_results: ValidationResult[];
  audit_events: AuditEvent[];
}

export interface DashboardStats {
  total_processed: number;
  approved: number;
  needs_review: number;
  flagged: number;
  recent_invoices: InvoiceSummary[];
}

export type FinalStatus = 'approved' | 'needs_review' | 'rejected' | null;
