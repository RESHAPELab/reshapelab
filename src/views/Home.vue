<template>
    <section>
        <div class="home_background_image" :style="{ backgroundImage: `url(${background_image})` }">
            <a>
                <img 
                    class = "largeLogo" 
                    :src= "large_logo"
                    alt = "university_large_logo"
                >
            </a>
        </div>

        <div class = "title"> <p> News </p> </div>
        
        <div class = "container">
            <div ref="masonry">
                <NewsCard
                    v-for="notice in news"
                    :key="notice.title"
                    :title="notice.title"
                    :date="notice.date"
                    :tag="notice.tag"
                    :image="notice.image"
                    :id="notice.id"
                    class="grid-item"
                />
            </div>
        </div>
    </section>
</template>

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

.font_mission {
    margin-top: 20vh;
    margin-left: 40px;
    margin-right: 40px;
    margin-bottom: 20vh;
    max-width: 15cm;

    font-size: 1cm;
    line-height: 1cm;
    text-align: center; 
    justify-content: center;
    align-items: center;
    display: flex;
}

.largeLogo {
    width: min(80vw, 500px);
    margin-top: 20px;
    margin-bottom: 20px;
}

.title {
    font-size: min(8vw, 1cm);
    line-height: min(8vw, 1cm);
    text-align: center; 
    justify-content: center;
    align-items: center;
    display: flex;
    text-align: right;

    margin-bottom: 10px;
    margin-top: 20px;
}

.container {
    max-width: 980px;
    margin: 0 auto;
}

@media (max-width: 645px) {
    .container {
        max-width: min(320px, 85vw);
        margin: 0 auto;
    }
}

@media (min-width: 646px) and (max-width: 1099px) {
    .container {
        width: 645px;
    }
}

.grid-item {
    margin-bottom: 20px;
}

</style>

<script>
    import research_lab from '/public/research_lab.json';
    import NewsCard from '../components/cards/NewsCard.vue';
    import NewsResource from '../api/resource/news'
    
    import Masonry from 'masonry-layout';
    import imagesLoaded from 'imagesloaded';

    export default {
        components: {
            NewsCard,
        },

        data() {
            return {
                primary_color: research_lab.color_pallete.primary_color,
                secundary_color: research_lab.color_pallete.secundary_color,
                mission: research_lab.research_lab_mission,
                background_image: research_lab.laboratory_images.image_folder,
                large_logo: "images/logo/large_logo.png",
                news: [],
                
                masonry: null,
                columnWidth: 0,
            };
        },

        methods: {
            getNews() {
                NewsResource
                .getNews()
                .then((notices) => {
                    notices.forEach((notice) => {
                        this.news.push(notice)
                    })
                    this.$nextTick(() => {
                        imagesLoaded(this.$refs.masonry, () => {
                            this.initMasonry();
                        });
                    });
                })
                .catch((error) => {
                    console.error('An error occurred:', error);
                });
            },

            initMasonry() {
                this.masonry = new Masonry(
                    this.$refs.masonry, {
                    itemSelector: '.grid-item',
                    columnWidth: this.columnWidth,
                    gutter: 20,
                });
            },

            updateColumnWidth() {
                const windowWidth = window.innerWidth;
                const columnSize = 300;
                this.columnWidth = columnSize;
                
                if (this.masonry) {
                    this.masonry.columnWidth = this.columnWidth;
                    this.masonry.layout();
                }
            },
        },

        mounted() {
            this.updateColumnWidth = this.updateColumnWidth.bind(this);
            this.initMasonry();
            window.addEventListener('resize', this.updateColumnWidth);
        },

        created() {
            this.getNews();
        },
    }
</script>