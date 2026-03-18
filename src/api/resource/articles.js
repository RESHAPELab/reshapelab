import Cite from 'citation-js';
import MembersResource from '../resource/people.js';

const LOCAL_BIB_ROUTE = 'papers.bib';
const DBLP_BIB_URL = 'https://dblp.org/pid';
const CACHE_PREFIX = 'dblp-bib-cache:';
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

function getCacheKey(pid) {
    return `${CACHE_PREFIX}${pid}`;
}

function readCache(pid) {
    if (typeof window === 'undefined' || !window.localStorage) {
        return null;
    }

    const rawValue = window.localStorage.getItem(getCacheKey(pid));

    if (!rawValue) {
        return null;
    }

    try {
        const parsedValue = JSON.parse(rawValue);

        if (!parsedValue.timestamp || !parsedValue.data) {
            return null;
        }

        if (Date.now() - parsedValue.timestamp > CACHE_TTL_MS) {
            window.localStorage.removeItem(getCacheKey(pid));
            return null;
        }

        return parsedValue.data;
    } catch (error) {
        window.localStorage.removeItem(getCacheKey(pid));
        return null;
    }
}

function writeCache(pid, data) {
    if (typeof window === 'undefined' || !window.localStorage) {
        return;
    }

    const value = JSON.stringify({
        timestamp: Date.now(),
        data
    });

    window.localStorage.setItem(getCacheKey(pid), value);
}

async function fetchBibText(bibRoute) {
    const response = await fetch(bibRoute);

    if (!response.ok) {
        throw new Error(`Failed to fetch bibliography from ${bibRoute}`);
    }

    return response.text();
}

function parseBibText(bibText) {
    return Cite.input(bibText);
}

function getArticleYear(article) {
    return article?.issued?.['date-parts']?.[0]?.[0] || 0;
}

function normalizeContainerTitle(article) {
    if (Array.isArray(article['container-title'])) {
        return article['container-title'].join(', ');
    }

    return article['container-title'] || article.publisher || 'Publication';
}

function normalizeAuthors(article) {
    if (!Array.isArray(article.author)) {
        return [];
    }

    return article.author.map((author) => ({
        given: author.given || '',
        family: author.family || author.literal || ''
    }));
}

function normalizeArticle(article) {
    return {
        ...article,
        DOI: article.DOI || article.doi || '',
        URL: article.URL || article.url || '',
        author: normalizeAuthors(article),
        'container-title': normalizeContainerTitle(article)
    };
}

function normalizeArticles(articles) {
    return articles
        .map(normalizeArticle)
        .sort((firstArticle, secondArticle) => getArticleYear(secondArticle) - getArticleYear(firstArticle));
}

function matchesAnyAuthorName(article, names) {
    if (!Array.isArray(article.author) || !Array.isArray(names) || names.length === 0) {
        return false;
    }

    const normalizedNames = names.map((name) => name.toLowerCase());

    return article.author.some((author) => {
        const authorName = `${author.given || ''} ${author.family || author.literal || ''}`.trim().toLowerCase();
        return normalizedNames.some((name) => authorName.includes(name));
    });
}

function dedupeArticles(articles) {
    const seenArticles = new Set();

    return articles.filter((article) => {
        const identifier = (
            article.DOI ||
            `${article.title || ''}:${getArticleYear(article)}:${article.author?.map((author) => `${author.given} ${author.family}`).join('|') || ''}`
        ).toLowerCase();

        if (seenArticles.has(identifier)) {
            return false;
        }

        seenArticles.add(identifier);
        return true;
    });
}

async function getLocalArticles() {
    const bibText = await fetchBibText(LOCAL_BIB_ROUTE);
    return normalizeArticles(parseBibText(bibText));
}

async function getDblpArticlesByPid(pid) {
    if (!pid) {
        return [];
    }

    const cachedBibText = readCache(pid);

    if (cachedBibText) {
        return normalizeArticles(parseBibText(cachedBibText));
    }

    const bibText = await fetchBibText(`${DBLP_BIB_URL}/${pid}.bib`);
    writeCache(pid, bibText);
    return normalizeArticles(parseBibText(bibText));
}

const ArticlesResource = {
    async getArticlesByAuthor(names) {
        const localArticles = await getLocalArticles();
        return localArticles.filter((article) => matchesAnyAuthorName(article, names));
    },

    async getArticlesByDblpPid(pid) {
        return getDblpArticlesByPid(pid);
    },

    async getArticlesForMember(member) {
        if (member?.dblpPid) {
            try {
                return await getDblpArticlesByPid(member.dblpPid);
            } catch (error) {
                console.warn(`Falling back to local bibliography for ${member.firstName} ${member.lastName}.`, error);
            }
        }

        return this.getArticlesByAuthor(member?.author_name || []);
    },

    async getAllArticles() {
        const members = await MembersResource.getMembers();
        const membersWithDblpPid = members.filter((member) => member.dblpPid);

        if (membersWithDblpPid.length === 0) {
            return getLocalArticles();
        }

        const articleCollections = await Promise.all(
            membersWithDblpPid.map(async (member) => {
                try {
                    return await getDblpArticlesByPid(member.dblpPid);
                } catch (error) {
                    console.warn(`Skipping DBLP publications for ${member.firstName} ${member.lastName}.`, error);
                    return [];
                }
            })
        );

        const mergedArticles = dedupeArticles(articleCollections.flat());

        if (mergedArticles.length > 0) {
            return mergedArticles.sort((firstArticle, secondArticle) => getArticleYear(secondArticle) - getArticleYear(firstArticle));
        }

        return getLocalArticles();
    },

    async getArticlesByYear(year) {
        const allArticles = await this.getAllArticles();

        const filteredArticles = allArticles.filter((article) => {
            return getArticleYear(article) === year;
        });

        const articlesWithAuthors = await Promise.all(filteredArticles.map(async (article) => {
            const authorNames = article.author
                ? article.author.map((author) => `${author.given} ${author.family}`.trim())
                : [];
            const nauAuthors = await MembersResource.getMemberByAuthorName(authorNames);
            return { ...article, nau_authors: nauAuthors };
        }));

        return articlesWithAuthors;
    }
};

export default ArticlesResource;
