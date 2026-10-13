import { useCallback, useEffect, useRef, useState } from 'react';
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from './api';

const quantity = value => Number(value).toLocaleString('en-KE', { maximumFractionDigits: 9 });
const time = value => new Date(value.endsWith('Z') ? value : `${value}Z`).toLocaleString('en-KE', { timeZone: 'Africa/Nairobi' });
const labels = { ADEQUATE: 'Adequate', REPLENISH: 'Replenishment risk', OVERSTOCK: 'Overstock', UNASSESSED: 'Unassessed' };

function ResearchComparison({ value }) {
  return <section aria-label="Research model comparison" className="mt-8">
    <h3 className="text-xl font-semibold">Research model comparison</h3>
    <p className="notice my-3">28-day mean baseline (mean_28) selected on validation. Final-test results do not change that selection. {value.limitation}</p>
    <p className="text-sm mb-3">Validation: {value.validation_periods.join('; ')}. Final test: {value.final_test_period}. MAE and RMSE are quantities in units. {value.mape_policy}.</p>
    <div className="overflow-x-auto"><table className="data-table"><thead><tr><th>Model</th><th>Validation MAE</th><th>Validation RMSE</th><th>Final-test MAE</th><th>Final-test RMSE</th></tr></thead><tbody>
      {value.models.map(row => <tr key={row.name}><td>{row.name}{row.selected && <span className="badge">Selected on validation</span>}</td>
        <td>{quantity(row.validation.mae)}</td><td>{quantity(row.validation.rmse)}</td>
        <td>{row.final_test ? quantity(row.final_test.mae) : 'Not final-tested'}</td><td>{row.final_test ? quantity(row.final_test.rmse) : 'Not final-tested'}</td></tr>)}
    </tbody></table></div>
  </section>;
}

function Decision({ record, applicable }) {
  const s = record.snapshot;
  const fields = [['Predicted lead-time demand', s.predicted_lead_time_demand], ['Lead time (days)', s.lead_time_days],
    ['Safety stock', s.safety_stock], ['On hand', s.on_hand], ['Confirmed incoming', s.confirmed_in_transit], ['Allocated', s.allocated],
    ['Inventory position', s.inventory_position], ['Target stock', s.target_stock], ['Shortage / raw reorder', s.shortage],
    ['Suggested reorder', s.suggested_reorder], ['Overstock multiplier', s.overstock_multiplier], ['Overstock threshold', s.overstock_threshold]];
  return <section aria-label="Decision snapshot" className="mt-5 border rounded-lg p-4">
    <h4 className="font-semibold">{labels[record.risk_status]} · immutable decision snapshot</h4>
    {!applicable && <p className="notice my-2">Historical snapshot: the current overview does not consider this decision applicable. Review context, stock and configuration before generating a new snapshot.</p>}
    <p className="text-sm my-2">{s.product_sku} · {s.unit} · as of {record.decision_as_of} · inventory version {record.inventory_version}. Created {time(record.created_at)} (Nairobi).</p>
    <dl className="grid sm:grid-cols-3 gap-3">{fields.map(([label, value]) => <div key={label}><dt className="text-sm text-slate-600">{label}</dt><dd className="font-semibold">{quantity(value)}</dd></div>)}</dl>
    <p className="text-sm mt-3">Position = on hand + confirmed incoming − allocated. Target = sum of daily demand over lead time + safety stock. Reorder = max(0, target − position). Overstock only if position &gt; target × multiplier.</p>
    <p className="text-xs break-all my-3">Forecast {record.forecast_id} · origin {s.forecast_origin} · {s.forecast_horizon} days · {s.model_id} / {s.model_version} · {s.artifact_version} · {record.assumptions_version}. Snapshot {record.id}.</p>
    <ul className="list-disc pl-5 text-sm space-y-1">{s.assumptions.map(item => <li key={item}>{item}</li>)}</ul>
    <p className="notice mt-3">Human review required. These are deterministic risk rules, not probabilities. Recommendations do not execute purchases. Old snapshots retain the stock and configuration used when created.</p>
  </section>;
}

