import client from './client'
import { CUSTOMERS } from './endpoints'

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
    client.get<Customer[]>(CUSTOMERS.list, { params }),
  get: (id: number) => client.get<Customer>(CUSTOMERS.detail(id)),
  create: (payload: CustomerFormPayload) => client.post<Customer>(CUSTOMERS.create, payload),
  update: (id: number, payload: Partial<CustomerFormPayload>) =>
    client.put<Customer>(CUSTOMERS.update(id), payload),
  remove: (id: number) => client.delete(CUSTOMERS.remove(id)),
  toggleStatus: (id: number) => client.patch(CUSTOMERS.toggleStatus(id)),
  contacts: (id: number) => client.get<CustomerContact[]>(CUSTOMERS.contacts(id)),
  createContact: (id: number, payload: Omit<CustomerContact, 'id'>) =>
    client.post(CUSTOMERS.createContact(id), payload),
  updateContact: (id: number, contactId: number, payload: Omit<CustomerContact, 'id'>) =>
    client.put(CUSTOMERS.updateContact(id, contactId), payload),
  removeContact: (id: number, contactId: number) =>
    client.delete(CUSTOMERS.removeContact(id, contactId)),
}