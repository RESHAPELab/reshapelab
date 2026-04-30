<template>
    <div class="project_detail_page">
        <div class="hero" :style="{ backgroundColor: primary_color }">
            <div class="hero_content">
                <button class="back_button" @click="goBack">
                    Back to Projects
                </button>

                <p class="eyebrow" :style="{ color: secundary_color }"> PROJECT DETAIL </p>
                <p class="title">{{ project?.title || 'Loading project...' }}</p>
                <p v-if="project?.funding" class="hero_meta">{{ project.funding }}</p>
                <p v-if="project?.shortDescription || project?.description" class="hero_summary">
                    {{ project?.shortDescription || project?.description }}
                </p>
            </div>
        </div>

        <div class="content">
            <div v-if="isLoading" class="status_card">
                Loading project details...
            </div>

            <div v-else-if="errorMessage" class="status_card">
                {{ errorMessage }}
            </div>

            <template v-else-if="project">
                <div class="media_card" v-if="project.image">
                    <img :src="resolveImage(project.image)" class="project_image" :alt="project.title">
                </div>

                <div class="info_card">
                    <p class="section_title"> Overview </p>

                    <div class="overview_grid">
                        <div class="overview_item">
                            <span class="overview_label">Funding</span>
                            <span>{{ project.funding || 'Not listed' }}</span>
                        </div>

                        <div class="overview_item">
                            <span class="overview_label">Research Areas</span>
                            <span>{{ project.researchAreas.length ? project.researchAreas.join(', ') : 'Not listed' }}</span>
                        </div>

                        <div class="overview_item">
                            <span class="overview_label">People</span>
                            <span>{{ project.people.length ? project.people.length : 0 }}</span>
                        </div>

                        <div class="overview_item">
                            <span class="overview_label">Related Articles</span>
                            <span>{{ project.articleTitles.length ? project.articleTitles.length : 0 }}</span>
                        </div>
                    </div>
                </div>

                <div class="info_card" v-if="project.description">
                    <p class="section_title"> Description </p>
                    <p class="body_text">{{ project.description }}</p>
                </div>

                <div class="detail_grid">
                    <div class="info_card">
                        <p class="section_title"> Research Areas </p>
                        <div v-if="project.researchAreas.length" class="pill_row">
                            <span
                                v-for="area in project.researchAreas"
                                :key="`${project.slug}-${area}`"
                                class="info_pill"
                            >
                                {{ area }}
                            </span>
                        </div>
                        <p v-else class="body_text muted_text">No research areas listed for this project.</p>
                    </div>

                    <div class="info_card">
                        <p class="section_title"> People </p>
                        <div v-if="project.people.length" class="link_list">
                            <router-link
                                v-for="person in project.people"
                                :key="`${project.slug}-${person}`"
                                class="person_link"
                                :to="getPersonRoute(person)"
                            >
                                {{ person }}
                            </router-link>
                        </div>
                        <p v-else class="body_text muted_text">No people listed for this project.</p>
                    </div>
                </div>

                <div class="info_card">
                    <p class="section_title"> Related Articles </p>
                    <ul v-if="project.articleTitles.length" class="article_list">
                        <li
                            v-for="articleTitle in project.articleTitles"
                            :key="`${project.slug}-${articleTitle}`"
                        >
                            {{ articleTitle }}
                        </li>
                    </ul>
                    <p v-else class="body_text muted_text">No related article titles listed for this project.</p>
                </div>
            </template>
        </div>
    </div>
</template>

<script>
import research_lab from '../../public/research_lab.json';
import ProjectsResource, { resolveProjectImageUrl } from '../api/resource/projects';

function slugifyPersonName(name) {
    return `${name || ''}`
        .trim()
        .replace(/\s+/g, '-');
}

export default {
    name: 'ProjectDetail',

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            project: null,
            isLoading: true,
            errorMessage: ''
        };
    },

    methods: {
        async loadProject() {
            this.isLoading = true;
            this.errorMessage = '';

            try {
                const project = await ProjectsResource.getProjectBySlug(this.$route.params.slug);

                if (!project) {
                    this.errorMessage = 'We could not find that project.';
                    this.project = null;
                    return;
                }

                this.project = project;
            } catch (error) {
                console.error('An error occurred:', error);
                this.project = null;
                this.errorMessage = 'The project details could not be loaded right now.';
            } finally {
                this.isLoading = false;
            }
        },

        resolveImage(imagePath) {
            return resolveProjectImageUrl(imagePath);
        },

        getPersonRoute(personName) {
            return {
                name: 'researcher',
                params: {
                    researcher_name: slugifyPersonName(personName)
                }
            };
        },

        goBack() {
            if (window.history.length > 1) {
                this.$router.back();
                return;
            }

            this.$router.push({ name: 'projects' });
        }
    },

    created() {
        this.loadProject();
    },

    watch: {
        '$route.params.slug'() {
            this.loadProject();
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

.project_detail_page {
    min-height: 100vh;
    background: linear-gradient(180deg, #f7f3eb 0%, #ffffff 38%);
}

.hero {
    display: flex;
    justify-content: center;
    padding: 32px 16px;
}

.hero_content {
    width: min(1080px, 100%);
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
    font-size: min(11vw, 62px);
    line-height: 0.95;
    margin-top: 8px;
}

.hero_meta,
.hero_summary {
    color: white;
    font-size: 24px;
    margin-top: 14px;
    max-width: 860px;
}

.content {
    width: min(1080px, calc(100% - 32px));
    margin: -24px auto 0;
    padding-bottom: 40px;
}

.media_card,
.info_card,
.status_card {
    background: white;
    border-radius: 28px;
    box-shadow: 0 12px 30px rgba(25, 31, 44, 0.08);
    padding: 24px;
    margin-bottom: 18px;
}

.media_card {
    padding: 0;
    overflow: hidden;
}

.project_image {
    width: 100%;
    max-height: 480px;
    object-fit: cover;
    display: block;
}

.section_title {
    font-size: 34px;
    margin-bottom: 18px;
}

.overview_grid,
.detail_grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
}

.detail_grid {
    align-items: start;
}

.overview_item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 16px;
    border-radius: 18px;
    background: #f6f2ea;
}

.overview_label {
    font-size: 18px;
    color: #586274;
}

.body_text,
.article_list,
.person_link {
    font-size: 24px;
    line-height: 1.2;
}

.muted_text {
    color: #586274;
}

.pill_row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}

.info_pill {
    border-radius: 999px;
    padding: 10px 14px;
    background: #f6f2ea;
    font-size: 20px;
}

.link_list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.person_link {
    text-decoration: none;
    color: #2b4f7c;
}

.person_link:hover {
    text-decoration: underline;
}

.article_list {
    margin: 0;
    padding-left: 24px;
}

.article_list li + li {
    margin-top: 10px;
}

@media (max-width: 700px) {
    .title {
        font-size: min(13vw, 44px);
    }

    .hero_meta,
    .hero_summary,
    .body_text,
    .article_list,
    .person_link {
        font-size: 20px;
    }

    .section_title {
        font-size: 28px;
    }
}
</style>
