<template>
    <div class = "card">
        <div class="image-container" v-if="image">
            <p class="tag" :style="{ backgroundColor: secundary_color }"> {{ tag }} </p>
            <img class="image" :src="image" alt="Profile"/>
        </div>
        
        <p class="tagNoImage" :style="{ backgroundColor: secundary_color }" v-else> {{ tag }} </p>
        
        <p class = "date"> {{ date }} </p>
        <p class = "title" > {{ title }} </p>
        
        <button class = "read_more" :style="{ backgroundColor: primary_color }" @click = "goToNews"> 
            <div class = "link-container"> <!-- Add this div -->
                <div class = "link"> Read About </div>
                <img src="/icons/arrow_right.png" alt="Read About" class = "read_icon"/>
            </div>
        </button>
    </div>
</template>

<script>
import research_lab from '/public/research_lab.json'

export default {
    setup() {
        return
    },

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
        };
    },

    props: {
        title: String,
        date: String,
        person: String,
        tag: String,
        image: String,
        description: String,
        id:String,
    },

    methods: {
        goToNews() {
            this.$router.push(`/news/${this.id}`);
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
    width: min(300px, 80vw);
    justify-content: center;
    align-items: center;
    display: flex;
    position: relative;
    z-index: 0;
}

.image {
    width: min(300px, 80vw);
    height: 200px;
    object-fit: cover;
}

.date {
    font-size: 20px;
    color: gray;
}

.title{ 
    font-size: 20px;
    margin: 0px 20px 10px 20px;
    text-align: justify;
    line-height: 20px;
    color: black
}

.read_more {
    width: 130px;
    margin-bottom: 10px;
    border-radius: 20px;
    border: none;
}

.link {
    color: white;
    margin: 4px 0px 4px 20px;
}

.link-container {
    display: flex; 
    align-items: center; 
    justify-content: space-between; 
}

.read_icon {
    margin-right: 10px;
}

.image-container {
    position: relative;
}

.tag {
    position: absolute;
    top: 15px;
    z-index: 1;
    padding: 5px;
}

.tagNoImage {
    padding: 5px;
}

</style>