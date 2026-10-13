import { readFileSync } from 'node:fs';
import { afterEach, expect, test, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import Dashboard from './Dashboard';

afterEach(() => { cleanup(); vi.restoreAllMocks(); });
// The API mock tests UI behavior; research values come directly from preserved records.
const validation = JSON.parse(readFileSync('../docs/research/results/validation.json', 'utf8'));
const final = JSON.parse(readFileSync('../docs/research/results/final-test.json', 'utf8'));
const comparison = { selected: 'mean_28', limitation: 'UK retail; not validated for Kenyan retail.', validation_periods: ['2011 validation'],
  final_test_period: '2011 final test', mape_policy: 'MAPE omitted for zeros', models: validation.ranking.map(name => ({ name, selected: name === 'mean_28', validation: validation.scores[name], final_test: final.scores[name] })) };
const product = { id: 1, name: 'Synthetic scenario', sku: 'DEMO', unit: 'unit', active: true, lead_time_days: 3 };
const mapping = { id: 'm1', product_sku: 'DEMO', unit: 'unit', series_sku: '20728', enabled: true, reason: 'Synthetic test mapping' };
const forecast = { id: 'f1', created_at: '2026-10-01T00:00:00', product_sku: 'DEMO', series_sku: '20728', context: 'research_demo',
  model_id: 'mean_28', model_version: 'retail-demand-v1', artifact_version: 'sha256:fixture', forecast_origin: '2011-11-10', horizon: 3, unit: 'unit',
  points: [1, 2, 3].map(n => ({ horizon_day: n, forecast_date: `2011-11-${10 + n}`, predicted_quantity: '2' })) };
const recommendation = { id: 'r1', forecast_id: 'f1', created_at: '2026-10-01T00:00:01', risk_status: 'REPLENISH',
  decision_as_of: '2011-11-11', inventory_version: 1, assumptions_version: 'inventory-rules-v1', snapshot: {
    product_sku: 'DEMO', unit: 'unit', predicted_lead_time_demand: '6', lead_time_days: 3, safety_stock: '4', on_hand: '5', confirmed_in_transit: '3',
    allocated: '2', inventory_position: '6', target_stock: '10', shortage: '4', suggested_reorder: '4', overstock_multiplier: '2', overstock_threshold: '20',
    forecast_origin: '2011-11-10', forecast_horizon: 3, model_id: 'mean_28', model_version: 'retail-demand-v1', artifact_version: 'sha256:fixture', assumptions: ['Synthetic test stock; human review required.'] } };
const response = (value, status = 200) => ({ ok: status < 400, status, json: async () => value });
function setup({ products = [product], maps = [], forecasts = [], recommendations = [], manager = true, unavailable = false, mutate } = {}) {
  const state = { maps, forecasts, recommendations };
  const onUnauthorized = vi.fn();
  const mock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (url, options) => {
    if (options.method === 'POST') return mutate(url, options, state);
    if (url.includes('/dashboard?')) return response({ context: url.includes('research_demo') ? 'research_demo' : 'operational', total_active_products: products.length, products: [], decision_as_of: '2026-10-01',
      limitation: 'Unassessed is not safe.', status_counts: { ADEQUATE: 0, REPLENISH: 0, OVERSTOCK: 0, UNASSESSED: products.length } });
    if (url.endsWith('/forecast-support')) return unavailable ? response({ detail: 'Forecast artifact missing' }, 503) : response({ supported_series: ['20728'], available_origin: '2011-11-10', research_decision_as_of: '2011-11-11' });
    if (url.endsWith('/research/models')) return response(comparison);
    if (url.includes('/forecast-mappings')) return response(state.maps);
    if (url.endsWith('/history')) return response({ points: [{ date: '2011-11-10', quantity: 2 }] });
    if (url.includes('/forecasts/1?')) return response(state.forecasts);
    if (url.includes('/recommendations/1?')) return response(state.recommendations);
    throw new Error(`Unexpected URL ${url}`);
  });
  render(<Dashboard token="test-token" manager={manager} products={products} onUnauthorized={onUnauthorized}/>);
  return { mock, onUnauthorized };
}
async function choose() {
  await screen.findByRole('region', { name: 'Research model comparison' });
  fireEvent.change(screen.getByLabelText('Decision product'), { target: { value: '1' } });
  await screen.findByText(/Explicit manager mapping required|Documented UK research series/);
}
function scenario() { fireEvent.change(screen.getByLabelText('Decision context'), { target: { value: 'research_demo' } }); }

