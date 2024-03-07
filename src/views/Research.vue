<template>
    <section>
        <div class="home_background_image" :style="{ backgroundImage: `url(${background_image})`}">
            <div class="title_container">
                <p class = "medium_title"> MEET OUR </p>
                <p class = "big_title"> RESEARCH AREAS! </p>
                <p class = "small_title" :style="{ color: secundary_color }"> {{ research_lab_name }} </p>
            </div>
        </div>
        <div class = "member_container">
            <p class = "normal_title"> RESEARCH AREAS </p>
            
            <div class = "grid_container"> 
                <ResearchCard
                    v-for="project in projects"
                    :key="project.title"
                    :title="project.title"
                    :description="project.description"
                    :image="project.image"
                />
            </div>
        </div>
    </section>
</template>

<script> 
import ResearchCard from '../components/cards/ResearchCard.vue';
import research_lab from '/public/research_lab.json';

import ProjectsResource from '../api/resource/projects'

export default {
    name: 'Research',
    components: {
        ResearchCard,
    },

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            background_image: research_lab.laboratory_images.people_background,
            research_lab_name: research_lab.research_lab_name,
            projects: [],
        };
    },

    methods: {
        getResearchAreas() {
            ProjectsResource
            .getProjects()
            .then((projects) => {
                this.projects = projects;
            })
            .catch((error) => {
                console.error('An error occurred:', error);
            });
        },
    },

    created() {
        this.getResearchAreas();
    },

    watch: {
        inputTerm: function(newInputTerm) {
            this.searchTerm = newInputTerm;
        }
    },
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

.home_background_image {
    justify-content: center;
    align-items: center;
    display: flex;
    background-size: cover; 
    background-position: center;
}

.big_title {
    font-size: min(12vw, 1.8cm);
    line-height: min(12vw, 1.8cm);
    text-align: right; 
    justify-content: center;
    align-items: center;
    display: flex;
    color: white;
    text-align: right;
}

.medium_title {
    font-size: min(10vw, 1.5cm);
    line-height: min(10vw, 1.5cm);
    text-align: right; 
    justify-content: center;
    align-items: center;
    display: flex;
    color: white;
    text-align: right;
}

.small_title {
    font-size: min(8vw, 1cm);
    line-height: min(8vw, 1cm);
    text-align: center; 
    justify-content: center;
    align-items: center;
    display: flex;
    text-align: right;
}

.normal_title {
    font-size: min(8vw, 0.8cm);
}

.title_container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-end;
    text-align: right;
    margin-bottom: 50px;
    margin-top: 50px;
    margin-right: 15px;
    margin-left: 15px;
}

.member_container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}

.grid_container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 10px;
    width: min(800px, 90vw);
}

</style>