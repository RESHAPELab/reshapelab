import { createClient } from '@supabase/supabase-js';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, '..');
const publicDir = path.join(projectRoot, 'public');
const newsBucket = 'news-images';
const peopleBucket = 'people-images';

function loadEnvFile() {
    const envPath = path.join(projectRoot, '.env');

    return fs.readFile(envPath, 'utf8')
        .then((contents) => {
            contents.split(/\r?\n/).forEach((line) => {
                const trimmed = line.trim();

                if (!trimmed || trimmed.startsWith('#')) {
                    return;
                }

                const equalsIndex = trimmed.indexOf('=');

                if (equalsIndex < 0) {
                    return;
                }

                const key = trimmed.slice(0, equalsIndex).trim();
                const rawValue = trimmed.slice(equalsIndex + 1).trim();
                const unwrappedValue = rawValue.replace(/^['"]|['"]$/g, '');

                if (!(key in process.env)) {
                    process.env[key] = unwrappedValue;
                }
            });
        })
        .catch(() => {
            // The project can still run if the caller provided env vars directly.
        });
}

function getContentType(filePath) {
    const extension = path.extname(filePath).toLowerCase();

    switch (extension) {
    case '.png':
        return 'image/png';
    case '.jpg':
    case '.jpeg':
        return 'image/jpeg';
    case '.gif':
        return 'image/gif';
    case '.webp':
        return 'image/webp';
    case '.svg':
        return 'image/svg+xml';
    default:
        return 'application/octet-stream';
    }
}

function toPosixPath(filePath) {
    return filePath.split(path.sep).join('/');
}

function getLocalAssetPath(relativePath) {
    return path.join(publicDir, relativePath.replace(/^\/+/, ''));
}

function isLocalAssetPath(value, prefix) {
    return typeof value === 'string' && value.replace(/^(\.\.\/|\.\/)+/, '').startsWith(prefix);
}

async function readJson(relativePath) {
    const contents = await fs.readFile(path.join(projectRoot, relativePath), 'utf8');
    return JSON.parse(contents);
}

async function ensureBucket(supabase, bucketName) {
    const { error } = await supabase.storage.createBucket(bucketName, {
        public: true
    });

    if (error && !/already exists/i.test(error.message || '')) {
        throw error;
    }
}

async function uploadAssetIfNeeded(supabase, bucketName, sourcePath, storagePath, cache = new Map()) {
    const cacheKey = `${bucketName}:${sourcePath}`;

    if (cache.has(cacheKey)) {
        return cache.get(cacheKey);
    }

    const fileBuffer = await fs.readFile(getLocalAssetPath(sourcePath));
    const normalizedStoragePath = toPosixPath(storagePath);

    const { error: uploadError } = await supabase.storage
        .from(bucketName)
        .upload(normalizedStoragePath, fileBuffer, {
            upsert: true,
            cacheControl: '3600',
            contentType: getContentType(sourcePath)
        });

    if (uploadError) {
        throw uploadError;
    }

    const {
        data: { publicUrl }
    } = supabase.storage.from(bucketName).getPublicUrl(normalizedStoragePath);

    const result = {
        storagePath: normalizedStoragePath,
        publicUrl
    };

    cache.set(cacheKey, result);
    return result;
}

function collectDescriptionImagePaths(description) {
    const matches = [];
    const pattern = /<img\b[^>]*\bsrc=['"]([^'"]+)['"][^>]*>/gi;
    let match = pattern.exec(description || '');

    while (match) {
        matches.push(match[1]);
        match = pattern.exec(description || '');
    }

    return matches;
}

async function importNews(supabase) {
    const { posts } = await readJson('public/posts.json');
    const uploadCache = new Map();
    const assetMap = new Map();

    for (const post of posts) {
        const candidatePaths = [post.image, ...collectDescriptionImagePaths(post.description)];

        for (const candidatePath of candidatePaths) {
            if (!isLocalAssetPath(candidatePath, 'images/posts/')) {
                continue;
            }

            const normalizedSourcePath = candidatePath.replace(/^(\.\.\/)+/, '');
            const storagePath = normalizedSourcePath.replace(/^images\/posts\//, '');
            const uploadedAsset = await uploadAssetIfNeeded(
                supabase,
                newsBucket,
                normalizedSourcePath,
                storagePath,
                uploadCache
            );

            assetMap.set(candidatePath, uploadedAsset);
            assetMap.set(normalizedSourcePath, uploadedAsset);
        }
    }

    const payload = posts.map((post) => {
        const primaryImage = assetMap.get(post.image);
        let description = post.description || '';

        assetMap.forEach((asset, sourcePath) => {
            if (!sourcePath) {
                return;
            }

            const escapedSourcePath = sourcePath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            description = description.replace(new RegExp(escapedSourcePath, 'g'), asset.publicUrl);
        });

        return {
            id: post.id,
            title: post.title,
            date: post.date,
            person: post.person || [],
            tag: post.tag || '',
            image: primaryImage ? `${newsBucket}/${primaryImage.storagePath}` : post.image || '',
            description,
            published: post.published !== false,
            sort_order: typeof post.sort_order === 'number' ? post.sort_order : null
        };
    });

    const { error } = await supabase.from('news_posts').upsert(payload, {
        onConflict: 'id'
    });

    if (error) {
        throw error;
    }

    return {
        postsImported: payload.length,
        newsImagesUploaded: uploadCache.size
    };
}

async function importPeople(supabase) {
    const { members } = await readJson('public/members.json');
    const uploadCache = new Map();

    const payload = [];

    for (const member of members) {
        const photos = { ...(member.photos || {}) };

        for (const [photoKey, photoPath] of Object.entries(photos)) {
            if (!isLocalAssetPath(photoPath, 'images/people/')) {
                continue;
            }

            const storagePath = photoPath.replace(/^images\/people\//, '');
            const uploadedAsset = await uploadAssetIfNeeded(
                supabase,
                peopleBucket,
                photoPath,
                storagePath,
                uploadCache
            );

            photos[photoKey] = `${peopleBucket}/${uploadedAsset.storagePath}`;
        }

        payload.push({
            slug: member.slug || `${member.first_name || ''} ${member.last_name || ''}`.trim().replace(/ /g, '-'),
            first_name: member.first_name,
            last_name: member.last_name,
            role: member.role,
            description: member.description || '',
            contacts: member.contacts || {},
            photos,
            research_keywords: member.research_keywords || [],
            highlighted_publications: member.highlighted_publications || [],
            author_name: member.author_name || [],
            dblp_pid: member.dblp_pid || '',
            projects: member.projects || [],
            is_active: member.is_active !== false
        });
    }

    const { error } = await supabase.from('people_profiles').upsert(payload, {
        onConflict: 'slug'
    });

    if (error) {
        throw error;
    }

    return {
        peopleImported: payload.length,
        peopleImagesUploaded: uploadCache.size
    };
}

async function main() {
    await loadEnvFile();

    const supabaseUrl = process.env.VITE_SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !serviceRoleKey) {
        throw new Error(
            'Missing VITE_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY. Add them to .env before running the import.'
        );
    }

    const supabase = createClient(supabaseUrl, serviceRoleKey, {
        auth: {
            persistSession: false,
            autoRefreshToken: false
        }
    });

    await ensureBucket(supabase, newsBucket);
    await ensureBucket(supabase, peopleBucket);

    const newsResult = await importNews(supabase);
    const peopleResult = await importPeople(supabase);

    console.log('Supabase import complete.');
    console.log(JSON.stringify({ ...newsResult, ...peopleResult }, null, 2));
}

main().catch((error) => {
    console.error('Supabase import failed.');
    console.error(error.message || error);
    process.exitCode = 1;
});
