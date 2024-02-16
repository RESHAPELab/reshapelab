<template>
    <div class = "header_bar" :style="{ backgroundColor: primary_color }">
        <div class = "header">
            <div class = "researcher_image_div">
                <div class = "researcher_image" :style="{ backgroundImage: `url(${image_without_background})` }"></div>
            </div>
            <div class = "researcher_content">
                <p class = "first_name_title"> {{this.first_name}} </p>
                <p class = "last_name_title"> {{this.last_name}} </p>
                <p class = "job_title" :style="{ color: secundary_color }"> {{this.role}} </p>
            </div>
        </div>
    </div>

    <div class = "project_container">
        <div class="project_description">
            <p class="description_title" :style="{backgroundColor: primary_color}"> DESCRIPTION </p>

            <div class="description_text"> 
                <p> {{this.description}} </p>
            </div>

            <div class="description_text"> 
                <p> <strong> CONTACT ME </strong> </p>
                <p> Email - {{this.contacts.email}} </p>
                <p> GitHub - {{this.contacts.github}} </p>
            </div>
        </div>
        
        <p class = "normal_title title_keywords"> RESEARCH KEYWORDS </p>
        
        <div class = "key_words_container">
            <KeyWordsCard v-if="this.research_keywords" v-for="(keyword, index) in this.research_keywords" :key="index" :keyword="keyword" />
        </div>

        <p class = "normal_title title_keywords"> PUBLISHED PAPERS </p>

        <div class = "search_container">
            <input 
                type = "text" 
                v-model = "inputTerm" 
                placeholder = "Search by name or journal" 
                class = "search_bar"
            >
                
            <button @click="inputTerm ? resetSearch() : search" :style="{backgroundColor: primary_color}" class="button search_button" >
                <img :src="inputTerm ? '/icons/remove.png' : '/icons/search.png'" :alt="inputTerm ? 'Clean' : 'Search'" class="button-icon">
            </button>
        </div>

        <div>
            <button 
                @click="changePage(1)" 
                class = "botaoPaginacao"
            >
                First Page
            </button>

            <button 
                v-if="currentPage > 1" 
                @click="changePage(currentPage - 1)"
                class = "botaoPaginacao"
            >
                {{ currentPage - 1 }}
            </button>

            <button 
                @click="changePage(currentPage)"
                class = "botaoPaginacao"
                :style="{backgroundColor: '#BCC6D4'}"
            >
                {{ currentPage }}
            </button>

            <button 
                v-if="currentPage < Math.ceil(filteredPapers.length / papersPerPage)" 
                @click="changePage(currentPage + 1)"
                class = "botaoPaginacao"
            >
                {{ currentPage + 1 }}
            </button>

            <button 
                v-if="currentPage == 1 & currentPage < Math.ceil(filteredPapers.length / papersPerPage)" 
                @click="changePage(3)"
                class = "botaoPaginacao"
            >
                3
            </button>

            <button 
                @click="changePage(Math.ceil(filteredPapers.length / papersPerPage))"
                class = "botaoPaginacao"
            >
                Last Page
            </button>
        </div>

        <div class = "published_paper_container">
            <PublishedPaperCard
                v-for="paper in paginatedPapers"
                :key="paper.doi"
                :title="paper.title"
                :journal="paper['container-title']"
                :year="paper.issued['date-parts'][0][0]"
                :url="paper.URL"
                :doi="paper.DOI"
                :authors="paper.author"
            />
        </div>

        <div>
            <button 
                @click="changePage(1)" 
                class = "botaoPaginacao"
            >
                First Page
            </button>

            <button 
                v-if="currentPage > 1" 
                @click="changePage(currentPage - 1)"
                class = "botaoPaginacao"
            >
                {{ currentPage - 1 }}
            </button>

            <button 
                @click="changePage(currentPage)"
                class = "botaoPaginacao"
                :style="{backgroundColor: '#d9d9d9'}"

            >
                {{ currentPage }}
            </button>

            <button 
                v-if="currentPage < Math.ceil(filteredPapers.length / papersPerPage)" 
                @click="changePage(currentPage + 1)"
                class = "botaoPaginacao"
            >
                {{ currentPage + 1 }}
            </button>

            <button 
                v-if="currentPage == 1 & currentPage < Math.ceil(filteredPapers.length / papersPerPage)" 
                @click="changePage(3)"
                class = "botaoPaginacao"
            >
                3
            </button>

            <button 
                @click="changePage(Math.ceil(filteredPapers.length / papersPerPage))"
                class = "botaoPaginacao"
            >
                Last Page
            </button>
        </div>
    </div>
</template>

<script>
import NavBar from '../components/NavBar.vue';
import research_lab from '../../public/research_lab.json';

import KeyWordsCard from '../components/cards/KeyWordsCard.vue';
import PublishedPaperCard from '../components/cards/PublishedPaperCard.vue';

import MembersResource from '../api/resource/people'
import ArticlesResource from '../api/resource/articles'

