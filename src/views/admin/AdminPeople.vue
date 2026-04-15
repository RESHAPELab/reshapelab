<template>
    <section class="admin_page">
        <div class="panel">
            <div class="panel_header">
                <div>
                    <p class="eyebrow">Content</p>
                    <h1>People</h1>
                </div>

                <button @click="startCreate">New person</button>
            </div>

            <p v-if="statusMessage" class="status">{{ statusMessage }}</p>
            <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>

            <div class="table_like">
                <button
                    v-for="member in members"
                    :key="member.slug"
                    class="row_button"
                    @click="selectMember(member)"
                >
                    <div>
                        <strong>{{ member.firstName }} {{ member.lastName }}</strong>
                        <p>{{ member.role }}</p>
                    </div>
                    <span>{{ member.slug }}</span>
                </button>
            </div>
        </div>

        <div class="panel">
            <h2>{{ isCreating ? 'Create person' : 'Edit person' }}</h2>

            <form class="editor_form" @submit.prevent="saveMember">
                <div class="two_col">
                    <label>
                        First name
                        <input v-model="form.firstName" required>
                    </label>

                    <label>
                        Last name
                        <input v-model="form.lastName" required>
                    </label>
                </div>

                <div class="two_col">
                    <label>
                        Slug
                        <input v-model="form.slug" required>
                    </label>

                    <label>
                        Role
                        <input v-model="form.role" required>
                    </label>
                </div>

                <label>
                    Bio / description
                    <textarea v-model="form.description" rows="6"></textarea>
                </label>

                <label>
                    Research keywords
                    <input v-model="researchKeywordsInput" placeholder="comma, separated, keywords">
                </label>

                <label>
                    Author aliases
                    <input v-model="authorNamesInput" placeholder="comma, separated, aliases">
                </label>

                <label>
                    Projects
                    <input v-model="projectsInput" placeholder="comma, separated, projects">
                </label>

                <div class="two_col">
                    <label>
                        Email
                        <input v-model="form.contacts.email">
                    </label>

                    <label>
                        GitHub
                        <input v-model="form.contacts.github">
                    </label>
                </div>

                <div class="two_col">
                    <label>
                        Photo with background
                        <input v-model="form.photos.photo_with_background">
                    </label>

                    <label>
                        Photo without background
                        <input v-model="form.photos.photo_without_background">
                    </label>
                </div>

                <label>
                    DBLP PID
                    <input v-model="form.dblpPid">
                </label>

                <div class="action_row">
                    <button type="submit">{{ isSaving ? 'Saving...' : 'Save' }}</button>
                    <button v-if="!isCreating" type="button" class="secondary" @click="removeMember">Delete</button>
                </div>
            </form>
        </div>
    </section>
</template>

<script>
import MembersResource from '../../api/resource/people';

function emptyMember() {
    return {
        firstName: '',
        lastName: '',
        slug: '',
        role: '',
        description: '',
        research_keywords: [],
        author_name: [],
        projects: [],
        dblpPid: '',
        contacts: {
            email: '',
            github: ''
        },
        photos: {
            photo_with_background: '',
            photo_without_background: ''
        }
    };
}

export default {
    name: 'AdminPeople',

    data() {
        return {
            members: [],
            form: emptyMember(),
            researchKeywordsInput: '',
            authorNamesInput: '',
            projectsInput: '',
            isCreating: true,
            isSaving: false,
            statusMessage: '',
            errorMessage: ''
        };
    },

    async created() {
        await this.loadMembers();
    },

    methods: {
        async loadMembers() {
            this.members = await MembersResource.getAdminMembers();
        },

        startCreate() {
            this.form = emptyMember();
            this.researchKeywordsInput = '';
            this.authorNamesInput = '';
            this.projectsInput = '';
            this.isCreating = true;
            this.statusMessage = '';
            this.errorMessage = '';
        },

        selectMember(member) {
            this.form = JSON.parse(JSON.stringify(member));
            this.researchKeywordsInput = (member.research_keywords || []).join(', ');
            this.authorNamesInput = (member.author_name || []).join(', ');
            this.projectsInput = (member.projects || []).join(', ');
            this.isCreating = false;
            this.statusMessage = '';
            this.errorMessage = '';
        },

        async saveMember() {
            this.isSaving = true;
            this.statusMessage = '';
            this.errorMessage = '';

            try {
                const payload = {
                    ...this.form,
                    research_keywords: this.researchKeywordsInput.split(',').map((item) => item.trim()).filter(Boolean),
                    author_name: this.authorNamesInput.split(',').map((item) => item.trim()).filter(Boolean),
                    projects: this.projectsInput.split(',').map((item) => item.trim()).filter(Boolean)
                };

                const savedMember = await MembersResource.upsertMember(payload);
                await this.loadMembers();
                this.selectMember(savedMember);
                this.statusMessage = 'Person saved.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to save the person.';
            } finally {
                this.isSaving = false;
            }
        },

        async removeMember() {
            if (!this.form.slug) {
                return;
            }

            try {
                await MembersResource.deleteMember(this.form.slug);
                await this.loadMembers();
                this.startCreate();
                this.statusMessage = 'Person deleted.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to delete the person.';
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
