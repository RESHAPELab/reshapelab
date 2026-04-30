import localData from '/public/research_areas.json';
import MembersResource from './people';
import { isSupabaseConfigured, supabase } from '../../lib/supabase';

const RESEARCH_AREA_IMAGES_BUCKET = 'research-area-images';
const RESEARCH_AREA_STORAGE_PREFIX = `${RESEARCH_AREA_IMAGES_BUCKET}/`;

function slugifyResearchAreaTitle(title) {
    return `${title || ''}`
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

function sanitizePathSegment(value) {
    return `${value || ''}`
        .toLowerCase()
        .replace(/[^a-z0-9-_]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 80) || 'research-area';
}

function sanitizeFileName(name) {
    const lastDotIndex = name.lastIndexOf('.');
    const baseName = lastDotIndex >= 0 ? name.slice(0, lastDotIndex) : name;
    const extension = lastDotIndex >= 0 ? name.slice(lastDotIndex).toLowerCase() : '';

    return `${sanitizePathSegment(baseName)}${extension}`;
}

function normalizeStoredResearchAreaImagePath(imagePath) {
    if (!imagePath) {
        return '';
    }

    const normalizedValue = `${imagePath}`.trim();
    const normalizedPath = normalizedValue.replace(/^\/+/, '');

    if (normalizedPath.startsWith(RESEARCH_AREA_STORAGE_PREFIX)) {
        return normalizedPath;
    }

    try {
        const parsedUrl = new URL(normalizedValue, 'http://localhost');
        const marker = `/storage/v1/object/public/${RESEARCH_AREA_IMAGES_BUCKET}/`;
        const storagePathIndex = parsedUrl.pathname.indexOf(marker);

        if (storagePathIndex >= 0) {
            const filePath = decodeURIComponent(parsedUrl.pathname.slice(storagePathIndex + marker.length));
            return `${RESEARCH_AREA_STORAGE_PREFIX}${filePath}`;
        }
    } catch {
        // Keep the original value when it is not a valid URL.
    }

    return normalizedPath;
}

function getResearchAreaStorageFilePath(imagePath) {
    const normalizedPath = normalizeStoredResearchAreaImagePath(imagePath);

    if (!normalizedPath.startsWith(RESEARCH_AREA_STORAGE_PREFIX)) {
        return '';
    }

    return normalizedPath.slice(RESEARCH_AREA_STORAGE_PREFIX.length);
}

function normalizeResearchArea(area) {
    return {
        slug: area.slug || slugifyResearchAreaTitle(area.project_name || area.title),
        title: area.project_name || area.title || '',
        description: area.project_description || area.description || '',
        image: normalizeStoredResearchAreaImagePath(area.images?.small_image || area.image || ''),
        project_key_words: area.project_key_words || area.projectKeywords || [],
        is_active: area.is_active !== false
    };
}

function getLocalResearchAreas() {
    return (localData.projects || []).map(normalizeResearchArea);
}

async function getRemoteResearchAreas(includeInactive = false) {
    let query = supabase
        .from('research_areas')
        .select(`
            slug,
            title,
            description,
            image,
            project_keywords,
            is_active
        `)
        .order('title');

    if (!includeInactive) {
        query = query.eq('is_active', true);
    }

    const { data, error } = await query;

    if (error) {
        throw error;
    }

    return (data || []).map((area) => normalizeResearchArea({
        ...area,
        projectKeywords: area.project_keywords
    }));
}

function buildResearchAreaPayload(area) {
    return {
        slug: area.slug || slugifyResearchAreaTitle(area.title),
        title: area.title,
        description: area.description || '',
        image: normalizeStoredResearchAreaImagePath(area.image),
        project_keywords: area.project_key_words || [],
        is_active: area.is_active !== false
    };
}

export function resolveResearchAreaImageUrl(imagePath) {
    if (!imagePath) {
        return '';
    }

    if (imagePath.startsWith('data:') || imagePath.startsWith('blob:')) {
        return imagePath;
    }

    const storageFilePath = getResearchAreaStorageFilePath(imagePath);

    if (storageFilePath && isSupabaseConfigured && supabase) {
        const {
            data: { publicUrl }
        } = supabase.storage.from(RESEARCH_AREA_IMAGES_BUCKET).getPublicUrl(storageFilePath);

        return publicUrl;
    }

    if (/^(https?:)?\/\//i.test(imagePath)) {
        return imagePath;
    }

    const normalizedPath = imagePath.replace(/^\/+/, '');
    return `${import.meta.env.BASE_URL || '/'}${normalizedPath}`;
}

const ResearchAreasResource = {
    async getResearchAreas() {
        if (!isSupabaseConfigured || !supabase) {
            return getLocalResearchAreas();
        }

        try {
            return await getRemoteResearchAreas(false);
        } catch (error) {
            console.warn('Falling back to local research area data.', error);
            return getLocalResearchAreas();
        }
    },

    async getResearchAreaByTitle(title) {
        const researchAreas = await this.getResearchAreas();
        const normalizedTitle = `${title || ''}`.toLowerCase();

        return researchAreas.filter((area) => {
            return area.title.toLowerCase().includes(normalizedTitle) || area.slug === slugifyResearchAreaTitle(title);
        });
    },

    async getUsersByResearchArea(projectTitle) {
        const members = await MembersResource.getMembers();

        return members.filter((member) => {
            return Array.isArray(member.projects) ? member.projects.includes(projectTitle) : false;
        }).map((member) => ({
            firstName: member.firstName,
            lastName: member.lastName,
            role: member.role,
            photos: member.photos,
            contacts: member.contacts
        }));
    },

    async getAdminResearchAreas() {
        if (!isSupabaseConfigured || !supabase) {
            return getLocalResearchAreas();
        }

        return getRemoteResearchAreas(true);
    },

    async getAdminResearchAreasByTitle(title) {
        if (!isSupabaseConfigured || !supabase) {
            return getLocalResearchAreas().filter((area) => area.title.toLowerCase().includes(`${title || ''}`.trim().toLowerCase()));
        }

        const normalizedTitle = `${title || ''}`.trim();

        if (!normalizedTitle) {
            return getRemoteResearchAreas(true);
        }

        const { data, error } = await supabase
            .from('research_areas')
            .select(`
                slug,
                title,
                description,
                image,
                project_keywords,
                is_active
            `)
            .or(`title.ilike.%${normalizedTitle}%,slug.eq.${slugifyResearchAreaTitle(normalizedTitle)}`)
            .order('title');

        if (error) {
            throw error;
        }

        return (data || []).map((area) => normalizeResearchArea({
            ...area,
            projectKeywords: area.project_keywords
        }));
    },

    async upsertResearchArea(area) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const payload = buildResearchAreaPayload(area);

        const { data, error } = await supabase
            .from('research_areas')
            .upsert(payload)
            .select()
            .single();

        if (error) {
            throw error;
        }

        return normalizeResearchArea({
            ...data,
            projectKeywords: data.project_keywords
        });
    },

    async uploadResearchAreaImage(file, researchAreaSlug) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        if (!file) {
            throw new Error('Choose an image before uploading.');
        }

        const safeResearchAreaSlug = sanitizePathSegment(researchAreaSlug);
        const safeFileName = sanitizeFileName(file.name || 'research-area-image');
        const filePath = `${safeResearchAreaSlug}/${Date.now()}-${safeFileName}`;

        const { error } = await supabase.storage
            .from(RESEARCH_AREA_IMAGES_BUCKET)
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
        } = supabase.storage.from(RESEARCH_AREA_IMAGES_BUCKET).getPublicUrl(filePath);

        return {
            filePath: `${RESEARCH_AREA_STORAGE_PREFIX}${filePath}`,
            publicUrl
        };
    },

    async deleteResearchArea(slug) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const { error } = await supabase
            .from('research_areas')
            .delete()
            .eq('slug', slug);

        if (error) {
            throw error;
        }
    }
};

export default ResearchAreasResource;