export default function Dashboard({ token, manager, products, onUnauthorized }) {
  const [context, setContext] = useState('operational');
  const [overview, setOverview] = useState(null);
  const [support, setSupport] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [availabilityError, setAvailabilityError] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [productId, setProductId] = useState('');
  const [mappings, setMappings] = useState([]);
  const [forecasts, setForecasts] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [forecastOffset, setForecastOffset] = useState(0);
  const [recOffset, setRecOffset] = useState(0);
  const [forecastId, setForecastId] = useState('');
  const [recommendationId, setRecommendationId] = useState('');
  const [history, setHistory] = useState(null);
  const [acknowledged, setAcknowledged] = useState(false);
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const requests = useRef({});
  const product = products.find(item => String(item.id) === productId);
  const forecast = forecasts.find(item => item.id === forecastId);
  const recommendation = recommendations.find(item => item.id === recommendationId);
  const mapping = mappings[0];
  const mapped = mapping?.enabled && mapping.product_sku === product?.sku && mapping.unit === product?.unit;
  const fail = useCallback(err => { if (err.status === 401) onUnauthorized(); else setError(err.message); }, [onUnauthorized]);

  useEffect(() => {
    let active = true;
    setOverview(null);
    api(`/dashboard?context=${context}`, { token }).then(value => { if (active) setOverview(value); }).catch(err => { if (active) fail(err); });
    return () => { active = false; };
  }, [token, context, products, refresh, fail]);
  useEffect(() => {
    let active = true;
    Promise.allSettled([api('/forecast-support', { token }), api('/research/models', { token })]).then(results => {
      if (!active) return;
      const [forecastResult, researchResult] = results;
      if (forecastResult.status === 'fulfilled') { setSupport(forecastResult.value); setAvailabilityError(''); }
      else { setSupport(null); setAvailabilityError(forecastResult.reason.message); if (forecastResult.reason.status === 401) onUnauthorized(); }
      if (researchResult.status === 'fulfilled') setComparison(researchResult.value);
      else { setComparison(null); fail(researchResult.reason); }
    });
    return () => { active = false; };
  }, [token, refresh, fail, onUnauthorized]);
  useEffect(() => {
    let active = true;
    setHistory(null);
    if (!productId) { setMappings([]); setForecasts([]); setRecommendations([]); return; }
    Promise.all([api(`/products/${productId}/forecast-mappings?limit=1`, { token }),
      api(`/forecasts/${productId}?offset=${forecastOffset}&limit=20`, { token }),
      api(`/recommendations/${productId}?offset=${recOffset}&limit=20`, { token })]).then(([maps, fc, recs]) => {
      if (!active) return;
      setMappings(maps); setForecasts(fc); setRecommendations(recs);
      setForecastId(value => fc.some(row => row.id === value) ? value : fc[0]?.id || '');
      setRecommendationId(value => recs.some(row => row.id === value) ? value : recs[0]?.id || '');
    }).catch(err => { if (active) fail(err); });
    return () => { active = false; };
  }, [token, productId, forecastOffset, recOffset, refresh, fail]);
  useEffect(() => {
    let active = true;
    setHistory(null);
    if (forecastId && productId) api(`/forecasts/${productId}/${forecastId}/history`, { token }).then(value => { if (active) setHistory(value); }).catch(err => { if (active) fail(err); });
    return () => { active = false; };
  }, [token, productId, forecastId, refresh, fail]);

  async function write(name, path, values) {
    setBusy(true); setError(''); setSuccess('');
    const fingerprint = JSON.stringify({ path, values });
    if (!requests.current[name] || requests.current[name].fingerprint !== fingerprint)
      requests.current[name] = { fingerprint, key: crypto.randomUUID() };
    try {
      await api(path, { token, method: 'POST', body: JSON.stringify(name === 'mapping' ? values : { ...values, request_key: requests.current[name].key }) });
      delete requests.current[name];
      setForecastOffset(0); setRecOffset(0); setForecastId(''); setRecommendationId('');
      setSuccess(`${name === 'mapping' ? 'Research series mapping' : name === 'forecast' ? 'Forecast snapshot' : 'Recommendation snapshot'} saved.`);
      setRefresh(value => value + 1);
    } catch (err) { fail(err); }
    finally { setBusy(false); }
  }
  const chart = history && forecast ? [...history.points.map(point => ({ date: point.date, historical: point.quantity })),
    ...forecast.points.map(point => ({ date: point.forecast_date, forecast: Number(point.predicted_quantity) }))] : [];
  return <div>
    <h3 className="text-2xl font-semibold">Inventory decision dashboard</h3>
    <p className="notice my-4">UCI Online Retail II forecasts use UK retail data and have not been validated for Kenyan businesses. The frozen 28-day mean baseline is selected on validation. Compatible research history ends 2011-11-10; current forecasts are unavailable.</p>
    <div className="flex flex-wrap gap-3 items-end mb-4">
      <label className="text-sm">Decision context<select className="field" value={context} disabled={busy} onChange={e => { setContext(e.target.value); setAcknowledged(false); }}><option value="operational">Current inventory</option><option value="research_demo">UK historical research scenario (2011-11-11)</option></select></label>
      <button className="secondary" disabled={busy} onClick={() => { setError(''); setRefresh(value => value + 1); }}>Refresh dashboard</button>
    </div>
    {error && <p role="alert" className="text-red-700 my-3">{error}</p>}
    {availabilityError && <p role="alert" className="text-amber-800 my-3">Forecasting unavailable: {availabilityError}. Inventory remains available.</p>}
    {success && <p role="status" className="text-green-800 my-3">{success}</p>}
    {overview?.context === context ? <section aria-label="Inventory overview">
      <p className="text-sm mb-3">{overview.limitation} Decision date: {overview.decision_as_of}.</p>
      <div className="grid sm:grid-cols-5 gap-3">{[['Active products', overview.total_active_products], ...Object.entries(overview.status_counts).map(([key, value]) => [labels[key], value])].map(([label, value]) => <div key={label} className="rounded-lg bg-slate-100 p-4"><span className="block text-sm">{label}</span><strong className="text-2xl">{value}</strong></div>)}</div>
      {overview.products.length === 0 ? <p className="my-4">No active products. Add products before reviewing stock decisions.</p> : <div className="overflow-x-auto my-4"><table className="data-table"><thead><tr><th>Product</th><th>On hand</th><th>Incoming</th><th>Allocated</th><th>Position</th><th>Current scenario status</th></tr></thead><tbody>{overview.products.map(item => <tr key={item.product_id}><td>{item.name}<span className="block text-xs">{item.sku} · {item.unit}</span></td><td>{quantity(item.on_hand)}</td><td>{quantity(item.confirmed_in_transit)}</td><td>{quantity(item.allocated)}</td><td>{quantity(item.inventory_position)}</td><td>{labels[item.risk_status]}<span className="block text-xs">{item.forecastability}</span></td></tr>)}</tbody></table></div>}
      <p className="text-sm">Unassessed means no valid snapshot for this context and stock/configuration version. It does not mean adequate stock.</p>
    </section> : <p role="status">Loading stock overview…</p>}
    <section aria-label="Product forecasts and decisions" className="mt-8">
      <label className="block font-medium">Decision product<select className="field" value={productId} disabled={busy} onChange={e => {
        setProductId(e.target.value); setForecastOffset(0); setRecOffset(0); setForecastId(''); setRecommendationId(''); setForecasts([]); setRecommendations([]); setMappings([]); setError(''); setSuccess(''); setAcknowledged(false);
      }}><option value="">Select product</option>{products.map(item => <option key={item.id} value={item.id}>{item.name} · {item.sku}{!item.active && ' (archived; history only)'}</option>)}</select></label>
      {product && <>
        <p className="my-3">{mapped ? `Documented UK research series: ${mapping.series_sku}. Reason: ${mapping.reason}` : 'Forecast unavailable — insufficient or unsupported historical series. Explicit manager mapping required.'}</p>
        {manager && product.active && context === 'research_demo' && <fieldset disabled={busy} className="border rounded-lg p-4 space-y-3">
          <legend className="font-semibold">Historical research demonstration</legend>
          <p className="text-sm">Current illustrative inventory is applied to a historical 2011-11-11 scenario. It is not measured 2011 stock or a present-day purchasing recommendation. Use synthetic test inventory.</p>
          <label className="block text-sm"><input type="checkbox" checked={acknowledged} onChange={e => setAcknowledged(e.target.checked)}/> I acknowledge the UK historical research scenario and illustrative stock.</label>
          {support && product.unit === 'unit' ? <form key={`${productId}:${mapping?.id || 'new'}`} aria-label="Forecast mapping form" onSubmit={e => {
            e.preventDefault(); const data = new FormData(e.currentTarget);
            write('mapping', `/products/${productId}/forecast-mappings`, { series_sku: data.get('series_sku'), reason: data.get('reason'), enabled: data.get('enabled') === 'true', confirm_research_demo: true });
          }} className="grid sm:grid-cols-2 gap-3">
            <label className="text-sm">Supported UK series<select className="field" name="series_sku" defaultValue={mapping?.series_sku || support.supported_series[0]}>{support.supported_series.map(sku => <option key={sku}>{sku}</option>)}</select></label>
            <label className="text-sm">Mapping reason<input className="field" name="reason" required minLength={3} maxLength={240}/></label>
            <label className="text-sm">Mapping state<select className="field" name="enabled"><option value="true">Enabled</option><option value="false">Disabled</option></select></label>
            <button className="secondary self-end" disabled={!acknowledged}>Save research mapping</button>
          </form> : <p className="text-sm">Mapping requires available verified research support and product unit “unit”; kg and other units cannot be converted silently.</p>}
          <form aria-label="Forecast generation form" className="flex gap-3 items-end" onSubmit={e => {
            e.preventDefault(); const data = new FormData(e.currentTarget);
            write('forecast', `/forecasts/${productId}/generate`, { forecast_origin: support.available_origin, horizon: Number(data.get('horizon')), context, confirm_research_demo: true });
          }}><label className="text-sm">Forecast horizon (days)<input className="field" name="horizon" type="number" required min={1} max={28} step={1} defaultValue={28}/></label>
            <button className="button" disabled={!mapped || !support || !acknowledged}>Generate forecast snapshot</button></form>
          <p className="text-sm">Origin {support?.available_origin || 'unavailable'}, unchanged historical dates. Lead time {product.lead_time_days} days must fit inside the forecast horizon (maximum 28).</p>
        </fieldset>}
        <h4 className="font-semibold mt-5">Stored forecasts</h4>
        {forecasts.length === 0 ? <p className="my-2">No forecast snapshots on this page.</p> : <label className="text-sm">Forecast snapshot<select className="field" value={forecastId} onChange={e => setForecastId(e.target.value)}>{forecasts.map(row => <option key={row.id} value={row.id}>{time(row.created_at)} · origin {row.forecast_origin} · {row.horizon} days · {row.id}</option>)}</select></label>}
        <div className="flex gap-2 my-2"><button className="secondary" disabled={busy || forecastOffset === 0} onClick={() => setForecastOffset(value => value - 20)}>Previous forecasts</button><button className="secondary" disabled={busy || forecasts.length < 20} onClick={() => setForecastOffset(value => value + 20)}>Next forecasts</button></div>
        {forecast && <>
          <p className="text-sm break-all">{forecast.context} · UK series {forecast.series_sku} · {forecast.model_id} / {forecast.model_version} · {forecast.artifact_version}.</p>
          {chart.length > 0 && <div className="h-80 mt-3" aria-label="Historical UK demand and stored forecast chart"><ResponsiveContainer width="100%" height="100%" minWidth={0}><LineChart data={chart} margin={{ top: 15, right: 20, left: 10, bottom: 5 }} accessibilityLayer><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date" minTickGap={40}/><YAxis/><Tooltip/><Legend/><Line dataKey="historical" name="Historical UK demand (units)" stroke="#64748b" dot={false}/><Line dataKey="forecast" name="Stored mean_28 forecast (units)" stroke="#0284c7" dot={false}/></LineChart></ResponsiveContainer></div>}
          <details className="my-3"><summary className="cursor-pointer">Daily forecast quantities (accessible table)</summary><table className="data-table"><thead><tr><th>Date</th><th>Horizon day</th><th>Demand ({forecast.unit})</th></tr></thead><tbody>{forecast.points.map(point => <tr key={point.horizon_day}><td>{point.forecast_date}</td><td>{point.horizon_day}</td><td>{quantity(point.predicted_quantity)}</td></tr>)}</tbody></table></details>
          {manager && product.active && <button className="button" disabled={busy || !support || !mapped || context !== 'research_demo' || !acknowledged} onClick={() => write('recommendation', `/recommendations/${productId}/generate`, { forecast_id: forecast.id, decision_as_of: support.research_decision_as_of, context, confirm_research_demo: true })}>Generate recommendation snapshot</button>}
        </>}
        <h4 className="font-semibold mt-5">Stored recommendations</h4>
        {recommendations.length === 0 ? <p className="my-2">No recommendation snapshots on this page.</p> : <label className="text-sm">Recommendation snapshot<select className="field" value={recommendationId} onChange={e => setRecommendationId(e.target.value)}>{recommendations.map(row => <option key={row.id} value={row.id}>{time(row.created_at)} · {labels[row.risk_status]} · {row.id}</option>)}</select></label>}
        <div className="flex gap-2 my-2"><button className="secondary" disabled={busy || recOffset === 0} onClick={() => setRecOffset(value => value - 20)}>Previous recommendations</button><button className="secondary" disabled={busy || recommendations.length < 20} onClick={() => setRecOffset(value => value + 20)}>Next recommendations</button></div>
        {recommendation && <Decision record={recommendation} applicable={overview?.context === context && overview.products.some(row => row.recommendation_id === recommendation.id)}/>}
      </>}
    </section>
    {comparison && <ResearchComparison value={comparison}/>}
  </div>;
}
