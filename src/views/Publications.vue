<template>
    <div class = "project_container">
        <p class = "title" :style="{ color: primary_color }"> PUBLICATIONS </p>

        <div class = "published_paper_container">
            <PublishedPaperCard
                v-for="paper in publishedPapers"
                :key="paper.doi"
                :title="paper.title"
                :journal="paper['container-title']"
                :year="paper.issued['date-parts'][0][0]"
                :url="paper.URL"
                :doi="paper.DOI"
                :authors="paper.author"
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
            publishedPapers: []
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
        }
    },

    created() {
        this.getAllArticles();
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

.title {
    font-size: min(9vw, 1.1cm);
    line-height: min(9vw, 1.1cm);
    display: flex;
    text-align: right;
    margin-top: 20px;
}

</style>