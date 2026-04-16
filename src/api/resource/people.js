import localData from '/public/members.json';
import { isSupabaseConfigured, supabase } from '../../lib/supabase';

function slugFromMember(member) {
    return `${member.first_name?.trim() || ''} ${member.last_name?.trim() || ''}`.trim().replace(/ /g, '-');
}

function normalizeMember(member) {
    return {
        firstName: member.first_name,
        lastName: member.last_name,
        role: member.role,
        photos: member.photos || {
            photo_with_background: 'images/people/user_icon.png',
            photo_without_background: 'images/people/user_icon.png'
        },
        contacts: member.contacts || {},
        description: member.description || '',
        research_keywords: member.research_keywords || [],
        highlighted_publications: member.highlighted_publications || [],
        author_name: member.author_name || [],
        dblpPid: member.dblp_pid || '',
        projects: member.projects || [],
        slug: member.slug || slugFromMember(member)
    };
}

function normalizeRemoteMember(member) {
    return normalizeMember({
        ...member,
        photos: member.photos || member.photos_json,
        contacts: member.contacts || member.contacts_json,
        research_keywords: member.research_keywords || [],
        author_name: member.author_name || [],
        projects: member.projects || []
    });
}

function sortMembers(members) {
    return members.sort((a, b) => {
        const nameA = `${a.firstName} ${a.lastName}`;
        const nameB = `${b.firstName} ${b.lastName}`;
        return nameA.localeCompare(nameB);
    });
}

function getLocalMembers() {
    return sortMembers(localData.members.map(normalizeMember));
}

async function getRemoteMembers() {
    const { data, error } = await supabase
        .from('people_profiles')
        .select(`
            id,
            slug,
            first_name,
            last_name,
            role,
            description,
            photos,
            contacts,
            research_keywords,
            highlighted_publications,
            author_name,
            dblp_pid,
            projects,
            is_active
        `)
        .eq('is_active', true);

    if (error) {
        throw error;
    }

    return sortMembers((data || []).map(normalizeRemoteMember));
}

const MembersResource = {
    async getMembers() {
        if (!isSupabaseConfigured || !supabase) {
            return getLocalMembers();
        }

        try {
            return await getRemoteMembers();
        } catch (error) {
            console.warn('Falling back to local member data.', error);
            return getLocalMembers();
        }
    },

    async getMembersByRole(role) {
        const members = await this.getMembers();

        if (role === 'Student') {
            return members.filter((member) => !member.role.includes('Professor'));
        }

        return members.filter((member) => member.role.includes(role));
    },

    async getMembersByEmail(email) {
        const members = await this.getMembers();
        return members.find((member) => member.contacts?.email === email) || null;
    },

    async getFirstMemberByName(fullName) {
        const members = await this.getMembers();
        return members.find((member) => member.slug === fullName) || null;
    },

    async getMemberByAuthorName(authorNames) {
        const members = await this.getMembers();

        return members
            .filter((member) => {
                return member.author_name ? member.author_name.some((name) => authorNames.includes(name)) : false;
            })
            .map((member) => ({
                first_name: member.firstName,
                last_name: member.lastName,
                contacts: member.contacts,
                photos: member.photos
            }));
    },

    async getAdminMembers() {
        if (!isSupabaseConfigured || !supabase) {
            return getLocalMembers();
        }

        const { data, error } = await supabase
            .from('people_profiles')
            .select(`
                id,
                slug,
                first_name,
                last_name,
                role,
                description,
                photos,
                contacts,
                research_keywords,
                highlighted_publications,
                author_name,
                dblp_pid,
                projects,
                is_active
            `)
            .order('first_name');

        if (error) {
            throw error;
        }

        return (data || []).map(normalizeRemoteMember);
    },

    async upsertMember(member) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const payload = {
            slug: member.slug || `${member.firstName} ${member.lastName}`.trim().replace(/ /g, '-'),
            first_name: member.firstName,
            last_name: member.lastName,
            role: member.role,
            description: member.description || '',
            photos: member.photos || {},
            contacts: member.contacts || {},
            research_keywords: member.research_keywords || [],
            highlighted_publications: member.highlighted_publications || [],
            author_name: member.author_name || [],
            dblp_pid: member.dblpPid || '',
            projects: member.projects || [],
            is_active: member.is_active !== false
        };

        const { data, error } = await supabase
            .from('people_profiles')
            .upsert(payload)
            .select()
            .single();

        if (error) {
            throw error;
        }

        return normalizeRemoteMember(data);
    },

    async deleteMember(slug) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const { error } = await supabase
            .from('people_profiles')
            .delete()
            .eq('slug', slug);

        if (error) {
            throw error;
        }
    }
};

export default MembersResource;
