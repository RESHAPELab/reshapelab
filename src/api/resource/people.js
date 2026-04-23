import localData from '/public/members.json';
import { isSupabaseConfigured, supabase } from '../../lib/supabase';

const PEOPLE_IMAGES_BUCKET = 'people-images';
const PEOPLE_STORAGE_PREFIX = `${PEOPLE_IMAGES_BUCKET}/`;

function slugFromMember(member) {
    return `${member.first_name?.trim() || ''} ${member.last_name?.trim() || ''}`.trim().replace(/ /g, '-');
}

function sanitizePathSegment(value) {
    return `${value || ''}`
        .toLowerCase()
        .replace(/[^a-z0-9-_]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 80) || 'person';
}

function sanitizeFileName(name) {
    const lastDotIndex = name.lastIndexOf('.');
    const baseName = lastDotIndex >= 0 ? name.slice(0, lastDotIndex) : name;
    const extension = lastDotIndex >= 0 ? name.slice(lastDotIndex).toLowerCase() : '';

    return `${sanitizePathSegment(baseName)}${extension}`;
}

function normalizeStoredPeopleImagePath(imagePath) {
    if (!imagePath) {
        return '';
    }

    const normalizedValue = `${imagePath}`.trim();
    const normalizedPath = normalizedValue.replace(/^\/+/, '');

    if (normalizedPath.startsWith(PEOPLE_STORAGE_PREFIX)) {
        return normalizedPath;
    }

    try {
        const parsedUrl = new URL(normalizedValue, 'http://localhost');
        const marker = `/storage/v1/object/public/${PEOPLE_IMAGES_BUCKET}/`;
        const storagePathIndex = parsedUrl.pathname.indexOf(marker);

        if (storagePathIndex >= 0) {
            const filePath = decodeURIComponent(parsedUrl.pathname.slice(storagePathIndex + marker.length));
            return `${PEOPLE_STORAGE_PREFIX}${filePath}`;
        }
    } catch {
        // Keep the original value when it is not a valid URL.
    }

    return normalizedPath;
}

function getPeopleStorageFilePath(imagePath) {
    const normalizedPath = normalizeStoredPeopleImagePath(imagePath);

    if (!normalizedPath.startsWith(PEOPLE_STORAGE_PREFIX)) {
        return '';
    }

    return normalizedPath.slice(PEOPLE_STORAGE_PREFIX.length);
}

function normalizePhotos(photos = {}) {
    return {
        photo_with_background: normalizeStoredPeopleImagePath(photos.photo_with_background) || 'images/people/user_icon.png',
        photo_without_background: normalizeStoredPeopleImagePath(photos.photo_without_background) || 'images/people/user_icon.png'
    };
}

export function resolveMemberImageUrl(imagePath) {
    if (!imagePath) {
        return '';
    }

    if (imagePath.startsWith('data:') || imagePath.startsWith('blob:')) {
        return imagePath;
    }

    const storageFilePath = getPeopleStorageFilePath(imagePath);

    if (storageFilePath && isSupabaseConfigured && supabase) {
        const {
            data: { publicUrl }
        } = supabase.storage.from(PEOPLE_IMAGES_BUCKET).getPublicUrl(storageFilePath);

        return publicUrl;
    }

    if (/^(https?:)?\/\//i.test(imagePath)) {
        return imagePath;
    }

    const normalizedPath = imagePath.replace(/^\/+/, '');
    return `${import.meta.env.BASE_URL || '/'}${normalizedPath}`;
}

function normalizeMember(member) {
    return {
        firstName: member.first_name,
        lastName: member.last_name,
        role: member.role,
        photos: normalizePhotos(member.photos),
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
            photos: normalizePhotos(member.photos || {}),
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

    async uploadMemberImage(file, memberSlug, photoVariant) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        if (!file) {
            throw new Error('Choose an image before uploading.');
        }

        const safeMemberSlug = sanitizePathSegment(memberSlug);
        const safeVariant = sanitizePathSegment(photoVariant);
        const safeFileName = sanitizeFileName(file.name || 'profile-image');
        const filePath = `${safeMemberSlug}/${safeVariant}/${Date.now()}-${safeFileName}`;

        const { error } = await supabase.storage
            .from(PEOPLE_IMAGES_BUCKET)
            .upload(filePath, file, {
                cacheControl: '3600',
                upsert: false,
                contentType: file.type || undefined
            });

        if (error) {
            throw error;
        }

        const {
            data: { publicUrl }
        } = supabase.storage.from(PEOPLE_IMAGES_BUCKET).getPublicUrl(filePath);

        return {
            filePath: `${PEOPLE_STORAGE_PREFIX}${filePath}`,
            publicUrl
        };
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
