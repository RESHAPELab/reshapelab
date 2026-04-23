import localData from '/public/posts.json';
import { isSupabaseConfigured, supabase } from '../../lib/supabase';

const NEWS_IMAGES_BUCKET = 'news-images';
const NEWS_STORAGE_PREFIX = `${NEWS_IMAGES_BUCKET}/`;

function normalizeStoredNewsImagePath(imagePath) {
    if (!imagePath) {
        return '';
    }

    const normalizedValue = `${imagePath}`.trim();
    const normalizedPath = normalizedValue.replace(/^\/+/, '');

    if (normalizedPath.startsWith(NEWS_STORAGE_PREFIX)) {
        return normalizedPath;
    }

    try {
        const parsedUrl = new URL(normalizedValue, 'http://localhost');
        const marker = `/storage/v1/object/public/${NEWS_IMAGES_BUCKET}/`;
        const storagePathIndex = parsedUrl.pathname.indexOf(marker);

        if (storagePathIndex >= 0) {
            const filePath = decodeURIComponent(parsedUrl.pathname.slice(storagePathIndex + marker.length));
            return `${NEWS_STORAGE_PREFIX}${filePath}`;
        }
    } catch {
        // Keep the original value when it is not a valid URL.
    }

    return normalizedPath;
}

function getNewsStorageFilePath(imagePath) {
    const normalizedPath = normalizeStoredNewsImagePath(imagePath);

    if (!normalizedPath.startsWith(NEWS_STORAGE_PREFIX)) {
        return '';
    }

    return normalizedPath.slice(NEWS_STORAGE_PREFIX.length);
}

function normalizeNewsItem(news) {
    return {
        id: news.id,
        title: news.title,
        date: news.date,
        person: news.person || [],
        tag: news.tag || '',
        image: normalizeStoredNewsImagePath(news.image),
        description: news.description || '',
        published: news.published !== false,
        sort_order: typeof news.sort_order === 'number' ? news.sort_order : null
    };
}

function getLocalNews() {
    return localData.posts.map(normalizeNewsItem);
}

function sanitizePathSegment(value) {
    return `${value || ''}`
        .toLowerCase()
        .replace(/[^a-z0-9-_]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .slice(0, 80) || 'news-item';
}

function sanitizeFileName(name) {
    const lastDotIndex = name.lastIndexOf('.');
    const baseName = lastDotIndex >= 0 ? name.slice(0, lastDotIndex) : name;
    const extension = lastDotIndex >= 0 ? name.slice(lastDotIndex).toLowerCase() : '';

    return `${sanitizePathSegment(baseName)}${extension}`;
}

export function resolveNewsImageUrl(imagePath) {
    if (!imagePath) {
        return '';
    }

    if (imagePath.startsWith('data:') || imagePath.startsWith('blob:')) {
        return imagePath;
    }

    const storageFilePath = getNewsStorageFilePath(imagePath);

    if (storageFilePath && isSupabaseConfigured && supabase) {
        const {
            data: { publicUrl }
        } = supabase.storage.from(NEWS_IMAGES_BUCKET).getPublicUrl(storageFilePath);

        return publicUrl;
    }

    if (/^(https?:)?\/\//i.test(imagePath)) {
        return imagePath;
    }

    const normalizedPath = imagePath.replace(/^\/+/, '');
    return `${import.meta.env.BASE_URL || '/'}${normalizedPath}`;
}

function sortNewsItems(items) {
    return items.sort((firstItem, secondItem) => {
        const firstSortOrder = typeof firstItem.sort_order === 'number' ? firstItem.sort_order : Number.MAX_SAFE_INTEGER;
        const secondSortOrder = typeof secondItem.sort_order === 'number' ? secondItem.sort_order : Number.MAX_SAFE_INTEGER;

        if (firstSortOrder !== secondSortOrder) {
            return firstSortOrder - secondSortOrder;
        }

        return `${secondItem.date || ''}`.localeCompare(`${firstItem.date || ''}`);
    });
}

function mergeNewsItems(localItems, remoteItems) {
    const mergedItems = new Map();

    localItems.forEach((item) => {
        mergedItems.set(item.id, item);
    });

    remoteItems.forEach((item) => {
        mergedItems.set(item.id, item);
    });

    return sortNewsItems(Array.from(mergedItems.values()));
}

async function getRemoteNews(includeDrafts = false) {
    const query = supabase
        .from('news_posts')
        .select('id, title, date, person, tag, image, description, published, sort_order')
        .order('sort_order', { ascending: true, nullsFirst: false })
        .order('date', { ascending: false });

    if (!includeDrafts) {
        query.eq('published', true);
    }

    const { data, error } = await query;

    if (error) {
        throw error;
    }

    return (data || []).map(normalizeNewsItem);
}

const NewsResource = {
    async getNews() {
        const localNews = getLocalNews();

        if (!isSupabaseConfigured || !supabase) {
            return sortNewsItems(localNews);
        }

        try {
            const remoteNews = await getRemoteNews(false);
            return mergeNewsItems(localNews, remoteNews);
        } catch (error) {
            console.warn('Falling back to local news data.', error);
            return sortNewsItems(localNews);
        }
    },

    async getNewsById(id) {
        const news = await this.getNews();
        return news.find((item) => item.id === id) || null;
    },

    async getAdminNews() {
        if (!isSupabaseConfigured || !supabase) {
            return getLocalNews();
        }

        return getRemoteNews(true);
    },

    async upsertNewsItem(newsItem) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const payload = {
            id: newsItem.id,
            title: newsItem.title,
            date: newsItem.date,
            person: newsItem.person || [],
            tag: newsItem.tag || '',
            image: normalizeStoredNewsImagePath(newsItem.image),
            description: newsItem.description || '',
            published: newsItem.published !== false
        };

        const { data, error } = await supabase
            .from('news_posts')
            .upsert(payload)
            .select()
            .single();

        if (error) {
            throw error;
        }

        return normalizeNewsItem(data);
    },

    async uploadNewsImage(file, newsId) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        if (!file) {
            throw new Error('Choose an image before uploading.');
        }

        const safeNewsId = sanitizePathSegment(newsId);
        const safeFileName = sanitizeFileName(file.name || 'upload-image');
        const filePath = `${safeNewsId}/${Date.now()}-${safeFileName}`;

        const { error } = await supabase.storage
            .from(NEWS_IMAGES_BUCKET)
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
        } = supabase.storage.from(NEWS_IMAGES_BUCKET).getPublicUrl(filePath);

        return {
            filePath: `${NEWS_STORAGE_PREFIX}${filePath}`,
            publicUrl
        };
    },

    async deleteNewsItem(id) {
        if (!isSupabaseConfigured || !supabase) {
            throw new Error('Supabase is not configured.');
        }

        const { error } = await supabase
            .from('news_posts')
            .delete()
            .eq('id', id);

        if (error) {
            throw error;
        }
    }
};

export default NewsResource;