test('empty dashboard shows limitation and genuine separately labelled validation/final metrics', async () => {
  setup({ products: [] });
  expect(await screen.findByText('No active products. Add products before reviewing stock decisions.')).toBeInTheDocument();
  expect(await screen.findByText('4.753635204')).toBeInTheDocument();
  expect(screen.getByText('5.335034014')).toBeInTheDocument();
  expect(screen.getByText('Selected on validation')).toBeInTheDocument();
  expect(screen.getByText('Validation MAE')).toBeInTheDocument();
  expect(screen.getByText('Final-test MAE')).toBeInTheDocument();
  expect(screen.getByLabelText('Decision context')).toHaveValue('operational');
});
test('unsupported product cannot generate or implicitly map', async () => {
  const { mock } = setup(); await choose(); scenario();
  expect(screen.getByRole('button', { name: 'Generate forecast snapshot' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Save research mapping' })).toBeDisabled();
  expect(mock.mock.calls.every(([, options]) => options.method !== 'POST')).toBe(true);
});
test('researcher reads evidence and cannot see mutation forms', async () => {
  setup({ manager: false, maps: [mapping], forecasts: [forecast], recommendations: [recommendation] });
  await choose(); scenario();
  expect(await screen.findByRole('region', { name: 'Decision snapshot' })).toHaveTextContent('Inventory position');
  expect(screen.queryByRole('button', { name: 'Generate forecast snapshot' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Generate recommendation snapshot' })).not.toBeInTheDocument();
});
test('stored snapshot displays all formula components and immutable provenance', async () => {
  setup({ maps: [mapping], recommendations: [recommendation] }); await choose();
  const section = await screen.findByRole('region', { name: 'Decision snapshot' });
  for (const label of ['Predicted lead-time demand', 'Lead time (days)', 'Safety stock', 'On hand', 'Confirmed incoming', 'Allocated',
    'Inventory position', 'Target stock', 'Shortage / raw reorder', 'Suggested reorder', 'Overstock threshold', 'inventory-rules-v1'])
    expect(section).toHaveTextContent(label);
  expect(section).toHaveTextContent('not probabilities');
  expect(section).toHaveTextContent('current overview does not consider this decision applicable');
});
test('manager mapping requires acknowledgement and sends supported series/reason', async () => {
  const { mock } = setup({ mutate: (_, options, state) => { state.maps = [mapping]; return response(mapping, 201); } });
  await choose(); scenario();
  fireEvent.click(screen.getByLabelText('I acknowledge the UK historical research scenario and illustrative stock.'));
  fireEvent.change(screen.getByLabelText('Mapping reason'), { target: { value: 'Synthetic test mapping' } });
  fireEvent.submit(screen.getByRole('form', { name: 'Forecast mapping form' }));
  expect(await screen.findByText('Research series mapping saved.')).toBeInTheDocument();
  const body = JSON.parse(mock.mock.calls.find(([, options]) => options.method === 'POST')[1].body);
  expect(body).toEqual({ series_sku: '20728', enabled: true, reason: 'Synthetic test mapping', confirm_research_demo: true });
});
test('failed forecast retry preserves UUID and displays actual server error', async () => {
  const { mock } = setup({ maps: [mapping], mutate: () => response({ detail: 'Forecast artifact incompatible' }, 503) });
  await choose(); await screen.findByText(/Documented UK research series/); scenario();
  fireEvent.click(screen.getByLabelText('I acknowledge the UK historical research scenario and illustrative stock.'));
  fireEvent.submit(screen.getByRole('form', { name: 'Forecast generation form' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Forecast artifact incompatible');
  fireEvent.submit(screen.getByRole('form', { name: 'Forecast generation form' }));
  await waitFor(() => expect(mock.mock.calls.filter(([, options]) => options.method === 'POST')).toHaveLength(2));
  const bodies = mock.mock.calls.filter(([, options]) => options.method === 'POST').map(([, options]) => JSON.parse(options.body));
  expect(bodies[0]).toEqual(bodies[1]);
  expect(bodies[0]).toMatchObject({ forecast_origin: '2011-11-10', horizon: 28, context: 'research_demo', confirm_research_demo: true });
});
test('unavailable artifact preserves inventory overview and disables writes', async () => {
  setup({ unavailable: true }); await choose(); scenario();
  expect(await screen.findByRole('alert')).toHaveTextContent('Inventory remains available');
  expect(screen.getByRole('region', { name: 'Inventory overview' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Generate forecast snapshot' })).toBeDisabled();
});
test('manager recommendation uses selected immutable forecast and explicit historical date', async () => {
  const { mock } = setup({ maps: [mapping], forecasts: [forecast], mutate: (_, options, state) => { state.recommendations = [recommendation]; return response(recommendation, 201); } });
  await choose(); await screen.findByLabelText('Forecast snapshot'); scenario();
  fireEvent.click(screen.getByLabelText('I acknowledge the UK historical research scenario and illustrative stock.'));
  fireEvent.click(screen.getByRole('button', { name: 'Generate recommendation snapshot' }));
  expect(await screen.findByText('Recommendation snapshot saved.')).toBeInTheDocument();
  expect(JSON.parse(mock.mock.calls.find(([, options]) => options.method === 'POST')[1].body)).toMatchObject({ forecast_id: 'f1', decision_as_of: '2011-11-11', context: 'research_demo' });
});
test('authentication expiry returns control to sign-in', async () => {
  const { onUnauthorized } = setup({ maps: [mapping], mutate: () => response({ detail: 'Session expired' }, 401) });
  await choose(); await screen.findByText(/Documented UK research series/); scenario();
  fireEvent.click(screen.getByLabelText('I acknowledge the UK historical research scenario and illustrative stock.'));
  fireEvent.submit(screen.getByRole('form', { name: 'Forecast generation form' }));
  await waitFor(() => expect(onUnauthorized).toHaveBeenCalled());
});
