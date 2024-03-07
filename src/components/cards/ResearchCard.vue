<template>
    <div class="card">
        <div class="card-image" :style="{ backgroundImage: 'url(' + image + ')' }"></div>
        <div class="card-content" :style="{backgroundColor: primary_color, color: 'white'}" ref="descriptionContainer">
            <p class="card-title" :style="{ color: secundary_color }"> {{title}} </p>
            <p class="card-description" ref="description"> {{description}} </p>
            
            <div class = "read_more_button"> 
                <button class = "project_button" :style="{ backgroundColor: secundary_color }" @click="goToProject"> 
                    <div class = "button_text"> Read More </div> 
                </button>
            </div>
        </div>
    </div>
</template>

<script>
import research_lab from '/public/research_lab.json';

export default  {
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
        title: String,
        description: String,
        image: String,
    },

    methods: {
        goToProject() {
            let projectName = this.title.replace(/ /g, '-');
            console.log(`Navigating to /research/${projectName}`);
            this.$router.push(`/research/${projectName}`);
        }
    }
}
</script>

<style scoped>
.card {
    display: flex;
    flex-direction: column;
    margin-bottom: 20px;
    margin-left: 30px;
    margin-right: 30px;
}

.card-title {
    font-size: 0.6cm;
    margin-left: 10px;
    margin-right: 10px;
}

.card-image {
    height: 270px;
    width: auto;
    background-size: 100% auto;
    background-position: center;
    background-repeat: no-repeat;
    background-color: #d6d6d6;
}

.card-content {
    padding: 10px;
}

.card-description {
    text-align: justify;
    margin-left: 10px;
    margin-right: 10px;
}

.project_button {
    height: 30px;
    border-radius: 30px;
    cursor: pointer;
    flex-grow: 1;
    margin: 0 5px;
    text-align: center;
    line-height: 50px;
    color: black;
    border: None;
}

.read_more_button {
    display: flex;
    width: 150px;
    justify-content: center;
    margin: auto;
}

.button_text {
    margin-top: -10px;
}

</style>