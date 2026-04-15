<template>
    <section class="admin_page">
        <div class="panel">
            <div class="panel_header">
                <div>
                    <p class="eyebrow">Content</p>
                    <h1>News</h1>
                </div>

                <button @click="startCreate">New post</button>
            </div>

            <p v-if="statusMessage" class="status">{{ statusMessage }}</p>
            <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>

            <div class="table_like">
                <button
                    v-for="item in newsItems"
                    :key="item.id"
                    class="row_button"
                    @click="selectItem(item)"
                >
                    <div>
                        <strong>{{ item.title }}</strong>
                        <p>{{ item.date }} · {{ item.tag || 'UNTAGGED' }}</p>
                    </div>
                    <span>{{ item.published ? 'Published' : 'Draft' }}</span>
                </button>
            </div>
        </div>

        <div class="panel">
            <h2>{{ isCreating ? 'Create news post' : 'Edit news post' }}</h2>

            <form class="editor_form" @submit.prevent="saveItem">
                <label>
                    ID
                    <input v-model="form.id" required>
                </label>

                <label>
                    Title
                    <input v-model="form.title" required>
                </label>

                <div class="two_col">
                    <label>
                        Date
                        <input v-model="form.date" placeholder="YYYY-MM-DD or YYYY-MM">
                    </label>

                    <label>
                        Tag
                        <input v-model="form.tag">
                    </label>
                </div>

                <label>
                    Image path
                    <input v-model="form.image" placeholder="images/posts/example.png">
                </label>

                <label>
                    People
                    <input v-model="peopleInput" placeholder="comma,separated,names">
                </label>

                <label>
                    Description HTML
                    <textarea v-model="form.description" rows="10"></textarea>
                </label>

                <label class="checkbox">
                    <input v-model="form.published" type="checkbox">
                    Published
                </label>

                <div class="action_row">
                    <button type="submit">{{ isSaving ? 'Saving...' : 'Save' }}</button>
                    <button v-if="!isCreating" type="button" class="secondary" @click="removeItem">Delete</button>
                </div>
            </form>
        </div>
    </section>
</template>

<script>
import NewsResource from '../../api/resource/news';

function emptyForm() {
    return {
        id: '',
        title: '',
        date: '',
        person: [],
        tag: '',
        image: '',
        description: '',
        published: true
    };
}

export default {
    name: 'AdminNews',

    data() {
        return {
            newsItems: [],
            form: emptyForm(),
            peopleInput: '',
            isCreating: true,
            isSaving: false,
            statusMessage: '',
            errorMessage: ''
        };
    },

    async created() {
        await this.loadNews();
    },

    methods: {
        async loadNews() {
            this.newsItems = await NewsResource.getAdminNews();
        },

        startCreate() {
            this.form = emptyForm();
            this.peopleInput = '';
            this.isCreating = true;
            this.statusMessage = '';
            this.errorMessage = '';
        },

        selectItem(item) {
            this.form = { ...item };
            this.peopleInput = (item.person || []).join(', ');
            this.isCreating = false;
            this.statusMessage = '';
            this.errorMessage = '';
        },

        async saveItem() {
            this.isSaving = true;
            this.statusMessage = '';
            this.errorMessage = '';

            try {
                const payload = {
                    ...this.form,
                    person: this.peopleInput
                        .split(',')
                        .map((name) => name.trim())
                        .filter(Boolean)
                };

                const savedItem = await NewsResource.upsertNewsItem(payload);
                await this.loadNews();
                this.selectItem(savedItem);
                this.statusMessage = 'News item saved.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to save the news item.';
            } finally {
                this.isSaving = false;
            }
        },

        async removeItem() {
            if (!this.form.id) {
                return;
            }

            try {
                await NewsResource.deleteNewsItem(this.form.id);
                await this.loadNews();
                this.startCreate();
                this.statusMessage = 'News item deleted.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to delete the news item.';
            }
        }
    }
}
</script>

<style scoped>
.admin_page {
    display: grid;
    grid-template-columns: minmax(300px, 420px) minmax(0, 1fr);
    gap: 20px;
}

.panel {
    background: white;
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 16px 36px rgba(31, 42, 61, 0.08);
}

.panel_header,
.action_row,
.two_col {
    display: flex;
    gap: 12px;
}

.panel_header,
.action_row {
    justify-content: space-between;
    align-items: center;
}

.editor_form {
    display: grid;
    gap: 14px;
}

.two_col > label {
    flex: 1;
}

label {
    display: grid;
    gap: 8px;
}

input,
textarea,
button {
    font: inherit;
}

input,
textarea {
    border: 1px solid #c9d3df;
    border-radius: 14px;
    padding: 12px 14px;
}

button {
    min-height: 44px;
    border: 0;
    border-radius: 999px;
    padding: 0 16px;
    background: #3c485e;
    color: white;
    cursor: pointer;
}

.secondary {
    background: #8a2d24;
}

.row_button {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    text-align: left;
    background: #f5f8fb;
    color: black;
    border-radius: 18px;
    margin-bottom: 10px;
    padding: 14px 16px;
}

.table_like {
    margin-top: 18px;
}

.status {
    background: #e6f4ea;
    color: #24613f;
    border-radius: 14px;
    padding: 12px 14px;
    margin-top: 14px;
}

.status.error {
    background: #ffe9e7;
    color: #8a2d24;
}

.checkbox {
    grid-template-columns: auto 1fr;
    align-items: center;
}

.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6b7586;
    margin-bottom: 8px;
}

@media (max-width: 980px) {
    .admin_page {
        grid-template-columns: 1fr;
    }

    .two_col {
        flex-direction: column;
    }
}
</style>
