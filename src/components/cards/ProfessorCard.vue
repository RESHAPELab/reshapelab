<template>
    <button class="card" @click="goToResearcher">
        <div class="image-overlay" :style="{ background: `linear-gradient(to top, ${primary_color}, transparent)` }"></div>
        <img :src="image"/>
        <div class="text-overlay">
            <div class="first_name_text"> {{ first_name }} </div>
            <div class="last_name_text"> {{ last_name }} </div>
        </div>
    </button>
</template>

<script>
import research_lab from '/public/research_lab.json';

export default {
    setup() {
        return {}
    },

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
        };
    },

    props: {
        image: String,
        first_name: String,
        last_name: String,
        email: String,
        github: String,
    },

    methods: {
        goToResearcher() {
            let researcher_name = `${this.first_name} ${this.last_name}`.replace(/ /g, '-');
            console.log(`Navigating to /people/${researcher_name}`);
            this.$router.push(`/people/${researcher_name}`);
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
    font-family: 'NATS', sans-serif;
    color: black;
}

.card {
    width: 250px;
    height: 290px;
    display: flex;
    position: relative;
    border: none;
    background: none;
    padding: 0;
    overflow: hidden;
}

.card img {
    max-width: 100%;
    max-height: 100%;
}

.first_name_text {
    margin-left: 10px;
    font-size: 35px;
    margin-bottom: -15px;
    color: white;
}

.last_name_text {
    margin-left: 10px;
    margin-bottom: 5px;
    font-size: 40px;
    color: white;
}

.text-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    text-align: left;
}

.image-overlay {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
}

</style>
