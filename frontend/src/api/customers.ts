import client from './client'

export interface CustomerContact {
  id?: number
  name?: string | null
  phone?: string | null
  email?: string | null
  position?: string | null
}

export interface Customer {
  id: number
  customer_code?: string | null
  customer_name: string
  dept_id?: string | null
  country?: string | null
  basic_require?: string | null
  special_require?: string | null
  payment_terms?: string | null
  status?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export interface CustomerFormPayload {
  customer_name: string
  dept_id?: string
  country?: string | null
  basic_require?: string | null
  special_require?: string | null
  payment_terms?: string | null
}

export const customersApi = {
  list: (params: { skip?: number; limit?: number } = {}) =>
    client.get<Customer[]>('/api/customers/', { params }),
  get: (id: number) => client.get<Customer>(`/api/customers/${id}`),
  create: (payload: CustomerFormPayload) => client.post<Customer>('/api/customers/', payload),
  update: (id: number, payload: Partial<CustomerFormPayload>) =>
    client.put<Customer>(`/api/customers/${id}`, payload),
  remove: (id: number) => client.delete(`/api/customers/${id}`),
  toggleStatus: (id: number) => client.patch(`/api/customers/${id}/status`),
  contacts: (id: number) => client.get<CustomerContact[]>(`/api/customers/${id}/contacts`),
  createContact: (id: number, payload: Omit<CustomerContact, 'id'>) =>
    client.post(`/api/customers/${id}/contacts`, payload),
  updateContact: (id: number, contactId: number, payload: Omit<CustomerContact, 'id'>) =>
    client.put(`/api/customers/${id}/contacts/${contactId}`, payload),
  removeContact: (id: number, contactId: number) =>
    client.delete(`/api/customers/${id}/contacts/${contactId}`),
}