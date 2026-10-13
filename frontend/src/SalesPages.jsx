import { useEffect, useRef, useState } from 'react';
import { api } from './api';

const nairobiNow = () => new Date(Date.now() + 3 * 3600000).toISOString().slice(0, 16);
const iso = value => new Date(`${value}:00+03:00`).toISOString();
const number = value => Number(value).toLocaleString('en-KE', { maximumFractionDigits: 3 });
const time = value => new Date(value).toLocaleString('en-KE', { timeZone: 'Africa/Nairobi' });

function Feedback({ error, success }) {
  return <>{error && <p role="alert" className="text-red-700 mb-4">{error}</p>}{success && <p role="status" className="notice mb-4">{success}</p>}</>;
}

function useAction(onUnauthorized) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  async function run(action) {
    setBusy(true); setError(''); setSuccess('');
    try { await action(setSuccess); }
    catch (err) { if (err.status === 401) onUnauthorized(); else setError(err.message); }
    finally { setBusy(false); }
  }
  return { busy, error, success, run };
}

export function SaleEntry({ token, manager, products, onUnauthorized, onInventoryChanged }) {
  const [selected, setSelected] = useState('');
  const requestKey = useRef(crypto.randomUUID());
  const state = useAction(onUnauthorized);
  const product = products.find(item => item.id === Number(selected) && item.active);
  return <section><h3 className="text-lg font-semibold mb-4">Record an operational sale</h3>
    <p className="text-sm text-slate-600 mb-4">This reduces current unallocated on-hand stock. Use CSV import for historical observations. Dates are entered in Nairobi time; unit prices are in KES.</p>
    <Feedback {...state}/>
    {!manager ? <p className="notice">A manager account is required to record sales.</p> : <form aria-label="Sales entry form" key={`${selected}:${product?.inventory.version}`} onChange={() => { requestKey.current = crypto.randomUUID(); }} onSubmit={event => {
      event.preventDefault();
      const form = event.currentTarget;
      const values = Object.fromEntries(new FormData(form));
      state.run(async success => {
        const result = await api('/sales', { token, method: 'POST', body: JSON.stringify({ product_id: Number(selected),
          quantity: values.quantity, unit_price: values.unit_price || null, sale_date: iso(values.sale_date),
          inventory_version: product.inventory.version, request_key: requestKey.current }) });
        // A successful sale must remain visibly successful even if the subsequent reload fails.
        success(`Sale #${result.id} recorded. ${number(result.quantity)} ${product.unit} deducted from current stock.`);
        requestKey.current = crypto.randomUUID(); form.reset();
        try { await onInventoryChanged(); } catch { success(`Sale #${result.id} recorded. Reload records to view the updated stock.`); }
      });
    }}><fieldset disabled={state.busy} className="space-y-4">
      <label className="block text-sm font-medium">Sale product / SKU<select className="field" name="product_id" required value={selected} onChange={event => setSelected(event.target.value)}><option value="">Select a product</option>{products.filter(item => item.active).map(item => <option key={item.id} value={item.id}>{item.name} · {item.sku}</option>)}</select></label>
      {product && <p className="notice">Available: {number(Number(product.inventory.on_hand) - Number(product.inventory.allocated))} {product.unit}. Stock version {product.inventory.version}. Allocated and incoming stock cannot be sold.</p>}
      <div className="grid sm:grid-cols-3 gap-4">
        <label className="block text-sm font-medium">Sale quantity<input className="field" name="quantity" type="number" min="0.001" step="0.001" required/></label>
        <label className="block text-sm font-medium">Sale date/time (Nairobi)<input className="field" name="sale_date" type="datetime-local" required defaultValue={nairobiNow()}/></label>
        <label className="block text-sm font-medium">Unit price (KES, optional)<input className="field" name="unit_price" type="number" min="0" step="0.01"/></label>
      </div><button className="button" disabled={!product}>Record sale</button>
    </fieldset></form>}
  </section>;
}

