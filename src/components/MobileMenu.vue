<template> 
    <div class = "menu" @click="checkOutsideClick">
        <button v-if="!isLargeMenuVisible" class="small_menu" @click.stop="toggleMenu" :style="{ backgroundColor: secundary_color }"> 
            <img src="/icons/menu-bar.png" class = "menu_bar">
        </button>
        
        <div v-if="isLargeMenuVisible" class = "large_menu" ref="largeMenu" :style="{ backgroundColor: secundary_color }">
            <div class = "close">
                <button class="button-close-largemenu" @click="toggleMenu"> <p  :style="{ color: secundary_color }"> X </p> </button>
            </div>
            <div class = "pages">
                <button class="button-largemenu" @click="navigateTo('/')"> HOME </button>
                <button class="button-largemenu" @click="navigateTo('/people')"> PEOPLE </button>
                <button class="button-largemenu" @click="navigateTo('/research')"> RESEARCH </button>
                <button class="button-largemenu" @click="navigateTo('/publication')"> PUBLICATION </button>
            </div>
        </div>
    </div>
</template>

<script>
import research_lab from '/public/research_lab.json';

export default {
    data() {
        return {
            isLargeMenuVisible: false,
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color,
        }
    },
    methods: {
        toggleMenu() {
            this.isLargeMenuVisible = !this.isLargeMenuVisible;
            if (this.isLargeMenuVisible) {
                window.addEventListener('click', this.checkOutsideClick);
            } else {
                window.removeEventListener('click', this.checkOutsideClick);
            }
        },

        checkOutsideClick(event) {
            if (!this.$refs.largeMenu.contains(event.target)) {
                this.toggleMenu();
            }
        },

        navigateTo(routePath) {
            this.$router.push(routePath);
            this.toggleMenu();
        }

    }
}
</script>

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


.large_menu {
    width: 250px;
    height: 300px;
    position: fixed;
    bottom: 20px;
    right: 20px;
    border-radius: 30px;
}

.small_menu {
    width: 80px;
    height: 80px;
    position: fixed;
    bottom: 20px;
    right: 20px;
    border-radius: 120px;
    border: None;
    box-shadow: 0 0 10px rgba(0,0,0,0.4);
}

.menu_bar {
    width: 40px;
    height: 30px;
}

.close {
    display: flex;
    justify-content: flex-end;
}

.button-close-largemenu {
    width: 30px;
    height: 30px;
    background: black;
    border-radius: 15px;
    border: none;
    margin-top: 10px;
    margin-right: 10px;
    font-size: 21px;
}

.button-largemenu {
    width: 170px;
    height: 60px;
    text-align: center;
    background: transparent;
    border: None;
    font-size: 20px;
    margin-left: 40px;
    margin-right: 40px;
    border-bottom: 2px solid black;
}

.button-largemenu:last-child {
    border-bottom: none; 
}

</style>