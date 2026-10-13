import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { CsvImport, SaleEntry, SalesHistory } from './SalesPages';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
const product = { id: 3, name: 'Rice', sku: 'RICE-1', unit: 'kg', active: true,
  inventory: { on_hand: '10', allocated: '2', version: 5 } };
const props = { token: 'manager-token', manager: true, products: [product], onUnauthorized: vi.fn(), onInventoryChanged: vi.fn().mockResolvedValue() };
const response = (data, status = 200) => ({ ok: status < 400, status, json: async () => data });
const batch = { id: 'batch', filename: 'history.csv', status: 'preview', preview_version: 2, valid_count: 1, rejected_count: 1,
  accepted_preview: [{ row_number: 2, sku: 'RICE-1', sale_date: '2026-09-01T00:00:00Z', quantity: '3', unit_price: null }],
  rejected_rows: [{ row_number: 3, values: { sku: 'MISSING', quantity: '-1' }, reason: 'Unknown SKU' }], imported_count: 0 };

function enterSale() {
  fireEvent.change(screen.getByLabelText('Sale product / SKU'), { target: { value: '3' } });
  fireEvent.change(screen.getByLabelText('Sale quantity'), { target: { value: '2.5' } });
  fireEvent.change(screen.getByLabelText('Sale date/time (Nairobi)'), { target: { value: '2026-09-01T10:00' } });
}

test('sale sends version, timezone, optional price and request key; reloads inventory', async () => {
  const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ id: 7, quantity: '2.5' }, 201));
  const reload = vi.fn().mockResolvedValue();
  render(<SaleEntry {...props} onInventoryChanged={reload}/>);
  enterSale();
  expect(screen.getByText(/Available: 8 kg/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Record sale' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Sale #7 recorded');
  expect(JSON.parse(mock.mock.calls[0][1].body)).toMatchObject({ product_id: 3, inventory_version: 5,
    sale_date: '2026-09-01T07:00:00.000Z', quantity: '2.5', unit_price: null });
  expect(JSON.parse(mock.mock.calls[0][1].body).request_key).toMatch(/^[0-9a-f-]{36}$/);
  await waitFor(() => expect(reload).toHaveBeenCalledOnce());
});

test('stale inventory error preserves form and unchanged retry key', async () => {
  const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ detail: 'Stock changed. Reload inventory.' }, 409));
  render(<SaleEntry {...props}/>); enterSale();
  fireEvent.submit(screen.getByRole('form', { name: 'Sales entry form' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Stock changed');
  expect(screen.getByLabelText('Sale quantity')).toHaveValue(2.5);
  fireEvent.submit(screen.getByRole('form', { name: 'Sales entry form' }));
  await waitFor(() => expect(mock).toHaveBeenCalledTimes(2));
  expect(JSON.parse(mock.mock.calls[0][1].body).request_key).toBe(JSON.parse(mock.mock.calls[1][1].body).request_key);
});

test('researcher sees no sale or CSV mutation form', () => {
  render(<><SaleEntry {...props} manager={false}/><CsvImport {...props} manager={false}/></>);
  expect(screen.queryByRole('form')).not.toBeInTheDocument();
  expect(screen.getByText('A manager account is required to record sales.')).toBeInTheDocument();
  expect(screen.getByText('A manager account is required to import sales.')).toBeInTheDocument();
});

test('archived products are excluded from sales selection', () => {
  render(<SaleEntry {...props} products={[product, { ...product, id: 4, sku: 'ARCHIVED', active: false }]}/>);
  expect(screen.queryByRole('option', { name: /ARCHIVED/ })).not.toBeInTheDocument();
});

test('sales session expiration invokes the auth callback', async () => {
  const expired = vi.fn();
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ detail: 'Authentication required' }, 401));
  render(<SaleEntry {...props} onUnauthorized={expired}/>); enterSale();
  fireEvent.submit(screen.getByRole('form', { name: 'Sales entry form' }));
  await waitFor(() => expect(expired).toHaveBeenCalledOnce());
});

