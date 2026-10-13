"""Bounded HTTP latency measurements; synthetic fixtures, no commercial capacity claims."""
import json
import os
import platform
import secrets
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    account=json.loads((ROOT/'.local/verification-account.json').read_text())
    rows=[]
    start=time.perf_counter()
    with httpx.Client(base_url='http://localhost:8000/api/v1',timeout=60) as client:
        result=client.post('/auth/login',json=account);result.raise_for_status()
        headers={'Authorization':'Bearer '+result.json()['access_token']}
        def call(method,path,body=None):
            r=client.request(method,path,headers=headers,json=body);r.raise_for_status();return r.json() if r.status_code!=204 else None
        category=call('POST','/categories',{'name':'Phase6 load fixture '+secrets.token_hex(4)})
        products=[]
        for worker in range(4):
            product=call('POST','/products',{'sku':'P6-LOAD-'+secrets.token_hex(4),'name':f'Phase6 synthetic load worker {worker}','category_id':category['id'],'initial_stock':'1000','unit':'unit','lead_time_days':3,'safety_stock':'4','overstock_multiplier':'2'})
            products.append(product)
            call('POST',f"/products/{product['id']}/forecast-mappings",{'series_sku':'20728','confirm_research_demo':True,'reason':'Performance fixture only; dated UK series'})
        def forecast(product):return call('POST',f"/forecasts/{product['id']}/generate",{'request_key':str(uuid4()),'forecast_origin':'2011-11-10','horizon':28,'context':'research_demo','confirm_research_demo':True})
        forecasts=[forecast(product) for product in products]
        operations=['liveness','readiness','login','products','sales','inventory_update','operational_sale','forecast_retrieval','forecast_inference','recommendation','dashboard']
        def one(operation,worker):
            item=products[worker];pid=item['id'];body=None;method='GET'
            if operation=='liveness':path='/health/live'
            elif operation=='readiness':path='/health/ready'
            elif operation=='login':path='/auth/login';method='POST';body=account
            elif operation=='products':path='/products'
            elif operation=='sales':path='/sales?limit=50'
            elif operation in ['inventory_update','operational_sale']:
                inv=call('GET',f'/products/{pid}/inventory')
                if operation=='inventory_update':
                    method='PUT';path=f'/products/{pid}/inventory';body={'on_hand':inv['on_hand'],'confirmed_in_transit':inv['confirmed_in_transit'],'allocated':inv['allocated'],'version':inv['version'],'reason':'Phase6 measured synthetic adjustment'}
                else:method='POST';path='/sales';body={'product_id':pid,'quantity':'1','unit_price':'10','sale_date':'2026-09-01T10:00:00Z','inventory_version':inv['version'],'request_key':str(uuid4())}
            elif operation=='forecast_retrieval':path=f'/forecasts/{pid}'
            elif operation=='forecast_inference':method='POST';path=f'/forecasts/{pid}/generate';body={'request_key':str(uuid4()),'forecast_origin':'2011-11-10','horizon':28,'context':'research_demo','confirm_research_demo':True}
            elif operation=='recommendation':method='POST';path=f'/recommendations/{pid}/generate';body={'request_key':str(uuid4()),'forecast_id':forecasts[worker]['id'],'decision_as_of':'2011-11-11','context':'research_demo','confirm_research_demo':True}
            else:path='/dashboard?context=research_demo'
            t=time.perf_counter()
            r=client.request(method,path,headers=headers,json=body)
            elapsed=(time.perf_counter()-t)*1000
            if operation=='login' and r.status_code==200:
                client.post('/auth/logout',headers={'Authorization':'Bearer '+r.json()['access_token']}).raise_for_status()
            sample = {'milliseconds':elapsed,'status':r.status_code}
            if r.status_code >= 400: sample['detail'] = r.json()
            return sample
        for mode,workers,per_worker in [('normal',1,8),('modest_concurrent',4,8)]:
            for operation in operations:
                t=time.perf_counter()
                def batch(worker):return [one(operation,worker) for _ in range(per_worker)]
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    samples=[r for batch_rows in pool.map(batch,range(workers)) for r in batch_rows]
                elapsed=time.perf_counter()-t
                values=[r['milliseconds'] for r in samples]
                errors=sum(r['status']>=400 for r in samples)
                rows.append({'mode':mode,'operation':operation,'concurrent_workers':workers,'requests':len(samples),'duration_seconds':elapsed,'mean_ms':float(np.mean(values)),'p50_ms':float(np.percentile(values,50)),'p95_ms':float(np.percentile(values,95)),'max_ms':max(values),'errors':errors,'error_rate':errors/len(samples),'samples':samples})
                print(f'{mode} {operation}: {len(samples)} requests; p95={rows[-1]["p95_ms"]:.1f}ms; errors={errors}',flush=True)
        integrity=[]
        for product in products:
            stock=call('GET',f"/products/{product['id']}/inventory")
            sales=call('GET',f"/sales?product_id={product['id']}")
            expected=984 if product==products[0] else 992
            integrity.append({'product_id':product['id'],'on_hand':stock['on_hand'],'sale_count':sales['total'],'expected_on_hand':expected,'passed':float(stock['on_hand'])==expected and sales['total']==1000-expected})
            call('DELETE',f"/products/{product['id']}")
        call('DELETE',f"/categories/{category['id']}");call('POST','/auth/logout')
    report={'executed_at_utc':datetime.now(UTC).isoformat(),'environment':{'os':platform.platform(),'python':platform.python_version(),'logical_processors':os.cpu_count(),'deployment':'Docker Desktop WSL2; MySQL8.4.11; localhost HTTP; native Windows client'},'tool':'httpx + perf_counter; ThreadPoolExecutor; NumPy percentiles','duration_seconds':time.perf_counter()-start,'warmup':'One 28-day real frozen inference per worker before measured samples','scope':'Four simulated workers, one authorized manager identity; worker-specific stock for writes; no capacity/SLA certification','measurement_boundary':'Request round trip only; prerequisite inventory GET and login logout excluded; setup/archive excluded','results':rows,'inventory_integrity':integrity}
    (ROOT/'docs/test-results/phase6-performance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert all(r['errors']==0 for r in rows) and all(r['passed'] for r in integrity)


if __name__=='__main__':main()
