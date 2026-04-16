import localData from '/public/posts.json';
import { isSupabaseConfigured, supabase } from '../../lib/supabase';

function normalizeNewsItem(news) {
    return {
        id: news.id,
        title: news.title,
        date: news.date,
        person: news.person || [],
        tag: news.tag || '',
        image: news.image || '',
        description: news.description || '',
        published: news.published !== false
    };
}

function getLocalNews() {
    return localData.posts.map(normalizeNewsItem);
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
        if (!isSupabaseConfigured || !supabase) {
            return getLocalNews();
        }

        try {
            return await getRemoteNews(false);
        } catch (error) {
            console.warn('Falling back to local news data.', error);
            return getLocalNews();
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
            image: newsItem.image || '',
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