test('history filters and pagination send product, user, source and UTC dates', async () => {
  const mock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ items: [{ id: 8, product_id: 3, sku_snapshot: 'RICE-1',
    sale_date: '2026-09-01T07:00:00Z', quantity: '2', unit_price: null, source: 'historical', actor_id: 1 }], total: 21 }));
  render(<SalesHistory {...props}/>);
  expect(await screen.findByText('RICE-1', { selector: 'td' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Next sales' }));
  await waitFor(() => expect(mock.mock.calls.at(-1)[0]).toContain('offset=20'));
  fireEvent.change(screen.getByLabelText('History product'), { target: { value: '3' } });
  fireEvent.change(screen.getByLabelText('Actor user ID'), { target: { value: '1' } });
  fireEvent.change(screen.getByLabelText('From (Nairobi)'), { target: { value: '2026-09-01T10:00' } });
  fireEvent.change(screen.getByLabelText('Sales source'), { target: { value: 'historical' } });
  await waitFor(() => expect(screen.getByRole('button', { name: 'Apply sales filters' })).not.toBeDisabled());
  fireEvent.click(screen.getByRole('button', { name: 'Apply sales filters' }));
  await waitFor(() => expect(mock.mock.calls.at(-1)[0]).toContain('product_id=3'));
  const query = new URL(mock.mock.calls.at(-1)[0], 'http://localhost').searchParams;
  expect(Object.fromEntries(query)).toMatchObject({ actor_id: '1', source: 'historical', offset: '0', date_from: '2026-09-01T07:00:00.000Z' });
});

test('empty history displays meaningful feedback', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ items: [], total: 0 }));
  render(<SalesHistory {...props}/>);
  expect(await screen.findByText('No sales match these filters.')).toBeInTheDocument();
});

function chooseFile(size) {
  const file = new File(['sku,sale_date,quantity\nRICE-1,2026-09-01T00:00:00Z,3\n'], 'history.csv', { type: 'text/csv' });
  if (size) Object.defineProperty(file, 'size', { value: size });
  fireEvent.change(screen.getByLabelText('Historical CSV file'), { target: { files: [file] } });
  return file;
}

test('CSV preview shows all rejected rows and requires acceptance before confirmation', async () => {
  const mock = vi.spyOn(globalThis, 'fetch').mockImplementation(async url => response(url.endsWith('/confirm') ? { ...batch, status: 'committed', imported_count: 1 } : batch));
  render(<CsvImport {...props}/>);
  const file = chooseFile();
  fireEvent.submit(screen.getByRole('form', { name: 'CSV preview form' }));
  expect(await screen.findByRole('region', { name: 'Rejected import rows' })).toHaveTextContent('Row 3: Unknown SKU');
  expect(mock.mock.calls[0][1].body).toBe(file);
  expect(mock.mock.calls[0][1].headers['Content-Type']).toBe('text/csv');
  expect(screen.getByRole('button', { name: 'Confirm historical import' })).toBeDisabled();
  fireEvent.click(screen.getByRole('checkbox', { name: /I reviewed/ }));
  fireEvent.click(screen.getByRole('button', { name: 'Confirm historical import' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Current stock is unchanged');
  expect(JSON.parse(mock.mock.calls[1][1].body)).toEqual({ preview_version: 2, accept_valid_rows: true });
  expect(screen.queryByRole('button', { name: 'Confirm historical import' })).not.toBeInTheDocument();
  expect(screen.getByRole('region', { name: 'Rejected import rows' })).toHaveTextContent('MISSING');
});

test('repeat-file preview reports previously imported and offers no second confirmation', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ ...batch, status: 'committed', imported_count: 1 }));
  render(<CsvImport {...props}/>); chooseFile();
  fireEvent.submit(screen.getByRole('form', { name: 'CSV preview form' }));
  expect(await screen.findByText(/previously imported; no additional rows saved/)).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Confirm historical import' })).not.toBeInTheDocument();
});

test('oversized CSV rejected locally without a request', async () => {
  const mock = vi.spyOn(globalThis, 'fetch');
  render(<CsvImport {...props}/>); chooseFile(1024 * 1024 + 1);
  fireEvent.submit(screen.getByRole('form', { name: 'CSV preview form' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('1 byte to 1 MiB');
  expect(mock).not.toHaveBeenCalled();
});

test('import conflict is visible and preserves rejected-row report', async () => {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async url => url.endsWith('/confirm') ? response({ detail: 'Preview changed. Preview again.' }, 409) : response(batch));
  render(<CsvImport {...props}/>); chooseFile();
  fireEvent.submit(screen.getByRole('form', { name: 'CSV preview form' }));
  await screen.findByRole('region', { name: 'Import preview' });
  fireEvent.click(screen.getByRole('checkbox', { name: /I reviewed/ }));
  fireEvent.click(screen.getByRole('button', { name: 'Confirm historical import' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Preview changed');
  expect(screen.getByRole('region', { name: 'Rejected import rows' })).toHaveTextContent('Unknown SKU');
});
