<template>
    <div class="keyword-container">
        <img src="/public/icons/search-black.png" alt="Icon" class="keyword-icon" :style="{ backgroundColor: secundary_color }">
        <div class = "keyword_description"> {{ keyword }} </div>
    </div>
</template>

<script>
import research_lab from '/public/research_lab.json';

export default {
    setup(props) {

    },

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
        };
    },

    props: {
        keyword: String,
    }
}
</script>

<style scoped>
.keyword-container {
    display: flex;
    justify-content: flex-start;
    align-items: center;
    padding: 5px 5px;
    border-radius: 25px;
    background-color: white;
    border: 1px solid #6E6E6E;
}

.keyword-icon {
    height: 30px;
    width: 30px;
    margin-right: 10px; 
    padding: 3px;
    border-radius: 30px 30px 30px 30px;
}

.keyword_description {
    margin-right: 10px;
}

</style>