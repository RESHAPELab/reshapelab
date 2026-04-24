<template>
    <section class="funding_page container py-4">
        <div class="hero row align-items-end g-4 mb-4">
            <div class="col-lg-8">
                <p class="eyebrow mb-2" :style="{ color: secundary_color }">Support</p>
                <h1 class="display_title">Funding</h1>
                <p class="lead_copy">
                    Current and past awards that support the lab's research areas, projects, and collaborations.
                </p>
            </div>
        </div>

        <div class="row g-4">
            <div
                v-for="item in fundingItems"
                :key="item.id"
                class="col-12"
            >
                <article class="funding_card card border-0 shadow-sm">
                    <div class="card-body p-4 p-lg-5">
                        <div class="d-flex flex-wrap gap-2 mb-3">
                            <span class="badge rounded-pill text-dark" :style="{ backgroundColor: secundary_color }">
                                {{ item.id }}
                            </span>
                            <span class="badge rounded-pill bg-light text-dark border">
                                {{ fundingRange(item) }}
                            </span>
                        </div>

                        <h2 class="h3 mb-3">{{ item.name }}</h2>

                        <div class="info_grid mb-3">
                            <div>
                                <p class="section_label">Amount</p>
                                <p class="mb-0">{{ item.total_amount || 'Not listed' }}</p>
                            </div>

                            <div>
                                <p class="section_label">Related Projects</p>
                                <ul class="list_block">
                                    <li
                                        v-for="project in item.projects"
                                        :key="`${item.id}-${project}`"
                                    >
                                        {{ project }}
                                    </li>
                                    <li v-if="!item.projects.length">No related projects listed</li>
                                </ul>
                            </div>
                        </div>

                        <a
                            v-if="item.access_link"
                            class="detail_button"
                            :href="item.access_link"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            View Award
                        </a>
                    </div>
                </article>
            </div>
        </div>
    </section>
</template>

<script>
import research_lab from '../../public/research_lab.json';
import FundingResource from '../api/resource/funding';

export default {
    name: 'Funding',

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            fundingItems: []
        };
    },

    created() {
        this.loadFunding();
    },

    methods: {
        async loadFunding() {
            try {
                this.fundingItems = await FundingResource.getFunding();
            } catch (error) {
                console.error('An error occurred:', error);
            }
        },

        fundingRange(item) {
            if (item.initial_date && item.final_date) {
                return `${item.initial_date} - ${item.final_date}`;
            }

            return item.initial_date || item.final_date || 'Dates not listed';
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

.funding_page {
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

.funding_card {
    border-radius: 28px;
}

.info_grid {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.section_label {
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.4rem;
}

.list_block {
    margin: 0;
    padding-left: 1.2rem;
}

.list_block li {
    margin-bottom: 0.45rem;
}

.detail_button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 44px;
    padding: 0 18px;
    border-radius: 999px;
    text-decoration: none;
    background: #1f3144;
    color: white;
}
</style>
