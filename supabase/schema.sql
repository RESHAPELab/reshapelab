create table if not exists public.profiles (
    id uuid primary key references auth.users (id) on delete cascade,
    email text unique,
    full_name text,
    is_admin boolean not null default false,
    created_at timestamp with time zone not null default timezone('utc', now())
);

create table if not exists public.news_posts (
    id text primary key,
    title text not null,
    date text not null,
    person text[] not null default '{}',
    tag text not null default '',
    image text not null default '',
    description text not null default '',
    published boolean not null default true,
    sort_order integer,
    created_at timestamp with time zone not null default timezone('utc', now()),
    updated_at timestamp with time zone not null default timezone('utc', now())
);

create table if not exists public.people_profiles (
    slug text primary key,
    first_name text not null,
    last_name text not null,
    role text not null,
    description text not null default '',
    contacts jsonb not null default '{}'::jsonb,
    photos jsonb not null default '{}'::jsonb,
    research_keywords text[] not null default '{}',
    highlighted_publications text[] not null default '{}',
    author_name text[] not null default '{}',
    dblp_pid text not null default '',
    projects text[] not null default '{}',
    is_active boolean not null default true,
    created_at timestamp with time zone not null default timezone('utc', now()),
    updated_at timestamp with time zone not null default timezone('utc', now())
);

create table if not exists public.projects (
    slug text primary key,
    title text not null,
    description text not null default '',
    short_description text not null default '',
    image text not null default '',
    funding text not null default '',
    research_areas text[] not null default '{}',
    people text[] not null default '{}',
    article_titles text[] not null default '{}',
    project_keywords text[] not null default '{}',
    is_active boolean not null default true,
    created_at timestamp with time zone not null default timezone('utc', now()),
    updated_at timestamp with time zone not null default timezone('utc', now())
);

insert into storage.buckets (id, name, public)
values ('news-images', 'news-images', true)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('people-images', 'people-images', true)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('project-images', 'project-images', true)
on conflict (id) do nothing;

create or replace function public.handle_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = timezone('utc', now());
    return new;
end;
$$;

drop trigger if exists set_news_posts_updated_at on public.news_posts;
create trigger set_news_posts_updated_at
before update on public.news_posts
for each row execute function public.handle_updated_at();

drop trigger if exists set_people_profiles_updated_at on public.people_profiles;
create trigger set_people_profiles_updated_at
before update on public.people_profiles
for each row execute function public.handle_updated_at();

drop trigger if exists set_projects_updated_at on public.projects;
create trigger set_projects_updated_at
before update on public.projects
for each row execute function public.handle_updated_at();

alter table public.profiles enable row level security;
alter table public.news_posts enable row level security;
alter table public.people_profiles enable row level security;
alter table public.projects enable row level security;

drop policy if exists "public can read published news" on public.news_posts;
create policy "public can read published news"
on public.news_posts
for select
using (published = true);

drop policy if exists "public can read active people" on public.people_profiles;
create policy "public can read active people"
on public.people_profiles
for select
using (is_active = true);

create policy "public can read active projects"
on public.projects
for select
using (is_active = true);

drop policy if exists "admins can read profiles" on public.profiles;
create policy "admins can read profiles"
on public.profiles
for select
to authenticated
using (auth.uid() = id);

drop policy if exists "admins can manage news" on public.news_posts;
create policy "admins can manage news"
on public.news_posts
for all
to authenticated
using (
    exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
)
with check (
    exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
	    )
	);

drop policy if exists "admins can manage people" on public.people_profiles;
create policy "admins can manage people"
on public.people_profiles
for all
to authenticated
using (
    exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
)
with check (
    exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

create policy "admins can manage projects"
on public.projects
for all
to authenticated
using (
    exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
)
with check (
    exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

drop policy if exists "public can read news images" on storage.objects;
create policy "public can read news images"
on storage.objects
for select
using (bucket_id = 'news-images');

drop policy if exists "admins can upload news images" on storage.objects;
create policy "admins can upload news images"
on storage.objects
for insert
to authenticated
with check (
    bucket_id = 'news-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

drop policy if exists "admins can update news images" on storage.objects;
create policy "admins can update news images"
on storage.objects
for update
to authenticated
using (
    bucket_id = 'news-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
)
with check (
    bucket_id = 'news-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

drop policy if exists "admins can delete news images" on storage.objects;
create policy "admins can delete news images"
on storage.objects
for delete
to authenticated
using (
    bucket_id = 'news-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

drop policy if exists "public can read people images" on storage.objects;
create policy "public can read people images"
on storage.objects
for select
using (bucket_id = 'people-images');

drop policy if exists "public can read project images" on storage.objects;
create policy "public can read project images"
on storage.objects
for select
using (bucket_id = 'project-images');

drop policy if exists "admins can upload people images" on storage.objects;
create policy "admins can upload people images"
on storage.objects
for insert
to authenticated
with check (
    bucket_id = 'people-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

drop policy if exists "admins can upload project images" on storage.objects;
create policy "admins can upload project images"
on storage.objects
for insert
to authenticated
with check (
    bucket_id = 'project-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

drop policy if exists "admins can update people images" on storage.objects;
create policy "admins can update people images"
on storage.objects
for update
to authenticated
using (
    bucket_id = 'people-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
)
with check (
    bucket_id = 'people-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

drop policy if exists "admins can update project images" on storage.objects;
create policy "admins can update project images"
on storage.objects
for update
to authenticated
using (
    bucket_id = 'project-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
)
with check (
    bucket_id = 'project-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

drop policy if exists "admins can delete people images" on storage.objects;
create policy "admins can delete people images"
on storage.objects
for delete
to authenticated
using (
    bucket_id = 'people-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

drop policy if exists "admins can delete project images" on storage.objects;
create policy "admins can delete project images"
on storage.objects
for delete
to authenticated
using (
    bucket_id = 'project-images'
    and exists (
        select 1
        from public.profiles
        where profiles.id = auth.uid()
        and profiles.is_admin = true
    )
);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, email, full_name, is_admin)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data ->> 'full_name', ''),
        false
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();
