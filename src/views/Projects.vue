<template>
    <section class="projects_page container py-4">
        <div class="hero row align-items-end g-4 mb-4">
            <div class="col-lg-8">
                <p class="eyebrow mb-2" :style="{ color: secundary_color }">Research Portfolio</p>
                <h1 class="display_title">Projects</h1>
                <p class="lead_copy">
                    Explore active and past RESHAPE Lab projects, including funding, research areas, collaborators, and related articles.
                </p>
            </div>
        </div>

        <div class="row g-4">
            <div
                v-for="project in projects"
                :key="project.slug"
                class="col-12"
            >
                <article
                    class="project_card card border-0 shadow-sm overflow-hidden"
                    role="button"
                    tabindex="0"
                    @click="goToProject(project.slug)"
                    @keydown.enter.prevent="goToProject(project.slug)"
                    @keydown.space.prevent="goToProject(project.slug)"
                >
                    <div class="row g-0">
                        <div class="col-lg-4" v-if="project.image">
                            <img :src="resolveImage(project.image)" class="project_image" :alt="project.title">
                        </div>

                        <div :class="project.image ? 'col-lg-8' : 'col-12'">
                            <div class="card-body p-4 p-lg-5">
                                <div class="d-flex flex-wrap gap-2 mb-3">
                                    <span class="badge rounded-pill text-dark" :style="{ backgroundColor: secundary_color }">
                                        {{ project.funding || 'Funding not listed' }}
                                    </span>
                                    <span
                                        v-for="area in project.researchAreas"
                                        :key="`${project.slug}-${area}`"
                                        class="badge rounded-pill bg-light text-dark border"
                                    >
                                        {{ area }}
                                    </span>
                                </div>

                                <h2 class="h3 mb-3">{{ project.title }}</h2>
                                <p class="mb-3">{{ project.shortDescription || project.description }}</p>
                                <button class="detail_button" @click.stop="goToProject(project.slug)">
                                    View Project
                                </button>

                                <div class="row g-4">
                                    <div class="col-md-6">
                                        <h3 class="section_label">People</h3>
                                        <ul class="list_block">
                                            <li
                                                v-for="person in project.people"
                                                :key="`${project.slug}-${person}`"
                                            >
                                                {{ person }}
                                            </li>
                                            <li v-if="!project.people.length">No people listed</li>
                                        </ul>
                                    </div>

                                    <div class="col-md-6">
                                        <h3 class="section_label">Articles</h3>
                                        <ul class="list_block">
                                            <li
                                                v-for="articleTitle in project.articleTitles"
                                                :key="`${project.slug}-${articleTitle}`"
                                            >
                                                {{ articleTitle }}
                                            </li>
                                            <li v-if="!project.articleTitles.length">No article titles listed</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </article>
            </div>
        </div>
    </section>
</template>

<script>
import research_lab from '../../public/research_lab.json';
import ProjectsResource, { resolveProjectImageUrl } from '../api/resource/projects';

export default {
    name: 'Projects',

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            projects: []
        };
    },

    created() {
        this.loadProjects();
    },

    methods: {
        async loadProjects() {
            try {
                this.projects = await ProjectsResource.getProjects();
            } catch (error) {
                console.error('An error occurred:', error);
            }
        },

        resolveImage(imagePath) {
            return resolveProjectImageUrl(imagePath);
        },

        goToProject(slug) {
            this.$router.push({
                name: 'project-detail',
                params: {
                    slug
                }
            });
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
    font-family: 'NATS', sans-serif;
}

.projects_page {
    max-width: 1100px;
}

.hero {
    min-height: 220px;
}

.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 1rem;
}

.display_title {
    font-size: clamp(2.5rem, 7vw, 5rem);
    line-height: 0.95;
    margin: 0;
}

.lead_copy {
    max-width: 760px;
    font-size: 1.2rem;
    margin-top: 1rem;
}

.project_card {
    border-radius: 28px;
    cursor: pointer;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.project_card:hover,
.project_card:focus-visible {
    transform: translateY(-2px);
    box-shadow: 0 18px 36px rgba(25, 31, 44, 0.14);
    outline: none;
}

.project_image {
    width: 100%;
    height: 100%;
    min-height: 260px;
    object-fit: cover;
}

.detail_button {
    border: none;
    border-radius: 999px;
    padding: 10px 18px;
    margin-bottom: 24px;
    background: #1f3144;
    color: white;
    font-size: 1rem;
}

.section_label {
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.8rem;
}

.list_block {
    margin: 0;
    padding-left: 1.2rem;
}

.list_block li {
    margin-bottom: 0.45rem;
}
</style>
