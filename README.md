# Northstar Investor Pressure Test — OpenAI + n8n + Supabase + Streamlit

**All Northstar company names, financials, transcripts, quotations, and management statements are synthetic classroom-demo data.**

## Architecture
Streamlit UI → n8n webhook → OpenAI `text-embedding-3-small` (1536 dimensions) → Supabase pgvector similarity search → OpenAI `gpt-4.1-mini` grounded answer → Streamlit evidence panel.

Excel workbook rows are imported separately into `financial_records` (JSONB/structured records). Narrative transcript chunks go into `rag_documents` with embeddings. This separation supports exact numeric lookup and semantic retrieval.

## Files
- `financials.xlsx`: synthetic quarterly financial workbook with P&L, Cash Flow, Balance Sheet, Segment Performance, KPI Summary, Guidance Register and Question Bank sheets.
- `metadata/chunks_seed.jsonl`: transcript/commentary chunks for vector search.
- `sql/supabase_schema.sql`: creates `rag_documents`, `financial_records`, and vector-match RPC.
- `scripts/ingest_excel.py`: imports Excel rows to `financial_records`.
- `scripts/ingest_seed_chunks.py`: embeds transcript chunks with OpenAI and upserts to pgvector.
- `n8n_workflows/query_rag_workflow.json`: OpenAI-powered query workflow.
- `streamlit_app/`: UI and included CSVs.

## Step 1 — Create API keys and Supabase project
1. Create an OpenAI API key at https://platform.openai.com/api-keys and make sure API billing/access is enabled.
2. Create a Supabase project at https://supabase.com.
3. Copy the Supabase project URL and server-side service-role/secret key from project API settings. Never expose this key in Streamlit frontend, browser code, or public GitHub.
4. In Supabase SQL Editor, run `sql/supabase_schema.sql` once. It uses `vector(1536)` to match OpenAI `text-embedding-3-small`.

## Step 2 — Install Python dependencies
From the project root (`northstar_n8n_supabase`):
```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install requests pandas openpyxl
```

Set environment variables in PowerShell (replace placeholders):
```powershell
$env:SUPABASE_URL="https://YOUR_PROJECT_REF.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY"
$env:OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```
Keep keys local; do not commit them.

## Step 3 — Import the Excel workbook into Supabase
```bash
python scripts/ingest_excel.py
```
This reads each workbook sheet and upserts rows into `financial_records`. Verify rows in Supabase Table Editor. It does **not** create embeddings for financial rows; it preserves structured values as JSONB.

## Step 4 — Embed and ingest transcript/commentary chunks
```bash
python scripts/ingest_seed_chunks.py
```
The script reads `metadata/chunks_seed.jsonl`, calls OpenAI embeddings, and inserts the chunks into `rag_documents`. It may take a few minutes and incur API usage. Verify the row count in Supabase Table Editor.

If you rerun ingestion, the scripts upsert using stable IDs. If you previously created the old Gemini schema with `vector(768)`, do not run the new ingestion against it. For a fresh prototype, use a new/clean Supabase project or migrate/drop the old table and RPC, then run the supplied SQL schema.

## Step 5 — Import the n8n workflow
1. In n8n, import `n8n_workflows/query_rag_workflow.json`.
2. Open **Embed Question — OpenAI** and **Draft Evidence-Grounded Answer — OpenAI**. Replace `REPLACE_WITH_OPENAI_API_KEY` in their Authorization headers with `Bearer YOUR_OPENAI_API_KEY`, or preferably configure n8n credentials/secrets.
3. In **Retrieve Evidence — Supabase RPC**, replace `https://YOUR_PROJECT_REF.supabase.co` and both Supabase key placeholders. Keep the service-role key only in n8n server-side.
4. Save and test the workflow with a POST body:
```json
{"question":"You previously expected margin recovery by Q2 FY26. What changed?","quarter":"Q2 FY26","top_k":5}
```
5. Activate/publish it and copy the Production URL from the Webhook node.

Node parameter names may vary slightly across n8n versions. If import warns about a parameter, recreate that HTTP Request node with the same URL, headers, JSON body, and response format. Never share a public webhook without authentication/rate limits.

## Step 6 — Run Streamlit
From the project root:
```bash
pip install -r streamlit_app/requirements.txt
```
Create `streamlit_app/.streamlit/secrets.toml` (copy from `secrets.toml.example`) and set:
```toml
N8N_WEBHOOK_URL = "https://YOUR_N8N_HOST/webhook/investor-pressure-test"
```
Then run:
```bash
streamlit run streamlit_app/app.py
```
The supplied `streamlit_app/data/` folder contains KPI, P&L, segment, question-bank and supporting CSVs so the dashboard charts work immediately. Streamlit calls n8n; it does not receive the Supabase service-role key.

## Step 7 — Demo and validate
Try these prompts:
- “Why did EBITDA margin decline 280 bps despite revenue growth?”
- “What did management previously say about margin recovery by Q2 FY26?”
- “Why did operating cash flow decline, and what evidence is missing?”
- “Which segments have the weakest margins?”

Check that every claim is supported by retrieved source labels. The current RAG workflow answers from transcript/commentary chunks; structured Excel rows are stored separately and are not yet automatically queried by the n8n workflow. For numeric answers, add a Supabase query node against `financial_records` or a curated metric table and merge its results into the prompt. Do not let the model infer values that are not in its evidence.

## Security and limitations
- Synthetic classroom prototype only; human Finance/Legal review required before external use.
- Never put API keys in GitHub or browser-side code.
- OpenAI API is billed separately from ChatGPT.
- Similarity threshold is a tunable prototype setting, not a guarantee of evidence quality.
- The Excel importer stores raw row data; production use should validate data types and use typed tables for key metrics.