export function SalesHistory({ token, products, onUnauthorized }) {
  const [filters, setFilters] = useState('');
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState(null);
  const [reload, setReload] = useState(0);
  const state = useAction(onUnauthorized);
  useEffect(() => {
    let active = true;
    state.run(async () => {
      const result = await api(`/sales?${filters}&offset=${offset}&limit=20`, { token });
      if (active) setPage(result);
    });
    return () => { active = false; };
  }, [token, filters, offset, reload]);
  return <section><h3 className="text-lg font-semibold mb-4">Sales history</h3><Feedback {...state}/>
    <p className="text-sm text-slate-600 mb-4">Newest sale first, with stable ordering for equal timestamps. Dates shown in Nairobi time. Historical imports retain the importing user and do not affect current stock.</p>
    <form aria-label="Sales history filters" onSubmit={event => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.currentTarget));
      const query = new URLSearchParams();
      for (const [key, value] of Object.entries(values)) if (value) query.set(key, key.startsWith('date_') ? iso(value) : value);
      setFilters(query.toString()); setOffset(0); setReload(value => value + 1);
    }} className="space-y-4 mb-6"><fieldset disabled={state.busy} className="grid sm:grid-cols-2 gap-4">
      <label className="block text-sm font-medium">History product<select className="field" name="product_id"><option value="">All products</option>{products.map(item => <option key={item.id} value={item.id}>{item.sku}{!item.active && ' (archived)'}</option>)}</select></label>
      <label className="block text-sm font-medium">Actor user ID<input className="field" name="actor_id" type="number" min="1" step="1"/></label>
      <label className="block text-sm font-medium">From (Nairobi)<input className="field" type="datetime-local" name="date_from"/></label>
      <label className="block text-sm font-medium">Through (Nairobi)<input className="field" type="datetime-local" name="date_to"/></label>
      <label className="block text-sm font-medium">Sales source<select className="field" name="source"><option value="">All sources</option><option value="operational">Operational</option><option value="historical">Historical</option></select></label>
      <button className="button self-end">Apply sales filters</button>
    </fieldset></form>
    {page && <><p className="mb-3">{page.total} sales found. {page.total > 0 && `Showing ${offset + 1}–${Math.min(offset + 20, page.total)}.`}</p>
      {!page.items.length ? <p>No sales match these filters.</p> : <div className="overflow-x-auto"><table className="data-table"><thead><tr><th>Sale / time</th><th>SKU</th><th>Quantity</th><th>Unit price</th><th>Source / actor</th></tr></thead><tbody>{page.items.map(row => <tr key={row.id}><td>#{row.id}<span className="block text-xs">{time(row.sale_date)}</span></td><td>{row.sku_snapshot || products.find(item => item.id === row.product_id)?.sku || `Product ${row.product_id}`}</td><td>{number(row.quantity)}</td><td>{row.unit_price === null ? 'Not supplied' : `KES ${number(row.unit_price)}`}</td><td>{row.source}<span className="block text-xs">User {row.actor_id ?? 'unknown (legacy)'}</span></td></tr>)}</tbody></table></div>}
      <div className="flex gap-3 mt-4"><button className="secondary" disabled={state.busy || offset === 0} onClick={() => setOffset(value => Math.max(0, value - 20))}>Previous sales</button><button className="secondary" disabled={state.busy || offset + 20 >= page.total} onClick={() => setOffset(value => value + 20)}>Next sales</button></div>
    </>}
  </section>;
}

export function CsvImport({ token, manager, onUnauthorized }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [accepted, setAccepted] = useState(false);
  const state = useAction(onUnauthorized);
  return <section><h3 className="text-lg font-semibold mb-4">Historical sales CSV import</h3>
    <p className="notice mb-4">Historical imports never change current stock or create stock movements. Maximum 1 MiB / 5,000 data rows; UTF-8 CSV. Preview expires after 30 minutes.</p>
    <p className="text-sm mb-3">Required columns: <code>sku,sale_date,quantity</code>. Optional: <code>unit_price,external_id</code>. Use positive quantities, optional nonnegative KES prices and ISO timestamps with timezone, such as <code>2026-09-01T10:00:00+03:00</code>.</p>
    <p className="text-sm mb-4">Duplicates use product + external ID when supplied, otherwise product + timestamp + quantity + price. Supply distinct external IDs for separate identical transactions. Repeated files are imported once. Rejected rows remain visible below.</p>
    <Feedback {...state}/>
    {!manager ? <p>A manager account is required to import sales.</p> : <>
      <form aria-label="CSV preview form" onSubmit={event => { event.preventDefault(); state.run(async () => {
        if (!file || !file.size || file.size > 1024 * 1024) throw new Error('Choose a CSV file of 1 byte to 1 MiB.');
        const result = await api(`/sales/imports/preview?filename=${encodeURIComponent(file.name)}`, { token, method: 'POST', headers: { 'Content-Type': 'text/csv' }, body: file });
        setPreview(result); setAccepted(false);
      }); }}><fieldset disabled={state.busy} className="space-y-4">
        <label className="block text-sm font-medium">Historical CSV file<input className="field" type="file" accept=".csv,text/csv" required onChange={event => { setFile(event.target.files[0] || null); setPreview(null); setAccepted(false); }}/></label>
        <button className="button">Preview CSV</button>
      </fieldset></form>
      {preview && <section aria-label="Import preview" className="mt-6 space-y-4"><h4 className="font-semibold">{preview.filename} · {preview.status}</h4>
        <p>{preview.valid_count} valid rows; {preview.rejected_count} rejected rows. {preview.status === 'committed' && `${preview.imported_count} previously imported; no additional rows saved.`}</p>
        {preview.preview_truncated && <p>First 100 valid rows shown. All {preview.valid_count} valid rows will be imported.</p>}
        {!!preview.accepted_preview.length && <div className="overflow-x-auto"><table className="data-table"><thead><tr><th>Row</th><th>SKU</th><th>Sale time</th><th>Quantity</th><th>Unit price</th></tr></thead><tbody>{preview.accepted_preview.map(row => <tr key={row.row_number}><td>{row.row_number}</td><td>{row.sku}</td><td>{time(row.sale_date)}</td><td>{row.quantity}</td><td>{row.unit_price ?? 'Not supplied'}</td></tr>)}</tbody></table></div>}
        {!!preview.rejected_rows.length && <section aria-label="Rejected import rows"><h4 className="font-semibold mb-3">Rejected rows</h4><ul className="divide-y">{preview.rejected_rows.map(row => <li key={row.row_number} className="py-3"><strong>Row {row.row_number}: {row.reason}</strong><pre className="text-xs whitespace-pre-wrap break-all mt-1">{JSON.stringify(row.values)}</pre></li>)}</ul></section>}
        {preview.status === 'preview' && preview.valid_count > 0 && <form aria-label="Confirm historical import" onSubmit={event => { event.preventDefault(); state.run(async success => {
          const result = await api(`/sales/imports/${preview.id}/confirm`, { token, method: 'POST', body: JSON.stringify({ preview_version: preview.preview_version, accept_valid_rows: accepted }) });
          setPreview(result); success(`${result.imported_count} historical sales imported. Current stock is unchanged. ${result.rejected_count} rejected rows retained in the report.`);
        }); }}><fieldset disabled={state.busy} className="space-y-3">
          <label className="block text-sm"><input type="checkbox" checked={accepted} onChange={event => setAccepted(event.target.checked)} required/> I reviewed the preview and accept only the valid rows. Rejected rows will not be imported.</label>
          <button className="button" disabled={!accepted}>Confirm historical import</button>
        </fieldset></form>}
      </section>}
    </>}
  </section>;
}
