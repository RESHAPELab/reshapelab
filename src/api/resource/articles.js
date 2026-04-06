import Cite from 'citation-js';
import MembersResource from '../resource/people.js';

const LOCAL_BIB_ROUTE = 'papers.bib';
const DBLP_BIB_URL = 'https://dblp.org/pid';
const OPEN_ALEX_WORKS_URL = 'https://api.openalex.org/works';
const CACHE_PREFIX = 'dblp-bib-cache:';
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

// Attach 'dblp-bib-cache' to the beginning of an author's DBLP PID
function getCacheKey(pid) {
    return `${CACHE_PREFIX}${pid}`;
}

// Reads BibTeX text from localStorage cache. If entries are older than
// 24 hours or missing, clear the cache
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

// Store BibTeX text in localStorage with timestamp accessed
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

// Request a BibTeX resource and return the response as text
async function fetchBibText(bibRoute) {
    const response = await fetch(bibRoute);

    if (!response.ok) {
        throw new Error(`Failed to fetch bibliography from ${bibRoute}`);
    }

    return response.text();
}

// Request a JSON resource and return the parsed response
async function fetchJson(url) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`Failed to fetch JSON from ${url}`);
    }

    return response.json();
}

// Cite BibTeX text
function parseBibText(bibText) {
    return Cite.input(bibText);
}

// Create a URL-safe ID from a value
function slugify(value) {
    return `${value || ''}`
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

// Create a stable identifier for a paper using DOI if available,
// otherwise title, year, and first author
function getArticleIdentifier(article) {
    const articleTitle = slugify(article?.title || 'publication');
    const articleYear = getArticleYear(article) || 'unknown';
    const firstAuthor = article?.author?.[0]
        ? slugify(`${article.author[0].given || ''} ${article.author[0].family || ''}`)
        : 'author';

    return article?.DOI || article?.doi || `${articleTitle}-${articleYear}-${firstAuthor}`;
}

function getArticleId(article) {
    return slugify(getArticleIdentifier(article));
}

// Get article's publication year, or return 0
function getArticleYear(article) {
    return article?.issued?.['date-parts']?.[0]?.[0] || 0;
}

// Make sure venue name is a usable string by joining the array
function normalizeContainerTitle(article) {
    if (Array.isArray(article['container-title'])) {
        return article['container-title'].join(', ');
    }

    return article['container-title'] || article.publisher || 'Publication';
}

// Split an array of authors into "given" and "family" or "literal" values
function normalizeAuthors(article) {
    if (!Array.isArray(article.author)) {
        return [];
    }

    return article.author.map((author) => ({
        given: author.given || '',
        family: author.family || author.literal || ''
    }));
}

// Composite function organizing article fields into a consistent shape
function normalizeArticle(article) {
    const normalizedAuthors = normalizeAuthors(article);
    const normalizedDoi = article.DOI || article.doi || '';
    const normalizedUrl = article.URL || article.url || '';

    return {
        ...article,
        id: getArticleId({
            ...article,
            DOI: normalizedDoi,
            author: normalizedAuthors
        }),
        DOI: normalizedDoi,
        URL: normalizedUrl,
        abstract: article.abstract || '',
        pdfUrl: article.pdfUrl || '',
        landingPageUrl: article.landingPageUrl || normalizedUrl,
        openAlexId: article.openAlexId || '',
        author: normalizedAuthors,
        'container-title': normalizeContainerTitle(article)
    };
}

// Sort articles descending by year
function normalizeArticles(articles) {
    return articles
        .map(normalizeArticle)
        .sort((firstArticle, secondArticle) => getArticleYear(secondArticle) - getArticleYear(firstArticle));
}

// Check if any author in a paper matches a member's author_name
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

// Remove duplicate articles based on DOI, then title, year, and authors
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

// Fetch papers.bib and format the text (backup)
async function getLocalArticles() {
    const bibText = await fetchBibText(LOCAL_BIB_ROUTE);
    return normalizeArticles(parseBibText(bibText));
}

// First try localStorage, then fetch the DBLP API, cache the BibTeX,
// format it, and return the author's articles
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

// Reconstruct an abstract from OpenAlex's inverted index
function reconstructAbstract(abstractInvertedIndex) {
    if (!abstractInvertedIndex || typeof abstractInvertedIndex !== 'object') {
        return '';
    }

    const orderedWords = [];

    Object.entries(abstractInvertedIndex).forEach(([word, positions]) => {
        positions.forEach((position) => {
            orderedWords[position] = word;
        });
    });

    return orderedWords.filter(Boolean).join(' ');
}

function getOpenAlexPdfUrl(work) {
    const locationWithPdf = [
        work?.primary_location,
        work?.best_oa_location,
        ...(Array.isArray(work?.locations) ? work.locations : [])
    ].find((location) => location?.pdf_url);

    return locationWithPdf?.pdf_url || '';
}

function getOpenAlexLandingPageUrl(work) {
    return (
        work?.primary_location?.landing_page_url ||
        work?.best_oa_location?.landing_page_url ||
        work?.open_access?.oa_url ||
        work?.doi ||
        ''
    );
}

// Normalize the OpenAlex work response into the same article shape
function normalizeOpenAlexWork(work) {
    const doi = work?.doi ? work.doi.replace(/^https?:\/\/doi\.org\//i, '') : '';

    return {
        abstract: reconstructAbstract(work?.abstract_inverted_index),
        pdfUrl: getOpenAlexPdfUrl(work),
        landingPageUrl: getOpenAlexLandingPageUrl(work),
        openAlexId: work?.id || '',
        citationCount: work?.cited_by_count || 0,
        publicationDate: work?.publication_date || '',
        DOI: doi
    };
}

// Fetch a single OpenAlex work by DOI
async function getOpenAlexWorkByDoi(doi) {
    if (!doi) {
        return null;
    }

    const normalizedDoi = doi.replace(/^https?:\/\/doi\.org\//i, '');
    const filterValue = encodeURIComponent(`doi:https://doi.org/${normalizedDoi}`);
    const response = await fetchJson(`${OPEN_ALEX_WORKS_URL}?filter=${filterValue}`);
    const work = response?.results?.[0];

    if (!work) {
        return null;
    }

    return normalizeOpenAlexWork(work);
}

const ArticlesResource = {
    // Uses local papers.bib and filters by author aliases (backup)
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
    },

    async getArticleById(articleId, collection = null) {
        const articles = collection || await this.getAllArticles();
        return articles.find((article) => article.id === articleId) || null;
    },

    async getArticleDetailsById(articleId, collection = null) {
        const article = await this.getArticleById(articleId, collection);

        if (!article) {
            return null;
        }

        if (!article.DOI) {
            return {
                ...article,
                hasRemoteDetails: false
            };
        }

        try {
            const remoteDetails = await getOpenAlexWorkByDoi(article.DOI);

            return normalizeArticle({
                ...article,
                ...remoteDetails
            });
        } catch (error) {
            console.warn(`Unable to fetch OpenAlex details for DOI ${article.DOI}.`, error);

            return {
                ...article,
                hasRemoteDetails: false
            };
        }
    }
};

export default ArticlesResource;
