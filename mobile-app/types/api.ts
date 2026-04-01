export interface AnalyzeResult {
  risk_level: string;
  risk_score: number;
  recommendation: string;
  explanation: string;
  alert?: any;
  delay_transaction: boolean;
  sms_analysis: any;
  transaction_analysis: any;
  response_time_ms: number;
}