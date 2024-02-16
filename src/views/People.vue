<template>
    <section>
        <div class="home_background_image" :style="{ backgroundImage: `url(${background_image})`}">
            <div class="title_container">
                <p class = "medium_title"> MEET OUR </p>
                <p class = "big_title"> GREAT TEAM! </p>
                <p class = "small_title" :style="{ color: secundary_color }"> {{ research_lab_name }} </p>
            </div>
        </div>

        <div class = "member_container">
            <p class = "normal_title"> PROFESSORS </p>

            <div class = "grid_container"> 
                <ProfessorCard
                v-for="member in professors"
                :key="member.email"
                :image="member.photos.photo_with_background"
                :first_name="member.firstName"
                :last_name="member.lastName"
                :email="member.contacts.email"
                :github="member.contacts.github"
                />
            </div>
        </div>

        <div class = "member_container">
            <p class = "normal_title"> STUDENTS </p>

            <div class = "search_container">
                <input 
                    type = "text" 
                    v-model = "inputTerm" 
                    placeholder = "Search by name or email..." 
                    class = "search_bar"
                >
                
                <button @click="inputTerm ? resetSearch() : search" class="button search_button">
                    <img :src="inputTerm ? '/icons/remove.png' : '/icons/search.png'" :alt="inputTerm ? 'Clean' : 'Search'" class="button-icon">
                </button>
            </div>

            <p class = "normalText"> Filter by role </p>

            <div class = "role_filter_container">
                <div class="role_filter">
                    <button 
                        v-for="role in ['Undergraduate', 'Master', 'PhD Student', 'Visitor', 'Alumni']" 
                        :key="role" 
                        @click="filterRole = filterRole === role ? '' : role" 
                        :class="{ active: filterRole === role }" 
                        :style="{ backgroundColor: filterRole === role ? primary_color : '#ffffff', color: filterRole === role ? 'white' : '#6E6E6E' }"
                        class="button role_button"
                    >
                        {{ role }}
                    </button>
                </div>
            </div>

            <div class = "grid_container student"> 
                <StudentCard
                v-for="member in filteredStudents"
                :key="member.email"
                :image="member.photos.photo_with_background"
                :first_name="member.firstName"
                :last_name="member.lastName"
                :email="member.contacts.email"
                :github="member.contacts.github"
                :role="member.role"
                />
            </div>
        </div> 
    </section>
</template>

<script> 
import ProfessorCard from '../components/cards/ProfessorCard.vue';
import StudentCard from '../components/cards/StudentCard.vue';

import research_lab from '/public/research_lab.json';
import MembersResource from '../api/resource/people'

export default {
    name: 'People',
    components: {
        ProfessorCard,
        StudentCard,
    },
    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            mission: research_lab.research_lab_mission,
            background_image: research_lab.laboratory_images.people_background,
            research_lab_name: research_lab.research_lab_name,
            professors: [],
            students: [],
            searchTerm: '',
            inputTerm: '',
            filterRole: '',
        };
    },
    methods: {
        getProfessors() {
            MembersResource
            .getMembersByRole('Professor')
            .then((members) => {
                members.forEach((professor) => {
                    this.professors.push(professor)
                })
            })
            .catch((error) => {
                console.error('An error occurred:', error);
            });
        },

        getStudents() {
            MembersResource
            .getMembersByRole('Student')
            .then((members) => {
                members.forEach((students) => {
                    this.students.push(students)
                })
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
        }
    },

    created() {
        this.getProfessors();
        this.getStudents();
    },

    watch: {
    inputTerm: function(newInputTerm) {
        this.searchTerm = newInputTerm;
        }
    },

    computed: {
        filteredStudents() {
            const lowerCaseSearchTerm = this.searchTerm.toLowerCase();
            return this.students.filter(student => 
                (!this.searchTerm || 
                (student.firstName.toLowerCase() + ' ' + student.lastName.toLowerCase()).includes(lowerCaseSearchTerm) ||
                student.contacts.email.toLowerCase().includes(lowerCaseSearchTerm)) &&
                (!this.filterRole || student.role.includes(this.filterRole))
            );
        }
    },
}

</script>

<style scoped>
@font-face {
    font-family: 'NATS';
    src: url('public/fonts/NATS-Regular.woff'); 
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
    color: ;
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

.normalText{
    font-size: 25px;
    margin-top: 0px;
    margin-bottom: -10px;
}

.member_container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
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
    background-color: var(--primary-color)
}

.role_filter {
    display: flex;
    justify-content: center; /* Align items horizontally in the center */
    flex-wrap: wrap; /* Allow the items to wrap into multiple rows */
    width: 100%;
    margin-top: 10px;
}

.role_button {
    height: 50px;
    border-radius: 30px;
    padding: 0 15px;
    background-color: var(--primary-color);
    color: white;
    cursor: pointer;
    flex-grow: 1;
    text-align: center;
    line-height: 50px;
    border: 1px solid #6E6E6E;
    margin-bottom: 10px;
    margin-left: 10px;
    }

.role_button.active {
    color: black;
}

.role_filter_container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    max-width: 80vw;
    margin: 0 auto;
    margin-bottom: 20px;
    position: relative;
}

.grid_container.student {
    margin-bottom: 40px;
}

</style>