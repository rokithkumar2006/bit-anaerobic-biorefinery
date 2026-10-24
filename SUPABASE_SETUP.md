# Supabase cloud records setup

This repository includes the backend and SQL foundation for per-user cloud record storage. It is not active until a Supabase project is created, the SQL is applied, environment variables are configured in Vercel, and the website sign-in/sync UI is connected.

## 1. Create a Supabase project

1. Create a project at https://supabase.com/dashboard and choose the Free plan.
2. Save the database password privately; the application does not need it.
3. In Project Settings → API (or Connect), copy the Project URL and the public publishable/anon key.
4. Never put the service-role/secret key into the website or these public configuration variables.

## 2. Create the table and security policies

Open SQL Editor in the Supabase dashboard and run supabase/migrations/202610240001_project_records.sql.

The table uses Row Level Security (RLS). Authenticated users can access only rows whose user_id equals their Supabase Auth user ID. Each account gets its own copy of each browser-storage key.

## 3. Add Vercel environment variables

In the Vercel project settings, add the following for Production, Preview, and Development as appropriate:

- SUPABASE_URL = the project URL, e.g. https://YOUR_PROJECT_REF.supabase.co
- SUPABASE_ANON_KEY = the public publishable/anon key

Do not set a service-role key for these endpoints. Redeploy after adding variables.

## 4. Endpoints in this repository

- GET /api/cloud_config returns the public URL and anon key only when configured.
- GET /api/cloud_records lists records for the authenticated user.
- POST /api/cloud_records upserts a batch of 1–250 records. Body: {"records":[{"record_key":"bitExample_v1","record_value":{"example":true}}]}.
- DELETE /api/cloud_records?key=bitExample_v1 removes one key for the authenticated user.

All cloud-record requests require Authorization: Bearer <Supabase access token>. The access token is validated by Supabase Auth, and database access is restricted by RLS. Do not share access tokens.

## Important current limitation

These endpoints are a secure backend foundation, not yet a complete website integration: the existing HTML frontend still needs Supabase sign-in/sign-up and explicit cloud-sync/restore controls. Existing local browser records remain local until the user signs in and deliberately syncs them. This setup deliberately does not silently overwrite local data with cloud data.
