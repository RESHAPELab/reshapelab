<template>
    <div class="grid_container">
        <img class = "imagem" :src="this.image">

        <p class = "small_title" :style="{ color: white }"> {{ this.title }} </p>

        <p class = "description"> {{ this.date }} </p>

        <div v-html="this.description" class = "description"></div>

    </div>


</template>

<script>

import NavBar from '../components/NavBar.vue';
import research_lab from '../../public/research_lab.json';
import NewsResource from '../api/resource/news';

export default {
    name: 'News',

    data() {
        return {
            id: this.$route.params.news_id,
            title: '',
            date: '',
            person: '',
            tag: '',
            description: '',
            image: '',
        }
    },

    methods: { 
        getNews() {
            NewsResource
            .getNewsById(this.id)
            .then((result) => {
                this.title = result.title;
                this.date = result.date;
                this.person = result.person;
                this.tag = result.tag;
                this.description = result.description;
                this.image = "../" + result.image;

                // Apply styles after setting the description
                this.applyStyles();
            })
        },

        applyStyles() {
        this.$nextTick(() => {
            const images = this.$el.querySelectorAll('.description img');
            images.forEach(img => {
                img.style.display = 'block';
                img.style.margin = '0 auto';
                img.style.maxWidth = '80vw';
                img.style.marginBottom = '20px';
            });
        });
    }
    },

    created() {
        this.getNews();
    },

    components: {
        NavBar
    },
    
    beforeRouteEnter(to, from, next) {
        NavBar.methods.loadData();
        next();
    },
}

</script>

<style scoped>
@font-face {
    font-family: 'NATS';
    src: url('../../public/fonts/NATS-Regular.woff'); 
}

* {
    padding: 0;
    margin: 0;
    font-family: 'NATS', sans-serif;
    color: black;
}

.grid_container {   
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    margin: 0 auto; /* This will center the container horizontally */
    width: min(800px, 70vw);
}

.small_title {
    text-align: center; 
    justify-content: center;
    align-items: center;
    display: flex;
    text-align: center;
    font-size: 30px;
    margin-top: 20px;
}

.description {
    text-align: justify;
    margin-top: 10px;
}

.imagem {
    margin-top: 20px;
    max-height: 250px;
    max-width: 80vw;
}
</style>

