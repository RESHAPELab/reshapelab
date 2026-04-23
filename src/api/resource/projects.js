import { isSupabaseConfigured, supabase } from '../../lib/supabase';
import MembersResource from './people';

const PROJECT_IMAGES_BUCKET = 'project-images';
const PROJECT_STORAGE_PREFIX = `${PROJECT_IMAGES_BUCKET}/`;

function slugifyProjectTitle(title) {
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
        .slice(0, 80) || 'project';
}

function sanitizeFileName(name) {
    const lastDotIndex = name.lastIndexOf('.');
    const baseName = lastDotIndex >= 0 ? name.slice(0, lastDotIndex) : name;
    const extension = lastDotIndex >= 0 ? name.slice(lastDotIndex).toLowerCase() : '';

    return `${sanitizePathSegment(baseName)}${extension}`;
}

function normalizeStoredProjectImagePath(imagePath) {
    if (!imagePath) {
        return '';
    }

    const normalizedValue = `${imagePath}`.trim();
    const normalizedPath = normalizedValue.replace(/^\/+/, '');

    if (normalizedPath.startsWith(PROJECT_STORAGE_PREFIX)) {
        return normalizedPath;
    }

    try {
        const parsedUrl = new URL(normalizedValue, 'http://localhost');
        const marker = `/storage/v1/object/public/${PROJECT_IMAGES_BUCKET}/`;
        const storagePathIndex = parsedUrl.pathname.indexOf(marker);

        if (storagePathIndex >= 0) {
            const filePath = decodeURIComponent(parsedUrl.pathname.slice(storagePathIndex + marker.length));
            return `${PROJECT_STORAGE_PREFIX}${filePath}`;
        }
    } catch {
        // Keep the original value when it is not a valid URL.
    }

    return normalizedPath;
}

function getProjectStorageFilePath(imagePath) {
    const normalizedPath = normalizeStoredProjectImagePath(imagePath);

    if (!normalizedPath.startsWith(PROJECT_STORAGE_PREFIX)) {
        return '';
    }

    return normalizedPath.slice(PROJECT_STORAGE_PREFIX.length);
}

function normalizeProject(project) {
    return {
        slug: project.slug || slugifyProjectTitle(project.project_name || project.title),
        title: project.project_name || project.title || '',
        description: project.project_description || project.description || '',
        shortDescription: project.short_project_description || project.shortDescription || '',
        image: normalizeStoredProjectImagePath(project.images?.small_image || project.image || ''),
        funding: project.funding || '',
        researchAreas: project.research_areas || project.researchAreas || [],
        people: project.people || [],
        articleTitles: project.article_titles || project.articleTitles || [],
        project_key_words: project.project_key_words || project.projectKeywords || []
    };
}

export function resolveProjectImageUrl(imagePath) {
    if (!imagePath) {
        return '';
    }

    if (imagePath.startsWith('data:') || imagePath.startsWith('blob:')) {
        return imagePath;
    }

    const storageFilePath = getProjectStorageFilePath(imagePath);

    if (storageFilePath && isSupabaseConfigured && supabase) {
        const {
            data: { publicUrl }
        } = supabase.storage.from(PROJECT_IMAGES_BUCKET).getPublicUrl(storageFilePath);

        return publicUrl;
    }

    if (/^(https?:)?\/\//i.test(imagePath)) {
        return imagePath;
    }

    const normalizedPath = imagePath.replace(/^\/+/, '');
    return `${import.meta.env.BASE_URL || '/'}${normalizedPath}`;
}

async function getRemoteProjects(includeInactive = false) {
    let query = supabase
        .from('projects')
        .select(`
            slug,
            title,
            description,
            short_description,
            image,
            funding,
            research_areas,
            people,
            article_titles,
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

    return (data || []).map((project) => normalizeProject({
        ...project,
        shortDescription: project.short_description,
        projectKeywords: project.project_keywords
    }));
}

async function searchRemoteProjectsByTitle(title, includeInactive = false) {
    const normalizedTitle = `${title || ''}`.trim();

    if (!normalizedTitle) {
        return getRemoteProjects(includeInactive);
    }

    let query = supabase
        .from('projects')
        .select(`
            slug,
            title,
            description,
            short_description,
            image,
            funding,
            research_areas,
            people,
            article_titles,
            project_keywords,
            is_active
        `)
        .or(`title.ilike.%${normalizedTitle}%,slug.eq.${slugifyProjectTitle(normalizedTitle)}`)
        .order('title');

    if (!includeInactive) {
        query = query.eq('is_active', true);
    }

    const { data, error } = await query;

    if (error) {
        throw error;
    }

    return (data || []).map((project) => normalizeProject({
        ...project,
        shortDescription: project.short_description,
        projectKeywords: project.project_keywords
    }));
}

const ProjectsResource = {
    async getProjects() {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        return getRemoteProjects(false);
    },

    async getProjectsByTitle(title) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        return searchRemoteProjectsByTitle(title, false);
    },

    async getAdminProjectsByTitle(title) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        return searchRemoteProjectsByTitle(title, true);
    },

    async getProjectsByUser(user) {
        const userFullName = `${user.first_name || user.firstName} ${user.last_name || user.lastName}`.trim().toLowerCase();
        const projects = await this.getProjects();

        return projects.filter((project) => {
            return project.people.some((personName) => personName.toLowerCase() === userFullName);
        });
    },

    async getUsersByProject(projectTitle) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const project = await this.getProjectsByTitle(projectTitle);
        const selectedProject = project[0];

        if (!selectedProject) {
            return [];
        }

        const projectPeople = selectedProject.people.map((person) => person.toLowerCase());
        const members = await MembersResource.getMembers();

        return members.filter((member) => {
            const fullName = `${member.firstName} ${member.lastName}`.toLowerCase();
            return projectPeople.includes(fullName);
        });
    },

    async getProjectBySlug(slug) {
        const projects = await this.getProjects();
        return projects.find((project) => project.slug === slug) || null;
    },

    async getAdminProjects() {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        return getRemoteProjects(true);
    },

    async upsertProject(project) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const payload = {
            slug: project.slug || slugifyProjectTitle(project.title),
            title: project.title,
            description: project.description || '',
            short_description: project.shortDescription || '',
            image: normalizeStoredProjectImagePath(project.image),
            funding: project.funding || '',
            research_areas: project.researchAreas || [],
            people: project.people || [],
            article_titles: project.articleTitles || [],
            project_keywords: project.project_key_words || [],
            is_active: project.is_active !== false
        };

        const { data, error } = await supabase
            .from('projects')
            .upsert(payload)
            .select()
            .single();

        if (error) {
            throw error;
        }

        return normalizeProject({
            ...data,
            shortDescription: data.short_description,
            projectKeywords: data.project_keywords
        });
    },

    async uploadProjectImage(file, projectSlug) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        if (!file) {
            throw new Error('Choose an image before uploading.');
        }

        const safeProjectSlug = sanitizePathSegment(projectSlug);
        const safeFileName = sanitizeFileName(file.name || 'project-image');
        const filePath = `${safeProjectSlug}/${Date.now()}-${safeFileName}`;

        const { error } = await supabase.storage
            .from(PROJECT_IMAGES_BUCKET)
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
        } = supabase.storage.from(PROJECT_IMAGES_BUCKET).getPublicUrl(filePath);

        return {
            filePath: `${PROJECT_STORAGE_PREFIX}${filePath}`,
            publicUrl
        };
    },

    async deleteProject(slug) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const { error } = await supabase
            .from('projects')
            .delete()
            .eq('slug', slug);

        if (error) {
            throw error;
        }
    }
};

export default ProjectsResource;
