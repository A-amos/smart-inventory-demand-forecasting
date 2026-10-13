import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import Workspace from './Workspace';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const manager = { access_token: 'manager-token', user: { role: 'manager', name: 'Manager' } };
const category = { id: 1, name: 'Groceries', active: true };
const product = { id: 1, name: 'Rice', sku: 'RICE-1', unit: 'kg', active: true, category_id: 1, lead_time_days: 7,
  safety_stock: '3', overstock_multiplier: '2', inventory: { on_hand: '12.5', confirmed_in_transit: '0', allocated: '0', version: 1 } };
const response = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });

function setup({ categories = [category], products = [], role = 'manager', mutate } = {}) {
  const state = { categories, products };
  const mock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, options) => {
    if ((options.method || 'GET') !== 'GET') return mutate(url, options, state);
    if (url.startsWith('/api/v1/categories?')) return response(state.categories);
    if (url.startsWith('/api/v1/products?')) return response(state.products);
    if (url.endsWith('/movements')) return response([{ id: 1, product_id: 1, actor_id: 1, kind: 'opening', reason: 'Opening stock',
      on_hand_before: '0', on_hand_after: '12.5', in_transit_before: '0', in_transit_after: '0', allocated_before: '0', allocated_after: '0', created_at: '2026-09-30T12:00:00' }]);
    throw new Error('Unexpected request ' + url);
  });
  render(<Workspace session={{ ...manager, user: { role } }} onUnauthorized={vi.fn()}/>);
  return mock;
}

test('manager creates a category and sees refreshed data', async () => {
  const mock = setup({ categories: [], mutate: (_, options, state) => { state.categories = [{ ...JSON.parse(options.body), id: 2 }]; return response(state.categories[0], 201); } });
  await screen.findByText('No products yet. Create a category, then add your first product.');
  fireEvent.click(screen.getByRole('button', { name: 'Categories' }));
  fireEvent.change(screen.getByLabelText('Category name'), { target: { value: 'Food' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save category' }));
  expect(await screen.findByRole('button', { name: 'Edit Food' })).toBeInTheDocument();
  const request = mock.mock.calls.find(([, options]) => options.method === 'POST');
  expect(JSON.parse(request[1].body)).toEqual({ name: 'Food', active: true });
});

test('manager creates a product with stock and replenishment configuration', async () => {
  const mock = setup({ mutate: (_, options, state) => { state.products = [{ ...product, ...JSON.parse(options.body), inventory: product.inventory }]; return response(state.products[0], 201); } });
  await screen.findByRole('form', { name: 'Product form' });
  fireEvent.change(screen.getByLabelText('SKU'), { target: { value: 'RICE-1' } });
  fireEvent.change(screen.getByLabelText('Product name'), { target: { value: 'Rice' } });
  fireEvent.change(screen.getByLabelText('Category'), { target: { value: '1' } });
  fireEvent.change(screen.getByLabelText('Opening stock'), { target: { value: '12.5' } });
  fireEvent.change(screen.getByLabelText('Safety stock'), { target: { value: '3' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save product' }));
  expect(await screen.findByRole('button', { name: 'Edit Rice' })).toBeInTheDocument();
  const payload = JSON.parse(mock.mock.calls.find(([, options]) => options.method === 'POST')[1].body);
  expect(payload).toMatchObject({ category_id: 1, lead_time_days: 7, safety_stock: '3', initial_stock: '12.5', overstock_multiplier: '2' });
});

test('duplicate SKU error preserves entered form', async () => {
  setup({ mutate: () => response({ detail: 'SKU already exists' }, 409) });
  await screen.findByRole('form', { name: 'Product form' });
  fireEvent.change(screen.getByLabelText('SKU'), { target: { value: 'RICE-1' } });
  fireEvent.submit(screen.getByRole('form', { name: 'Product form' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('SKU already exists');
  expect(screen.getByLabelText('SKU')).toHaveValue('RICE-1');
});

test('inventory adjustment sends quantities, reason and loaded version', async () => {
  const mock = setup({ products: [product], mutate: (_, options, state) => { state.products = [{ ...product, inventory: { ...JSON.parse(options.body), version: 2 } }]; return response(state.products[0].inventory); } });
  await screen.findByRole('button', { name: 'Edit Rice' });
  fireEvent.click(screen.getByRole('button', { name: 'Inventory' }));
  fireEvent.click(screen.getByRole('button', { name: 'Adjust Rice' }));
  fireEvent.change(screen.getByLabelText('On-hand stock'), { target: { value: '20' } });
  fireEvent.change(screen.getByLabelText('Adjustment reason'), { target: { value: 'Physical stock count' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save stock adjustment' }));
  await waitFor(() => expect(screen.queryByRole('form', { name: 'Inventory form' })).not.toBeInTheDocument());
  expect(JSON.parse(mock.mock.calls.find(([, options]) => options.method === 'PUT')[1].body)).toMatchObject({ on_hand: '20', reason: 'Physical stock count', version: 1 });
});

test('researcher sees records and history without mutation controls', async () => {
  setup({ products: [product], role: 'researcher' });
  await screen.findByText('Rice');
  expect(screen.queryByRole('form', { name: 'Product form' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Edit Rice' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Inventory' }));
  expect(screen.queryByRole('button', { name: 'Adjust Rice' })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'History for Rice' }));
  expect(await screen.findByRole('region', { name: 'Stock history' })).toHaveTextContent('Opening stock');
});

test('archive hides product and show-archived exposes edit for restoration', async () => {
  const mock = setup({ products: [product], mutate: (_, __, state) => { state.products = [{ ...product, active: false }]; return response(null, 204); } });
  fireEvent.click(await screen.findByRole('button', { name: 'Archive Rice' }));
  await waitFor(() => expect(screen.queryByRole('button', { name: 'Edit Rice' })).not.toBeInTheDocument());
  fireEvent.click(screen.getByLabelText('Show archived records'));
  expect(screen.getByRole('button', { name: 'Edit Rice' })).toBeInTheDocument();
  expect(mock.mock.calls.some(([url, options]) => url === '/api/v1/products/1' && options.method === 'DELETE')).toBe(true);
});

test('expired session clears authenticated workspace through callback', async () => {
  const onUnauthorized = vi.fn();
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ detail: 'Authentication required' }, 401));
  render(<Workspace session={manager} onUnauthorized={onUnauthorized}/>);
  await waitFor(() => expect(onUnauthorized).toHaveBeenCalled());
});
