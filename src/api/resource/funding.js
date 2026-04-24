import localData from '/public/funding.json';
import { isSupabaseConfigured, supabase } from '../../lib/supabase';

function normalizeFundingItem(item) {
    return {
        id: item.id || '',
        name: item.name || '',
        initial_date: item.initial_date || '',
        final_date: item.final_date || '',
        access_link: item.access_link || '',
        total_amount: item.total_amount || '',
        projects: item.projetcs || item.projects || [],
        is_active: item.is_active !== false
    };
}

function getLocalFunding() {
    return (localData.funding || []).map(normalizeFundingItem);
}

async function getRemoteFunding(includeInactive = false) {
    let query = supabase
        .from('funding_awards')
        .select(`
            id,
            name,
            initial_date,
            final_date,
            access_link,
            total_amount,
            projects,
            is_active
        `)
        .order('name');

    if (!includeInactive) {
        query = query.eq('is_active', true);
    }

    const { data, error } = await query;

    if (error) {
        throw error;
    }

    return (data || []).map(normalizeFundingItem);
}

function buildFundingPayload(item) {
    return {
        id: item.id,
        name: item.name || '',
        initial_date: item.initial_date || '',
        final_date: item.final_date || '',
        access_link: item.access_link || '',
        total_amount: item.total_amount || '',
        projects: item.projects || [],
        is_active: item.is_active !== false
    };
}

const FundingResource = {
    async getFunding() {
        if (!isSupabaseConfigured || !supabase) {
            return getLocalFunding();
        }

        try {
            return await getRemoteFunding(false);
        } catch (error) {
            console.warn('Falling back to local funding data.', error);
            return getLocalFunding();
        }
    },

    async getAdminFunding() {
        if (!isSupabaseConfigured || !supabase) {
            return getLocalFunding();
        }

        return getRemoteFunding(true);
    },

    async getAdminFundingByTitle(title) {
        if (!isSupabaseConfigured || !supabase) {
            const normalizedTitle = `${title || ''}`.trim().toLowerCase();
            return getLocalFunding().filter((item) => item.name.toLowerCase().includes(normalizedTitle) || item.id.toLowerCase().includes(normalizedTitle));
        }

        const normalizedTitle = `${title || ''}`.trim();

        if (!normalizedTitle) {
            return getRemoteFunding(true);
        }

        const { data, error } = await supabase
            .from('funding_awards')
            .select(`
                id,
                name,
                initial_date,
                final_date,
                access_link,
                total_amount,
                projects,
                is_active
            `)
            .or(`name.ilike.%${normalizedTitle}%,id.ilike.%${normalizedTitle}%`)
            .order('name');

        if (error) {
            throw error;
        }

        return (data || []).map(normalizeFundingItem);
    },

    async upsertFundingItem(item) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const { data, error } = await supabase
            .from('funding_awards')
            .upsert(buildFundingPayload(item))
            .select()
            .single();

        if (error) {
            throw error;
        }

        return normalizeFundingItem(data);
    },

    async deleteFundingItem(id) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const { error } = await supabase
            .from('funding_awards')
            .delete()
            .eq('id', id);

        if (error) {
            throw error;
        }
    }
};

export default FundingResource;
