"""Import workbook rows to Supabase financial_records as JSONB (not vectorized).
Environment: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
Run: python scripts/ingest_excel.py [optional/path/to/workbook.xlsx]
"""
import os, sys, json, hashlib, math
from pathlib import Path
import pandas as pd
import requests
ROOT=Path(__file__).resolve().parents[1]
XLSX=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/"financials.xlsx"
URL=os.environ["SUPABASE_URL"].rstrip("/")+"/rest/v1/financial_records?on_conflict=id"
KEY=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
HEADERS={"apikey":KEY,"Authorization":f"Bearer {KEY}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
count=0
for sheet in pd.ExcelFile(XLSX).sheet_names:
    df=pd.read_excel(XLSX,sheet_name=sheet)
    for ix, row in df.iterrows():
        data={str(k): (None if pd.isna(v) else (v.isoformat() if hasattr(v,'isoformat') else (v.item() if hasattr(v,'item') else v))) for k,v in row.items()}
        if not any(v is not None for v in data.values()): continue
        quarter=next((str(v) for k,v in data.items() if str(k).lower() in ('quarter','period','reporting quarter')),None)
        text=' | '.join(f'{k}: {v}' for k,v in data.items() if v is not None)
        stable=f'{XLSX.name}|{sheet}|{ix+2}'
        row_id=hashlib.sha256(stable.encode()).hexdigest()[:32]
        payload={"id":row_id,"source_file":XLSX.name,"sheet_name":sheet,"row_number":int(ix+2),"quarter":quarter,"row_data":data,"search_text":text}
        r=requests.post(URL,headers=HEADERS,json=payload,timeout=60)
        if not r.ok: raise RuntimeError(f'{sheet} row {ix+2}: {r.status_code} {r.text}')
        count+=1
    print(f'Imported sheet: {sheet} ({len(df)} rows)')
print(f'Imported {count} rows from {XLSX.name} into financial_records.')
