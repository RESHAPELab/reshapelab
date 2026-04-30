<template>
    <div
        class = "card"
        :class="{ interactive: clickable }"
        :role="clickable ? 'button' : undefined"
        :tabindex="clickable ? 0 : undefined"
        @click="handleSelect"
        @keydown.enter.prevent="handleSelect"
        @keydown.space.prevent="handleSelect"
    >
        <div class = "text title"> 
        <strong> {{ title }} </strong>
        </div>

        <div class = "text authors">
        {{ processedAuthors }}
        </div>
        
        <div class = "text journal"> 
        <i>{{ journal }}</i>
        </div>

        <div v-if="year" class = "text year">
            {{ year }}
        </div>

        <a v-if="paperLink" class = "doi" :href="paperLink" target="_blank" rel="noopener noreferrer" @click.stop>
            <strong> {{ linkLabel }} </strong> 
        </a>

    </div>
</template>

<script>
import research_lab from '/public/research_lab.json';

export default {
    emits: ['select'],

    setup() {
        return
    },

    data() {
        return {
            primary_color: research_lab.color_pallete.primary_color,
            secundary_color: research_lab.color_pallete.secundary_color
        };
    },

    props: {
        title: String,
        journal: String,
        year: Number,
        url: String,
        doi: String,
        authors: Array,
        clickable: {
            type: Boolean,
            default: false
        }
    },

    methods: {
        handleSelect() {
            if (this.clickable) {
                this.$emit('select');
            }
        }
    },

    computed: {
        paperLink() {
            if (this.doi) {
                return `https://doi.org/${this.doi}`;
            }

            return this.url || '';
        },

        linkLabel() {
            return this.doi ? 'DOI' : 'Link';
        },

        processedAuthors() {
            if (!this.authors) {
                return ' ';
            }

            const authorsArray = this.authors;
            const authorsNames = authorsArray.map(author => `${author.given} ${author.family}`);
            return authorsNames.join(', ');
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
    width: min(800px, 80vw);
    border: 0px;
    box-shadow: 0 0 10px rgba(0,0,0,0.15);
}

.card.interactive {
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card.interactive:hover,
.card.interactive:focus-visible {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.18);
    outline: none;
}

.text {
    margin-top: 0px;
    margin-left: 20px;
    margin-right: 20px;
    text-align: justify;
}

.text.title {
    margin-top: 10px;
}

.doi {
    margin-left: 20px;
    margin-right: 20px;
    margin-bottom: 10px;
    text-align: justify;
}

.paperButton {
    height: 50px;
    border-radius: 30px;
    padding: 0 15px;
    cursor: pointer;
    flex-grow: 1;
    margin: 0 5px;
    text-align: center;
    line-height: 50px;
    color: black;
    text-decoration: none;
}

.buttonBar {
    display: flex;
    justify-content: center;
    align-items: flex-end;
    width: 100%;
    height: 100%;
}

</style>
