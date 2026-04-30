<template>
    <div class = "project_container">
        <p class = "title" :style="{ color: primary_color }"> PUBLICATIONS </p>

        <div class = "search_container">
            <input 
                type = "text" 
                v-model = "inputTerm" 
                placeholder = "Search by title, author, year, DOI, or venue..." 
                class = "search_bar"
            >
            
            <button @click="inputTerm ? resetSearch() : search" class="button search_button" :style="{ backgroundColor: primary_color }">
                <img :src="inputTerm ? '/icons/remove.png' : '/icons/search.png'" :alt="inputTerm ? 'Clean' : 'Search'" class="button-icon">
            </button>
        </div>

        <div v-if="!filteredPapers.length" class="empty_state">
            No publications match the current search.
        </div>

        <div v-else class = "published_paper_container">
            <PublishedPaperCard
                v-for="paper in filteredPapers"
                :key="paper.id"
                :title="paper.title"
                :journal="paper['container-title']"
                :year="paper.issued?.['date-parts']?.[0]?.[0]"
                :url="paper.URL"
                :doi="paper.DOI"
                :authors="paper.author"
                :clickable="true"
                @select="openPublication(paper)"
            />
        </div>
    </div>
</template>

<script>
import NavBar from '../components/NavBar.vue';
import research_lab from '../../public/research_lab.json';

import PublishedPaperCard from '../components/cards/PublishedPaperCard.vue';
import ArticlesResource from '../api/resource/articles'

export default {
    name: 'Publications',

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            publishedPapers: [],
            searchTerm: '',
            inputTerm: ''
        };
    },
  
    methods: {
        getAllArticles() {
            ArticlesResource
            .getAllArticles()
            .then((articles) => {
                this.publishedPapers = articles;
            })
            .catch((error) => {
                console.error('An error occurred:', error);
            });
        },

        search() {
            if (this.inputTerm) {
                this.searchTerm = this.inputTerm;
            }
        },

        resetSearch() {
            this.inputTerm = '';
            this.searchTerm = '';
        },

        openPublication(paper) {
            this.$router.push({
                name: 'publication-detail',
                params: {
                    publication_id: paper.id
                }
            });
        },

        getPaperSearchText(paper) {
            const authors = Array.isArray(paper.author)
                ? paper.author.map((author) => `${author.given || ''} ${author.family || ''}`.trim()).join(' ')
                : '';
            const year = paper.issued?.['date-parts']?.[0]?.[0] || '';

            return [
                paper.title,
                paper['container-title'],
                paper.DOI,
                paper.URL,
                authors,
                `${year}`
            ]
                .filter(Boolean)
                .join(' ')
                .toLowerCase();
        }
    },

    created() {
        this.getAllArticles();
    },

    watch: {
        inputTerm(newInputTerm) {
            this.searchTerm = newInputTerm;
        }
    },

    computed: {
        filteredPapers() {
            const lowerCaseSearchTerm = this.searchTerm.toLowerCase().trim();

            if (!lowerCaseSearchTerm) {
                return this.publishedPapers;
            }

            return this.publishedPapers.filter((paper) => {
                return this.getPaperSearchText(paper).includes(lowerCaseSearchTerm);
            });
        }
    },

    components: {
        NavBar
    },

    beforeRouteEnter(to, from, next) {
        NavBar.methods.loadData();
        next();
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
    font-family: 'NATS', sans-serif;
    color: black;
}

.header_bar {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100vw;
}

.project_container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    margin-left: 10px;
    margin-right: 10px;
}

.published_paper_container {
    display: flex;
    flex-wrap: wrap;
    grid-gap: 10px;
    justify-content: center;
    align-items: stretch;
    margin-bottom: 10px;
    margin-top: 10px;
    max-width: 825px;
}

.search_bar {
    max-width: max(80vw);
    border-radius: 30px;
    padding-left: 15px;
    height: 50px;
    width: 500px;
    font-size: 18px;
    border: 1px solid #6E6E6E;
}

.button-icon {
    width: 24px;
    height: 24px;
}

.search_container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    max-width: 80vw;
    margin: 0 auto;
    position: relative;
}

.search_button {
    border: 1px solid #6E6E6E;
    position: absolute;
    right: 0;
    top: 0;
    height: 100%;
    width: 50px;
    border-radius: 30px 30px 30px 30px;
    padding: 0;
}

.empty_state {
    margin-top: 20px;
    font-size: 24px;
}

.title {
    font-size: min(9vw, 1.1cm);
    line-height: min(9vw, 1.1cm);
    display: flex;
    text-align: right;
    margin-top: 20px;
}

</style>
