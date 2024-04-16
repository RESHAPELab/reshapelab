<template>
    <div id="app">
        <NavBar></NavBar>
        <div class="espacamento-header">
            <RouterView />
        </div>
        <Footer class="footer"></Footer>
        <MobileMenu class="overlay-menu"></MobileMenu>
    </div>
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
#app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

.espacamento-header {
    margin-top: 2.8cm;
    flex: 1 0 auto;
}

.overlay-menu {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 9999;
}

.footer {
    margin-top: 30px;
    flex-shrink: 0;
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