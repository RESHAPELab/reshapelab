<template>
    <div class="card">
        <div class="image-container">
            <img :src="image" alt="Profile"/>
        </div>
        <div class="info">
            <div class="first_name"> {{ first_name }} </div> 
            <div class="last_name"> {{ last_name }}</div>
            <div class="role"> {{ role }} </div>
            <button class="view-more" @click="goToResearcher"> VIEW MORE </button>
            <div v-if="github" class="github">
                <img src="/icons/github.png" alt="GitHub Icon"/>
                <a :href="`https://github.com/${github}`" target="_blank">{{ github }}</a>
            </div>
            <div v-if="email" class="email">
                <img src="/icons/email.png" alt="Email"/>
                <a>{{ email }}</a>
            </div>
        </div>
    </div>
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
        role: String,
    },
    
    mounted() {
        document.documentElement.style.setProperty('--primary-color', this.primary_color);
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
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 250px;
    height: 400px;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 0 10px rgba(0,0,0,0.15);
    border: none;
}

.image-container {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    overflow: hidden;
    margin-top: 5px;
    position: relative;
}

.image-container img {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: cover;
    top: 0;
    left: 0;
}

.info {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.first_name {
    font-size: 30px;
}

.last_name {
    margin-top: -20px;
    font-size: 30px;
}

.role {
    font-size: 20px;
    color: #888888;
    margin-top: -10px;
}

.github, .email {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 5px;
}

.view-more {
    background-color: var(--primary-color);
    border: none;
    border-radius: 30px;
    height: 30px;
    color: white;
    padding: 0 20px;
    margin: 10px 0;
    cursor: pointer;
}
</style>