<template>
    <footer id="large_header">
        <nav class="navBar" :style="{ 'background-color': primary_color }">
            <div class="topPartNavBar"> 
                <img src="/images/logo/nau_logo.png" alt="NAU Logo" class = "nau_logo"/>

                <p class = "school name"> School of Informatics, Computing & Cyber Systems — NAU </p>
                <p class = "address name"> 1295 Knoles Dr, Flagstaff, AZ 86011, United States of America </p>
                <p class = "lab name"> Research in Software: Human Aspects, Practices and Education </p>
            </div>
        </nav>
    </footer>
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

#large_header {
    flex-shrink: 0;
    margin-top: 20px;
}

.navBar {
    width: 100vw;
    display: flex;
    justify-content: center;
    align-items: center;
}

.topPartNavBar {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
    width: min(1200px, 80vw);
}

.name {
    color: white;
    font-size: 15px;
    text-align: justify;
}

.school {
    font-size: 15px;
    margin-top: 15px;
}

.lab {
    font-size: 20px;
}

.nau_logo {
    width: min(80vw, 300px);
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

    methods: {
        loadData() {
            this.laboratory_large_image = research_lab.laboratory_images.large_logo;
            this.primary_color = research_lab.color_pallete.primary_color;
            this.secundary_color = research_lab.color_pallete.secundary_color;
        },
    },
}
</script>