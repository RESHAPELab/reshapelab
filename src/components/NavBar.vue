<template>
    <header id = "large_header" v-if="selected === 'large_header'">
        <nav class="navBar">
            <div class="topPartNavBar" :style="{ 'background-color': primary_color }"> 
                <a>
                    <img 
                        class = "topBarLogo" 
                        :src="logo"
                        alt = "university_logo"
                    >
                </a>
            </div>
            <div class="bottomPartNavBar" :style="{ 'background-color': secundary_color }"> 
                <router-link
                    to="/"
                    class="buttonTopBar"
                    @click="menuShow"
                >
                HOME
                </router-link>

                <router-link
                    to="/people"
                    class="buttonTopBar"
                    @click="menuShow"
                >
                    PEOPLE
                </router-link>

                <router-link
                    to="/research"
                    class="buttonTopBar"
                    @click="menuShow"
                >
                    RESEARCH
                </router-link>

                <router-link
                    to="/publications"
                    class="buttonTopBar"
                    @click="menuShow"
                >
                    PUBLICATIONS
                </router-link>
            </div>
        </nav>
    </header>

    <header id = "small_header" v-if="selected === 'small_header'">
        <nav class="navBar">
            <div class="topPartNavBar" :style="{ 'background-color': primary_color }"> 
                <a>
                    <img 
                        class = "topBarLogo" 
                        :src="logo"
                        alt = "university_logo"
                    >
                </a>
            </div>
        </nav>
    </header>
</template>

<style scoped>
@font-face {
    font-family: 'NATS';
    src: url('/fonts/NATS-Regular.woff') format('woff');
}

* {
    padding: 0;
    margin: 0;
    font-family: 'NATS', sans-serif;
}

header {
    box-shadow: 0px 3px 10px #464646;
    width: 100%;
    z-index: 1;
    top: 0;
    position: fixed;
}

.topPartNavBar {
    width: 100vw;
    height: 1.5cm;
    justify-content: right;
    align-items: center;
    display: flex;
}

.bottomPartNavBar {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    width: 100vw;
}

.navBar {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.topBarLogo {
    height: 0.75cm;
    margin-right: 1cm;
}

.buttonTopBar {
    display: flex;
    flex-wrap: wrap;
    height: 1.3cm;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    flex-shrink: 0;
    border: none;
    background: transparent;
    margin-left: 0.25cm;
    margin-right: 0.25cm;
    font-size: 0.45cm;
    color: black;
    text-decoration: none;
}

@media (max-width: 499px) {
    body .bottomPartNavBar {
        display: none !important;
        height: 0px;
        margin-bottom:-30px;
    }

    .navBar {
        height: 1.5cm;
    }

    .topBarLogo {
        margin-right: 0cm;
    }

    .topPartNavBar {
        width: 100vw;
        height: 1.5cm;
        justify-content: center;
        align-items: center;
        display: flex;
    }
}

</style>

<script>
import research_lab from '/public/research_lab.json';
import logo from '@/../public/images/logo/logo.png';
import NATSRegular from '@/../public/fonts/NATS-Regular.woff';

export default {
    data() {
        return {
            logo: logo,
            laboratory_large_image: research_lab.laboratory_images.large_logo,
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
            NATSRegular: NATSRegular,
            windowWidth: 0,
            selected: ''
        };
    },

    created() {
        this.loadData();
    },

    methods: {
        loadData() {
            this.laboratory_large_image = research_lab.laboratory_images.large_logo;
            this.primary_color = research_lab.color_pallete.primary_color;
            this.secundary_color = research_lab.color_pallete.secundary_color;
        },

        getWindowWidth() {
            this.windowWidth = window.innerWidth;
        },
    },

    mounted() {
        this.$nextTick(function() {
            window.addEventListener('resize', this.getWindowWidth.bind(this));
            this.getWindowWidth();
        }.bind(this));
    },

    watch: {
        windowWidth(newWidth) {
            if (newWidth > 499) {
                this.selected = 'large_header';
            }

            else {
                this.selected = 'small_header';
            }
        }
    }
}
</script>