import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import { api } from './api';
import { CsvImport, SaleEntry, SalesHistory } from './SalesPages';
const Dashboard = lazy(() => import('./Dashboard'));

const decimal = value => Number(value).toLocaleString('en-KE', { maximumFractionDigits: 3 });
const fieldNames = ['sku', 'name', 'category_id', 'unit', 'lead_time_days', 'safety_stock', 'overstock_multiplier'];

async function allPages(path, token) {
  const result = [];
  for (let offset = 0; ; offset += 100) {
    const page = await api(`${path}?include_archived=true&offset=${offset}&limit=100`, { token });
    result.push(...page);
    if (page.length < 100) return result;
  }
}

function Field({ label, ...props }) {
  return <label className="block text-sm font-medium">{label}<input className="field" {...props}/></label>;
}

function CategoryForm({ item, busy, onSave, onCancel }) {
  return <form aria-label="Category form" className="space-y-4" onSubmit={event => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    onSave({ name: data.get('name'), active: data.has('active') });
  }}><fieldset disabled={busy} className="space-y-4">
    <h3 className="text-lg font-semibold">{item ? 'Edit category' : 'New category'}</h3>
    <Field label="Category name" name="name" required maxLength={120} defaultValue={item?.name || ''}/>
    <label className="block text-sm"><input type="checkbox" name="active" defaultChecked={item?.active ?? true}/> Active category</label>
    <div className="flex gap-3"><button className="button">Save category</button>{item && <button type="button" className="secondary" onClick={onCancel}>Cancel</button>}</div>
  </fieldset></form>;
}

function ProductForm({ item, categories, busy, onSave, onCancel }) {
  return <form aria-label="Product form" onSubmit={event => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const payload = Object.fromEntries(fieldNames.map(key => [key, data.get(key)]));
    payload.category_id = Number(payload.category_id);
    payload.lead_time_days = Number(payload.lead_time_days);
    payload.active = data.has('active');
    if (!item) payload.initial_stock = data.get('initial_stock');
    onSave(payload);
  }}><fieldset disabled={busy} className="space-y-4">
    <h3 className="text-lg font-semibold">{item ? 'Edit product' : 'New product'}</h3>
    <div className="grid sm:grid-cols-2 gap-4">
      <Field label="SKU" name="sku" required maxLength={64} pattern="[A-Za-z0-9][A-Za-z0-9._-]*" defaultValue={item?.sku || ''}/>
      <Field label="Product name" name="name" required maxLength={160} defaultValue={item?.name || ''}/>
      <label className="block text-sm font-medium">Category<select className="field" name="category_id" required defaultValue={item?.category_id || ''}><option value="">Select a category</option>{categories.map(category => <option key={category.id} value={category.id} disabled={!category.active}>{category.name}{!category.active && ' (archived)'}</option>)}</select></label>
      <Field label="Unit" name="unit" required maxLength={30} defaultValue={item?.unit || 'unit'}/>
      <Field label="Lead time (days)" name="lead_time_days" type="number" required min={1} max={365} step={1} defaultValue={item?.lead_time_days || 7}/>
      <Field label="Safety stock" name="safety_stock" type="number" required min={0} step="0.001" defaultValue={item?.safety_stock || 0}/>
      <Field label="Overstock multiplier" name="overstock_multiplier" type="number" required min="1.001" max={100} step="0.001" defaultValue={item?.overstock_multiplier || 2}/>
      {!item && <Field label="Opening stock" name="initial_stock" type="number" required min={0} step="0.001" defaultValue={0}/>}
    </div>
    <p className="text-sm text-slate-600">Overstock threshold = forecast demand over lead time + safety stock, multiplied by this value. Review forecast decisions on the Dashboard page.</p>
    <label className="block text-sm"><input type="checkbox" name="active" defaultChecked={item?.active ?? true}/> Active product</label>
    <div className="flex gap-3"><button className="button">Save product</button>{item && <button type="button" className="secondary" onClick={onCancel}>Cancel</button>}</div>
  </fieldset></form>;
}

function StockForm({ product, busy, onSave, onCancel }) {
  const stock = product.inventory;
  return <form aria-label="Inventory form" className="space-y-4" onSubmit={event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    onSave({ ...values, version: stock.version });
  }}><fieldset disabled={busy} className="space-y-4">
    <h3 className="text-lg font-semibold">Adjust stock · {product.name}</h3>
    <p className="text-sm text-slate-600">Enter the current quantities in {product.unit}. Every adjustment records your account and reason.</p>
    <div className="grid sm:grid-cols-3 gap-4">
      <Field label="On-hand stock" name="on_hand" type="number" min={0} step="0.001" required defaultValue={stock.on_hand}/>
      <Field label="Confirmed incoming stock" name="confirmed_in_transit" type="number" min={0} step="0.001" required defaultValue={stock.confirmed_in_transit}/>
      <Field label="Allocated stock" name="allocated" type="number" min={0} step="0.001" required defaultValue={stock.allocated}/>
    </div>
    <Field label="Adjustment reason" name="reason" required minLength={3} maxLength={240}/>
    <div className="flex gap-3"><button className="button">Save stock adjustment</button><button className="secondary" type="button" onClick={onCancel}>Cancel</button></div>
  </fieldset></form>;
}

