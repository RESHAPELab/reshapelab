import { isSupabaseConfigured, supabase } from './supabase';

async function getCurrentSession() {
    if (!isSupabaseConfigured || !supabase) {
        return null;
    }

    const { data, error } = await supabase.auth.getSession();

    if (error) {
        throw error;
    }

    return data.session;
}

async function getCurrentUser() {
    const session = await getCurrentSession();
    return session?.user || null;
}

async function getAdminProfile() {
    const user = await getCurrentUser();

    if (!user || !supabase) {
        return null;
    }

    const { data, error } = await supabase
        .from('profiles')
        .select('id, email, full_name, is_admin')
        .eq('id', user.id)
        .maybeSingle();

    if (error) {
        throw error;
    }

    return data;
}

export async function requireAdminSession() {
    if (!isSupabaseConfigured || !supabase) {
        return { ok: false, reason: 'missing-config' };
    }

    const user = await getCurrentUser();

    if (!user) {
        return { ok: false, reason: 'signed-out' };
    }

    const profile = await getAdminProfile();

    if (!profile?.is_admin) {
        return { ok: false, reason: 'not-admin' };
    }

    return { ok: true, user, profile };
}

export async function signInAdmin(email, password) {
    if (!supabase) {
        throw new Error('Supabase is not configured.');
    }

    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
    });

    if (error) {
        throw error;
    }

    return data;
}

export async function signOutAdmin() {
    if (!supabase) {
        return;
    }

    const { error } = await supabase.auth.signOut();

    if (error) {
        throw error;
    }
}

export async function getAdminContext() {
    const session = await getCurrentSession();
    const profile = await getAdminProfile();

    return {
        session,
        profile
    };
}
