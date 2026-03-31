<template>
    <div class="publication_page">
        <div class="hero" :style="{ backgroundColor: primary_color }">
            <div class="hero_content">
                <button class="back_button" @click="goBack">
                    Back to Publications
                </button>

                <p class="eyebrow" :style="{ color: secundary_color }"> PUBLICATION DETAIL </p>
                <p class="title">{{ article?.title || 'Loading publication...' }}</p>

                <p v-if="article" class="meta">
                    {{ authorLine }}
                </p>

                <p v-if="article" class="meta">
                    {{ venueLine }}
                </p>
            </div>
        </div>

        <div class="content">
            <div v-if="isLoading" class="status_card">
                Loading publication details...
            </div>

            <div v-else-if="errorMessage" class="status_card">
                {{ errorMessage }}
            </div>

            <template v-else-if="article">
                <div class="info_card">
                    <p class="section_title"> Overview </p>

                    <div class="overview_grid">
                        <div class="overview_item">
                            <span class="overview_label">Year</span>
                            <span>{{ publicationYear || 'Not available' }}</span>
                        </div>

                        <div class="overview_item">
                            <span class="overview_label">DOI</span>
                            <a v-if="article.DOI" :href="doiLink" target="_blank" rel="noopener noreferrer">{{ article.DOI }}</a>
                            <span v-else>Not available</span>
                        </div>

                        <div class="overview_item">
                            <span class="overview_label">Venue</span>
                            <span>{{ article['container-title'] || 'Not available' }}</span>
                        </div>

                        <div class="overview_item">
                            <span class="overview_label">Abstract</span>
                            <span>{{ article.abstract ? 'Available below' : 'Not available' }}</span>
                        </div>
                    </div>

                    <div class="button_row">
                        <a v-if="article.landingPageUrl" class="action_button" :href="article.landingPageUrl" target="_blank" rel="noopener noreferrer">
                            Open Publisher Page
                        </a>

                        <a v-if="article.pdfUrl" class="action_button secondary" :href="article.pdfUrl" target="_blank" rel="noopener noreferrer">
                            Open PDF
                        </a>
                    </div>
                </div>

                <div class="info_card">
                    <p class="section_title"> Abstract </p>
                    <p class="body_text">
                        {{ article.abstract || 'An abstract was not available from the connected metadata source for this publication.' }}
                    </p>
                </div>

                <div class="info_card">
                    <p class="section_title"> PDF Preview </p>
                    <div v-if="article.pdfUrl" class="pdf_panel">
                        <iframe
                            class="pdf_frame"
                            :src="article.pdfUrl"
                            title="Publication PDF preview"
                        />
                        <p class="helper_text">
                            Some publishers block embedded PDF previews. If the frame stays blank, use the Open PDF button above.
                        </p>
                    </div>

                    <p v-else class="body_text">
                        No direct PDF URL was available for this publication.
                    </p>
                </div>
            </template>
        </div>
    </div>
</template>

<script>
import research_lab from '../../public/research_lab.json';
import ArticlesResource from '../api/resource/articles';

export default {
    name: 'PublicationDetail',

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            article: null,
            isLoading: true,
            errorMessage: ''
        };
    },

    computed: {
        publicationYear() {
            return this.article?.issued?.['date-parts']?.[0]?.[0] || '';
        },

        doiLink() {
            return this.article?.DOI ? `https://doi.org/${this.article.DOI}` : '';
        },

        authorLine() {
            if (!Array.isArray(this.article?.author) || this.article.author.length === 0) {
                return 'Authors not available';
            }

            return this.article.author
                .map((author) => `${author.given || ''} ${author.family || ''}`.trim())
                .join(', ');
        },

        venueLine() {
            const venue = this.article?.['container-title'] || 'Venue not available';
            const year = this.publicationYear;

            return year ? `${venue} - ${year}` : venue;
        }
    },

    methods: {
        async loadArticle() {
            this.isLoading = true;
            this.errorMessage = '';

            try {
                const article = await ArticlesResource.getArticleDetailsById(this.$route.params.publication_id);

                if (!article) {
                    this.errorMessage = 'We could not find that publication.';
                    return;
                }

                this.article = article;
            } catch (error) {
                console.error('An error occurred:', error);
                this.errorMessage = 'The publication details could not be loaded right now.';
            } finally {
                this.isLoading = false;
            }
        },

        goBack() {
            if (window.history.length > 1) {
                this.$router.back();
                return;
            }

            this.$router.push({ name: 'publications' });
        }
    },

    created() {
        this.loadArticle();
    },

    watch: {
        '$route.params.publication_id'() {
            this.loadArticle();
        }
    }
}
</script>

<style scoped>
@font-face {
    font-family: 'NATS';
    src: url('/fonts/NATS-Regular.woff');
}

* {
    padding: 0;
    margin: 0;
    box-sizing: border-box;
    font-family: 'NATS', sans-serif;
    color: black;
}

.publication_page {
    min-height: 100vh;
    background: linear-gradient(180deg, #f4f6f8 0%, #ffffff 40%);
}

.hero {
    display: flex;
    justify-content: center;
    padding: 32px 16px;
}

.hero_content {
    width: min(980px, 100%);
}

.back_button {
    border: 1px solid rgba(255, 255, 255, 0.35);
    background: rgba(255, 255, 255, 0.12);
    color: white;
    border-radius: 999px;
    padding: 10px 16px;
    cursor: pointer;
    margin-bottom: 18px;
}

.eyebrow {
    font-size: 22px;
    letter-spacing: 1px;
}

.title {
    color: white;
    font-size: min(11vw, 58px);
    line-height: 0.95;
    margin-top: 8px;
}

.meta {
    color: white;
    font-size: 24px;
    margin-top: 14px;
}

.content {
    width: min(980px, calc(100% - 32px));
    margin: -24px auto 0;
    padding-bottom: 40px;
}

.info_card,
.status_card {
    background: white;
    border-radius: 24px;
    box-shadow: 0 12px 30px rgba(25, 31, 44, 0.08);
    padding: 24px;
    margin-bottom: 18px;
}

.section_title {
    font-size: 34px;
    margin-bottom: 18px;
}

.overview_grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
}

.overview_item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 16px;
    border-radius: 18px;
    background: #f4f6f8;
}

.overview_label {
    font-size: 18px;
    color: #586274;
}

.button_row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 20px;
}

.action_button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    min-height: 48px;
    padding: 0 18px;
    border-radius: 999px;
    background: #3c485e;
    color: white;
}

.action_button.secondary {
    background: #d9b44a;
    color: black;
}

.body_text,
.helper_text {
    font-size: 24px;
    line-height: 1.2;
}

.pdf_panel {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.pdf_frame {
    width: 100%;
    min-height: 640px;
    border: 1px solid #d9dfe7;
    border-radius: 18px;
    background: #f4f6f8;
}

@media (max-width: 700px) {
    .title {
        font-size: min(13vw, 44px);
    }

    .meta,
    .body_text,
    .helper_text {
        font-size: 20px;
    }

    .pdf_frame {
        min-height: 460px;
    }
}
</style>
