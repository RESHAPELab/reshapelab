<template>
    <NavBar></NavBar>
    <div class="espacamento-header">
        <RouterView />
    </div>
    <Footer></Footer>
    <MobileMenu class="overlay-menu"></MobileMenu>
</template>

<script>
import { RouterLink, RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import MobileMenu from './components/MobileMenu.vue'
import Footer from './components/Footer.vue'

export default {
    components: {
        NavBar,
        RouterView,
        MobileMenu,
        Footer,
    },
    methods: {},
    onBeforeRouteUpdate() {
        this.scrollToTop()
    },
}
</script>
<style>

.espacamento-header {
    margin-top: 2.8cm;
}

.overlay-menu {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 9999;
}

@media (max-width: 499px) {
    .espacamento-header {
        margin-top: 1.3cm;
    }

    .overlay-menu {
        display: block;
    }
}
</style>

