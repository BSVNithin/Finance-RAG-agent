"""Import synthetic Northstar seed chunks into Supabase pgvector using OpenAI embeddings.
Run from any working directory: python scripts/ingest_seed_chunks.py
Environment: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, OPENAI_API_KEY
"""
import os, json, time, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "metadata" / "chunks_seed.jsonl"
SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]

if not CHUNKS.exists():
    raise FileNotFoundError(f"Seed chunks not found: {CHUNKS}. Keep metadata/chunks_seed.jsonl inside the project folder.")

def embed(text):
    r = requests.post("https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
        json={"model": "text-embedding-3-small", "input": text, "dimensions": 1536}, timeout=90)
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]

headers={"apikey":SUPABASE_KEY,"Authorization":f"Bearer {SUPABASE_KEY}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"}
url=f"{SUPABASE_URL}/rest/v1/rag_documents?on_conflict=id"
count=0
for line in CHUNKS.read_text(encoding="utf-8").splitlines():
    if not line.strip(): continue
    c=json.loads(line)
    emb=embed(c["text"])
    row={"id":c["chunk_id"],"document_id":c["document_id"],"source_file":c["source_file"],
      "document_type":c["document_type"],"quarter":c.get("quarter"),"document_date":c.get("document_date"),
      "speaker":c.get("speaker"),"section":c.get("section"),"page_or_timestamp":c.get("page_or_timestamp"),
      "tags":c.get("tags",[]),"synthetic":c.get("synthetic",True),"content":c["text"],"embedding":emb}
    r=requests.post(url,headers=headers,json=row,timeout=90)
    if not r.ok: raise RuntimeError(f"Supabase insert failed for {c['chunk_id']}: {r.status_code} {r.text}")
    count+=1
    print(f"Upserted {count}: {c['chunk_id']}")
    time.sleep(0.08)
print(f"Done. Upserted {count} chunks.")
