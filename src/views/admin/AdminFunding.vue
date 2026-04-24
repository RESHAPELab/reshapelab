<template>
    <section class="admin_page">
        <div class="panel">
            <div class="panel_header">
                <div>
                    <p class="eyebrow">Content</p>
                    <h1>Funding</h1>
                </div>

                <button @click="startCreate">New funding item</button>
            </div>

            <p v-if="statusMessage" class="status">{{ statusMessage }}</p>
            <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>

            <label class="search_field">
                Search funding
                <input v-model="searchTerm" placeholder="Search by award title or ID...">
            </label>

            <div class="table_like">
                <button
                    v-for="item in fundingItems"
                    :key="item.id"
                    class="row_button"
                    @click="selectItem(item)"
                >
                    <div>
                        <strong>{{ item.name }}</strong>
                        <p>{{ item.id }}</p>
                    </div>
                    <span>{{ item.final_date || 'No end date' }}</span>
                </button>
            </div>
        </div>

        <div class="panel">
            <h2>{{ isCreating ? 'Create funding item' : 'Edit funding item' }}</h2>

            <form class="editor_form" @submit.prevent="saveItem">
                <label>
                    Award ID
                    <input v-model="form.id" required>
                </label>

                <label>
                    Title
                    <input v-model="form.name" required>
                </label>

                <div class="two_col">
                    <label>
                        Initial date
                        <input v-model="form.initial_date" placeholder="Aug 2019">
                    </label>

                    <label>
                        Final date
                        <input v-model="form.final_date" placeholder="Jul 2023 or Ongoing">
                    </label>
                </div>

                <div class="two_col">
                    <label>
                        Access link
                        <input v-model="form.access_link" placeholder="https://...">
                    </label>

                    <label>
                        Total amount
                        <input v-model="form.total_amount" placeholder="$561,999.00">
                    </label>
                </div>

                <label>
                    Related projects
                    <input v-model="projectsInput" placeholder="comma, separated, projects">
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
import FundingResource from '../../api/resource/funding';

function emptyFundingItem() {
    return {
        id: '',
        name: '',
        initial_date: '',
        final_date: '',
        access_link: '',
        total_amount: '',
        projects: []
    };
}

export default {
    name: 'AdminFunding',

    data() {
        return {
            fundingItems: [],
            searchTerm: '',
            form: emptyFundingItem(),
            projectsInput: '',
            isCreating: true,
            isSaving: false,
            statusMessage: '',
            errorMessage: ''
        };
    },

    async created() {
        await this.loadFunding();
    },

    methods: {
        async loadFunding() {
            const normalizedSearch = this.searchTerm.trim();

            this.fundingItems = normalizedSearch
                ? await FundingResource.getAdminFundingByTitle(normalizedSearch)
                : await FundingResource.getAdminFunding();
        },

        startCreate() {
            this.form = emptyFundingItem();
            this.projectsInput = '';
            this.isCreating = true;
            this.statusMessage = '';
            this.errorMessage = '';
        },

        selectItem(item) {
            this.form = JSON.parse(JSON.stringify(item));
            this.projectsInput = (item.projects || []).join(', ');
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
                    projects: this.projectsInput.split(',').map((item) => item.trim()).filter(Boolean)
                };

                const savedItem = await FundingResource.upsertFundingItem(payload);
                await this.loadFunding();
                this.selectItem(savedItem);
                this.statusMessage = 'Funding item saved.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to save the funding item.';
            } finally {
                this.isSaving = false;
            }
        },

        async removeItem() {
            if (!this.form.id) {
                return;
            }

            try {
                await FundingResource.deleteFundingItem(this.form.id);
                await this.loadFunding();
                this.startCreate();
                this.statusMessage = 'Funding item deleted.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to delete the funding item.';
            }
        }
    },

    watch: {
        searchTerm() {
            this.loadFunding();
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
button {
    font: inherit;
}

input {
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

.table_like,
.search_field {
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