export default function Workspace({ session, onUnauthorized }) {
  const [tab, setTab] = useState('Products');
  const [categories, setCategories] = useState([]);
  const [products, setProducts] = useState([]);
  const [editCategory, setEditCategory] = useState(null);
  const [editProduct, setEditProduct] = useState(null);
  const [stockId, setStockId] = useState(null);
  const [movements, setMovements] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [categoryFormKey, setCategoryFormKey] = useState(0);
  const [productFormKey, setProductFormKey] = useState(0);
  const manager = session.user.role === 'manager';
  const token = session.access_token;
  const fail = useCallback(err => {
    if (err.status === 401) onUnauthorized();
    else setError(err.message);
  }, [onUnauthorized]);
  const load = useCallback(async () => {
    const [cats, items] = await Promise.all([allPages('/categories', token), allPages('/products', token)]);
    setCategories(cats); setProducts(items); setLoaded(true);
  }, [token]);
  useEffect(() => {
    let active = true;
    load().catch(err => { if (active) fail(err); });
    return () => { active = false; };
    // The session token identifies this mounted workspace; callback identity is incidental.
  }, [load]);
  async function perform(action) {
    setBusy(true); setError('');
    try { await action(); }
    catch (err) { fail(err); }
    finally { setBusy(false); }
  }
  async function saveCategory(payload) {
    await perform(async () => {
      await api(editCategory ? `/categories/${editCategory.id}` : '/categories', { token, method: editCategory ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      await load(); setEditCategory(null); setCategoryFormKey(value => value + 1);
    });
  }
  async function saveProduct(payload) {
    await perform(async () => {
      await api(editProduct ? `/products/${editProduct.id}` : '/products', { token, method: editProduct ? 'PUT' : 'POST', body: JSON.stringify(payload) });
      await load(); setEditProduct(null); setProductFormKey(value => value + 1);
    });
  }
  async function archive(type, item) {
    await perform(async () => {
      await api(`/${type}/${item.id}`, { token, method: 'DELETE' }); await load();
      setEditCategory(null); setEditProduct(null); setStockId(null);
    });
  }
  const visibleProducts = products.filter(item => showArchived || item.active);
  const visibleCategories = categories.filter(item => showArchived || item.active);
  const stockProduct = products.find(item => item.id === stockId);
  return <div>
    <nav aria-label="Workspace pages" className="flex flex-wrap gap-2 border-b border-slate-200 pb-4 mb-6">{['Dashboard', 'Products', 'Categories', 'Inventory', 'Sales entry', 'Sales history', 'CSV import'].map(page => <button type="button" key={page} aria-current={tab === page ? 'page' : undefined} className={tab === page ? 'button' : 'secondary'} onClick={() => { setTab(page); setMovements(null); }}>{page}</button>)}</nav>
    {!manager && <p className="notice mb-4">Research account: you can view catalog, stock, movements and sales history. A manager is required to make changes.</p>}
    {error && <p role="alert" className="text-red-700 mb-4">{error}</p>}
    <div className="flex flex-wrap items-center justify-between gap-4 mb-6"><label className="text-sm"><input type="checkbox" checked={showArchived} onChange={event => setShowArchived(event.target.checked)}/> Show archived records</label><button className="secondary" disabled={busy} onClick={() => perform(load)}>Reload records</button></div>
    {!loaded && <p role="status">Loading inventory workspace…</p>}
    {loaded && <>
      {tab === 'Dashboard' && <Suspense fallback={<p role="status">Loading dashboard…</p>}><Dashboard token={token} manager={manager} products={products} onUnauthorized={onUnauthorized}/></Suspense>}
      {tab === 'Sales entry' && <SaleEntry token={token} manager={manager} products={products} onUnauthorized={onUnauthorized} onInventoryChanged={load}/>}
      {tab === 'Sales history' && <SalesHistory token={token} products={products} onUnauthorized={onUnauthorized}/>}
      {tab === 'CSV import' && <CsvImport token={token} manager={manager} onUnauthorized={onUnauthorized}/>}
      {tab === 'Categories' && <div className="grid md:grid-cols-2 gap-8">
        <div><h3 className="text-lg font-semibold mb-4">Categories</h3>{visibleCategories.length === 0 && <p>No categories yet. Add a category to organize products.</p>}
          <ul className="divide-y divide-slate-200">{visibleCategories.map(item => <li key={item.id} className="py-4 flex flex-wrap justify-between gap-3"><span>{item.name}{!item.active && <span className="badge">Archived</span>}</span>{manager && <span className="flex gap-2"><button className="secondary" disabled={busy} onClick={() => setEditCategory(item)}>Edit {item.name}</button>{item.active && <button className="secondary" disabled={busy} onClick={() => archive('categories', item)}>Archive {item.name}</button>}</span>}</li>)}</ul>
        </div>{manager && <CategoryForm key={editCategory?.id || `new-${categoryFormKey}`} item={editCategory} busy={busy} onSave={saveCategory} onCancel={() => setEditCategory(null)}/>}
      </div>}
      {tab === 'Products' && <>
        <h3 className="text-lg font-semibold mb-4">Products</h3>
        {visibleProducts.length === 0 ? <p className="mb-6">No products yet. Create a category, then add your first product.</p> : <div className="overflow-x-auto mb-8"><table className="data-table"><thead><tr><th>Product / SKU</th><th>Category</th><th>Stock</th><th>Lead time</th><th>Safety stock</th><th>Overstock multiplier</th>{manager && <th>Actions</th>}</tr></thead><tbody>{visibleProducts.map(item => <tr key={item.id}><td>{item.name}<span className="block text-xs text-slate-500">{item.sku} · {item.unit}{!item.active && ' · Archived'}</span></td><td>{categories.find(cat => cat.id === item.category_id)?.name}</td><td>{decimal(item.inventory.on_hand)}</td><td>{item.lead_time_days} days</td><td>{decimal(item.safety_stock)}</td><td>× {decimal(item.overstock_multiplier)}</td>{manager && <td><div className="flex gap-2"><button className="secondary" disabled={busy} onClick={() => setEditProduct(item)}>Edit {item.name}</button>{item.active && <button className="secondary" disabled={busy} onClick={() => archive('products', item)}>Archive {item.name}</button>}</div></td>}</tr>)}</tbody></table></div>}
        {manager && (categories.some(item => item.active) ? <ProductForm key={editProduct?.id || `new-${productFormKey}`} item={editProduct} categories={categories} busy={busy} onSave={saveProduct} onCancel={() => setEditProduct(null)}/> : <p className="notice">Add an active category on the Categories page before creating products.</p>)}
      </>}
      {tab === 'Inventory' && <>
        <h3 className="text-lg font-semibold mb-4">Current inventory</h3>
        {visibleProducts.length === 0 ? <p>No products available for stock monitoring.</p> : <div className="overflow-x-auto mb-8"><table className="data-table"><thead><tr><th>Product</th><th>On hand</th><th>Confirmed incoming</th><th>Allocated</th><th>Actions</th></tr></thead><tbody>{visibleProducts.map(item => <tr key={item.id}><td>{item.name}<span className="block text-xs text-slate-500">{item.sku} · {item.unit}{!item.active && ' · Archived'}</span></td><td>{decimal(item.inventory.on_hand)}</td><td>{decimal(item.inventory.confirmed_in_transit)}</td><td>{decimal(item.inventory.allocated)}</td><td><div className="flex flex-wrap gap-2">{manager && item.active && <button className="secondary" disabled={busy} onClick={() => { setStockId(item.id); setMovements(null); }}>Adjust {item.name}</button>}<button className="secondary" disabled={busy} onClick={() => perform(async () => { const rows = await api(`/products/${item.id}/movements`, { token }); setMovements({ product: item, rows }); setStockId(null); })}>History for {item.name}</button></div></td></tr>)}</tbody></table></div>}
        {manager && stockProduct?.active && <StockForm key={`${stockProduct.id}:${stockProduct.inventory.version}`} product={stockProduct} busy={busy} onCancel={() => setStockId(null)} onSave={payload => perform(async () => { await api(`/products/${stockId}/inventory`, { token, method: 'PUT', body: JSON.stringify(payload) }); await load(); setStockId(null); })}/>}
        {movements && <section aria-label="Stock history"><h3 className="text-lg font-semibold mb-4">Stock history · {movements.product.name}</h3><p className="text-sm text-slate-500 mb-3">Latest 100 entries. Timestamps shown in Nairobi time.</p><div className="overflow-x-auto"><table className="data-table"><thead><tr><th>Time</th><th>Reason / actor</th><th>On hand</th><th>Incoming</th><th>Allocated</th></tr></thead><tbody>{movements.rows.map(row => <tr key={row.id}><td>{new Date(`${row.created_at}Z`).toLocaleString('en-KE', { timeZone: 'Africa/Nairobi' })}</td><td>{row.reason}<span className="block text-xs text-slate-500">{row.kind} · User {row.actor_id}</span></td><td>{decimal(row.on_hand_before)} → {decimal(row.on_hand_after)}</td><td>{decimal(row.in_transit_before)} → {decimal(row.in_transit_after)}</td><td>{decimal(row.allocated_before)} → {decimal(row.allocated_after)}</td></tr>)}</tbody></table></div></section>}
      </>}
    </>}
  </div>;
}
