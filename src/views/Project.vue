<template>
    <div class="header-bar" :style="{backgroundColor: primary_color}">
        <p class="header-text" :style="{ color: secundary_color }">Research Area</p>
        <p class="project-name">{{ projectName }}</p>
    </div>

    <div class = "project_container">
        <div class="project_description">
            <p class="description_title" :style="{backgroundColor: primary_color}"> DESCRIPTION </p>
                
            <div class="description_text"> 
                <p> {{project.description}} </p>
            </div>
        </div>

        <p class = "normal_title"> KEYWORDS </p>

        <div> 
            <div class="key_words_container">
                <KeyWordsCard
                    v-if="project.project_key_words"
                    v-for="(keyword, index) in project.project_key_words"
                    :key=index
                    :keyword=keyword.text
                    :class="{ 'vibrate': keyword.shouldVibrate }"
                />
            </div>

            <p class = "normal_title"> 
                RESEARCHERS 
            </p>

        </div>

        <div class = "grid_container"> 
            <ProjectMemberCard
                v-for="member in members"
                :key="member.email"
                :first_name="member.firstName"
                :last_name="member.lastName"
                :image="'../' + member.photos.photo_with_background"
                :email="member.contacts.email"
                :github="member.contacts.github"
                :role="member.role"
            />
        </div>
    </div>

</template>

<script>
import NavBar from '../components/NavBar.vue';
import research_lab from '../../public/research_lab.json';
import ProjectMemberCard from '../components/cards/ProjectMemberCard.vue';
import KeyWordsCard from '../components/cards/KeyWordsCard.vue';

import ProjectsResource from '../api/resource/projects'

export default  {
    name: 'Project',
    components: {
        ProjectMemberCard,
        KeyWordsCard,
    },

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            projectName: this.$route.params.projectName.replace(/-/g, ' '),
            members: [],
            project: {
                project_key_words: [],
            },
        };
    },

    methods: {
        getMembers() {
            ProjectsResource
                .getUsersByProject(this.projectName)
                .then((data) => {
                    this.members = data;
                    console.log(data);
                })
                .catch((error) => {
                    console.error('An error occurred:', error);
                });
        },

        getProject() {
            ProjectsResource
                .getProjectsByTitle(this.projectName)
                .then((data) => {
                    this.project = data[0];
                    this.project.project_key_words = this.project.project_key_words.map(keyword => ({
                        text: keyword,
                        shouldVibrate: false,
                    }));
                    this.addRandomVibration();
                })
                .catch((error) => {
                    console.error('An error occurred:', error);
                });
        },

        addRandomVibration() {
            this.project.project_key_words.forEach(keyword => {
                setInterval(() => {
                    keyword.shouldVibrate = true;
                    setTimeout(() => {
                        keyword.shouldVibrate = false;
                    }, 800); 
                }, Math.random() * 5000 + 5000); 
            });
        },
    },

    created() {
        this.getMembers();
        this.getProject();
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

<style>
.vibrate {
  animation: vibrate 0.3s infinite;
}

@keyframes vibrate {
  0% { transform: translate(0); }
  25% { transform: translate(1px, 1px); }
  50% { transform: translate(0); }
  75% { transform: translate(-1px, -1px); }
  100% { transform: translate(0); }
}
</style>

<style scoped>
@font-face {
    font-family: 'NATS';
    src: url('/public/fonts/NATS-Regular.woff'); 
}

* {
    padding: 0;
    margin: 0;
    font-family: 'NATS', sans-serif;
    color: black;
}

.header-bar {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 20px 0;
}

.header-text {
    font-size: 1.2em;
    margin-bottom: 10px;
}

.project-name {
    color: white;
    font-size: 1.5em;
    max-width: max(600px);
    word-wrap: break-word;
    margin-left: 20px;
    margin-right: 20px;
}

.grid_container {
    display: grid;
    max-width: min(1100px, 80vw);
    margin: 0 auto; 
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    grid-gap: 10px;
    justify-items: center;
    align-items: center;
    margin-bottom: 10px;
}

.project_container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
}


.normal_title {
    font-size: min(8vw, 0.8cm);
}

.project_description {
    max-width: 800px;
    margin: 0 auto;
    box-shadow: 0 0 10px rgba(0,0,0,0.15);
    margin-left: 10px;
    margin-right: 10px;
    margin-top: 20px;
}

.description_title {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
    height: 30px;
}

.description_text {
    margin-top: 10px;
    margin-left: 20px;
    margin-right: 20px;
    margin-bottom: 20px;
    text-align: justify;
}

.key_words_container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    margin-top: 10px;
    max-width: 800px;
    margin-left: 10px;
    margin-right: 10px;
}

.keyword-container {
    flex: 1 1 auto;
    margin: 5px;
}

.project_information {
    display: flex;
    flex-direction: column;
    align-items: center;
}

@media screen and (min-width: 700px) {
    .project_information {
        flex-direction: row;
        justify-content: space-between;
        align-items: flex-start; 
    }

    .title_keywords {
        margin-top: 10px;
        margin-left: 10px;
        margin-bottom: -15px;
        margin-right: 70px;
        text-align: left;
    }
}
</style>