import axios from 'axios';
import type {
  DashboardStats, InvoiceSummary, InvoiceDetail,
  ProcessingRunSummary, ProcessingRunDetail,
} from './types';

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({ baseURL: BASE });

export async function getDashboard(): Promise<DashboardStats> {
  const { data } = await api.get('/api/dashboard/');
  return data;
}

export async function getInvoices(): Promise<InvoiceSummary[]> {
  const { data } = await api.get('/api/invoices/');
  return data;
}

export async function getInvoice(id: string): Promise<InvoiceDetail> {
  const { data } = await api.get(`/api/invoices/${id}`);
  return data;
}

export async function getInvoiceRuns(invoiceId: string): Promise<ProcessingRunSummary[]> {
  const { data } = await api.get(`/api/invoices/${invoiceId}/runs`);
  return data;
}

export async function getRun(runId: string): Promise<ProcessingRunDetail> {
  const { data } = await api.get(`/api/invoices/runs/${runId}`);
  return data;
}

export async function uploadInvoice(file: File): Promise<ProcessingRunSummary> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/api/invoices/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export const API_BASE = BASE;