export default  {
    name: 'Researcher',

    components: {
        KeyWordsCard,
    },

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            raw_researcher_name: this.$route.params.researcher_name,
            image_without_background: '',
            description: '',
            contacts: '',
            first_name: '',
            last_name: '',
            research_keywords: '',
            role: '',
            paper_names: '',
            published_papers: [],
            searchTerm: '',
            inputTerm: '',
            currentPage: 1,
            papersPerPage: 6,
            author_name: [],
        };
    },

    methods: {
        getResearcher() {
            MembersResource
            .getFirstMemberByName(this.raw_researcher_name)
            .then((result) => {
                this.image_without_background = '../' + result.photos.photo_without_background;
                this.description = result.description;
                this.contacts = result.contacts;
                this.first_name = result.firstName;
                this.last_name = result.lastName;
                this.research_keywords = result.research_keywords;
                this.role = result.role;
                this.author_name = result.author_name;
                
                this.getPapers();
            })
            .catch((error) => {
                console.error('An error occurred:', error);
            });
        },

        getPapers() {
            ArticlesResource
            .getArticlesByAuthor(this.author_name)
            .then((result) => {
                this.published_papers = result;
            })
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

        changePage(page) {
            this.currentPage = page;
        }
    },

    created() {
        this.getResearcher();
    },

    components: {
        NavBar
    },
    
    beforeRouteEnter(to, from, next) {
        NavBar.methods.loadData();
        next();
    },

    watch: {
    inputTerm: function(newInputTerm) {
        this.searchTerm = newInputTerm;
        }
    },

    computed: {
        filteredPapers() {
            const lowerCaseSearchTerm = this.searchTerm.toLowerCase();
            return this.published_papers.filter(published_paper => 
                (!this.searchTerm || 
                published_paper.title.toLowerCase().includes(lowerCaseSearchTerm) ||
                published_paper['container-title'].toLowerCase().includes(lowerCaseSearchTerm)
                )
            );
        },

        paginatedPapers() {
            const start = (this.currentPage - 1) * this.papersPerPage;
            const end = start + this.papersPerPage;
            return this.filteredPapers.slice(start, end);
        }
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

.header_bar {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100vw;
}

.header {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    margin-left: 20px;
    margin-right: 20px;
}

.researcher_content {
    margin-left: 0px;
}

@media (max-width: 499px) {
    .researcher_image_div {
        background-color: #3C485E;
        width: 100vw;
        height: min(220px, 105vw);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    .researcher_image {
        height: min(200px, 100vw);
        width: min(200px, 100vw);
        background-size: cover;
        background-position: center;
        margin-top: 20px;
    }
}

@media (min-width: 500px) {
    .header_bar {
        display: flex;
        justify-content: center;
    }

    .header {
        flex-direction: row;
        height: 250px;
        margin-left: 20px;
        margin-right: 20px;
    }

    .researcher_image {
        height: 250px;
        width: 250px;
        background-size: cover;
        background-position: center;

    }

    .researcher_content {
        margin-left: 20px;
    }

}

.first_name_title {
    font-size: min(15vw, 60px);
    line-height: 1.5;
    color: white;
    margin-bottom: max(-10vw, -50px);
    margin-left: 10px;
}

.last_name_title {
    font-size: min(15vw, 60px);
    line-height: 1.5;
    color: white;
    margin-bottom: max(-6vw, -30px);
    margin-left: 10px;
}

.job_title {
    font-size: min(15vw, 40px);
    line-height: 0.8;
    margin-top: 10px;
    margin-bottom: 20px;
    margin-left: 10px;
}

.yellow_bar {
    width: 100vw;
    height: 10px;
}

.description_title {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
    height: 30px;
    font-size: 20px;
}

.description_text {
    padding: 20px;
    text-align: justify;
}

.keyword-container {
    flex: 1 1 auto;
    margin: 5px;
}

.key_words_container {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    margin-top: 10px;
    max-width: 800px;
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

.project_information {
    display: flex;
    flex-direction: column;
    align-items: center;
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

.project_description {
    max-width: 800px;
    margin: 0 auto;
    box-shadow: 0 0 10px rgba(0,0,0,0.15);
    margin-left: 10px;
    margin-right: 10px;
    margin-top: 20px;
}

.normal_title {
    margin-top: 10px;
    font-size: min(8vw, 0.8cm);
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
    margin-bottom: 0px;
}

.search_button {
    position: absolute;
    border: 1px solid #6E6E6E;
    right: 0;
    top: 0;
    height: 100%;
    width: 50px;
    border-radius: 30px 30px 30px 30px;
    padding: 0;
    background-color: var(--primary-color)
}

.botaoPaginacao {
    height: 30px;
    padding-left: 10px;
    padding-right: 10px;
    margin-left: 5px;
    margin-right: 5px;
    margin-bottom: 10px;
    margin-top: 10px;
    border-radius: 30px 30px 30px 30px;
    font-size: 18px;
    background-color: white;
    border: 1px solid #6E6E6E;
}

</style>