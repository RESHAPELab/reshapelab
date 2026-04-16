# reshapelab.github.io
Project Page

## Supabase admin prototype

This repo now includes a Supabase-backed admin prototype for:

1. Admin login at `/admin/login`
2. News CRUD at `/admin/news`
3. People CRUD at `/admin/people`
4. Editing research keywords, DBLP PIDs, and profile metadata for people

### Setup

1. Create a Supabase project.
2. Run the SQL in [supabase/schema.sql](./supabase/schema.sql) in the Supabase SQL editor.
3. Copy [.env.example](./.env.example) to `.env` and fill in:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
4. In Supabase Auth, enable Email/Password login.
5. Create your first user in Supabase Auth.
6. In the `profiles` table, set that user's `is_admin` to `true`.

### Notes

- The public site still falls back to the local JSON files when Supabase is not configured or unavailable.
- For this prototype, news images and profile images are still stored as string paths. Storage upload flows can be added next.

Steps to deploy to Github Pages

To recommit new changes and push up to the remote repository:

1. On remote repository delete the "gh-pages" branch. 

2. In you local repository run this command: npm run build

3. git add dist -f

4. git commit -m [your commit message here]

5. git subtree push --prefix dist origin gh-pages
