<template>
    <div class = "card">
        <div class="image-container" v-if="image">
            <p class="tag" :style="{ backgroundColor: secundary_color }"> {{ tag }} </p>
            <img class="image" :src="resolveImageUrl(image)" alt="Profile"/>
        </div>
        
        <p class="tagNoImage" :style="{ backgroundColor: secundary_color }" v-else> {{ tag }} </p>
        
        <p class = "date"> {{ date }} </p>
        <p class = "title" > {{ truncatedTitle }} </p>
        
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
import { resolveNewsImageUrl } from '../../api/resource/news';

export default {
    computed: {
        truncatedTitle() {
            const maxLength = 50;
            const normalizedTitle = `${this.title || ''}`.trim();

            if (normalizedTitle.length <= maxLength) {
                return normalizedTitle;
            }

            return `${normalizedTitle.slice(0, maxLength).trimEnd()}...`;
        }
    },

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
        resolveImageUrl(image) {
            return resolveNewsImageUrl(image);
        },

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
    display: flex;
    flex-direction: column;
    align-items: stretch;
    position: relative;
    z-index: 0;
    gap: 12px;
    padding-bottom: 12px;
}

.image {
    width: min(300px, 80vw);
    height: 200px;
    object-fit: cover;
}

.date {
    font-size: 20px;
    color: gray;
    padding: 0 20px;
}

.title{ 
    font-size: 20px;
    padding: 0 20px;
    text-align: justify;
    line-height: 20px;
    min-height: 40px;
    color: black
}

.read_more {
    width: 130px;
    margin: 0 20px;
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
    margin-bottom: 4px;
}

.tag {
    position: absolute;
    top: 15px;
    left: 0;
    z-index: 1;
    padding: 5px 10px;
}

.tagNoImage {
    padding: 5px 10px;
    margin: 0 20px;
    align-self: flex-start;
}

</style>
