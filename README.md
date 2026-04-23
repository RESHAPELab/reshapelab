# reshapelab.github.io
Project Page

## Supabase Admin

This repo now includes a Supabase-backed admin portal for:

1. Admin login at `/admin/login`
2. News CRUD at `/admin/news`
3. People CRUD at `/admin/people`
4. Editing research keywords, DBLP PIDs, and profile metadata for people

### Setup

1. Create a Supabase project.
2. Run the SQL in [supabase/schema.sql](./supabase/schema.sql) in the Supabase SQL editor.
3. Create a `.env` file and fill in these values after the "=" using your Supabase API keys.
   - `VITE_SUPABASE_URL=`
   - `VITE_SUPABASE_ANON_KEY=`
   - `SUPABASE_SERVICE_ROLE_KEY=`
4. In Supabase Auth, enable Email/Password login (it may already be enabled).
5. Create your first user in Supabase Auth.
6. In the `profiles` table, set that user's `is_admin` to `true`. This user may now use the admin portal for the website.

### Notes

- The public site still falls back to the local .json files when Supabase is not configured or unavailable.
- News images and profile images are still stored as string paths.
- The current .json and image data can be uploaded to Supabase at anytime (as long as .env is configured) using `npm run import:supabase`
- Test this project by first using `npm i` then `npm run dev`
