<template>
    <section class="admin_page">
        <div class="panel">
            <div class="panel_header">
                <div>
                    <p class="eyebrow">Content</p>
                    <h1>Projects</h1>
                </div>

                <button @click="startCreate">New project</button>
            </div>

            <p v-if="statusMessage" class="status">{{ statusMessage }}</p>
            <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>

            <label class="search_field">
                Search project titles
                <input v-model="searchTerm" placeholder="Search by project title...">
            </label>

            <div class="table_like">
                <button
                    v-for="project in projects"
                    :key="project.slug"
                    class="row_button"
                    @click="selectProject(project)"
                >
                    <div>
                        <strong>{{ project.title }}</strong>
                        <p>{{ project.funding || 'No funding listed' }}</p>
                    </div>
                    <span>{{ project.slug }}</span>
                </button>
            </div>
        </div>

        <div class="panel">
            <h2>{{ isCreating ? 'Create project' : 'Edit project' }}</h2>

            <form class="editor_form" @submit.prevent="saveProject">
                <div class="two_col">
                    <label>
                        Title
                        <input v-model="form.title" required>
                    </label>

                    <label>
                        Slug
                        <input v-model="form.slug" required>
                    </label>
                </div>

                <div class="two_col">
                    <label>
                        Funding
                        <input v-model="form.funding" placeholder="NSF Award #1234567">
                    </label>

                    <label>
                        Upload image
                        <input
                            ref="imageInput"
                            type="file"
                            accept="image/*"
                            @change="handleImageSelection"
                        >
                    </label>
                </div>

                <div class="upload_row">
                    <button
                        type="button"
                        class="tertiary"
                        :disabled="!selectedImageFile || isUploadingImage"
                        @click="uploadSelectedImage"
                    >
                        {{ isUploadingImage ? 'Uploading...' : 'Upload image' }}
                    </button>
                    <p v-if="selectedImageFile" class="file_name">{{ selectedImageFile.name }}</p>
                </div>

                <p class="help_text">
                    Uploaded project images are stored in the Supabase Storage bucket `project-images` and their path is filled in automatically.
                </p>

                <label>
                    Image path or URL
                    <input v-model="form.image" placeholder="project-images/project-slug/file.png">
                </label>

                <div v-if="imagePreviewUrl" class="image_preview">
                    <img :src="imagePreviewUrl" alt="Project image preview">
                </div>

                <label>
                    Short description
                    <textarea v-model="form.shortDescription" rows="3"></textarea>
                </label>

                <label>
                    Full description
                    <textarea v-model="form.description" rows="7"></textarea>
                </label>

                <label class="suggestion_field">
                    Research areas
                    <input
                        ref="researchAreasInput"
                        v-model="researchAreasInput"
                        placeholder="comma, separated, areas"
                        @focus="isResearchAreasInputFocused = true"
                        @blur="handleSuggestionBlur('researchAreas')"
                    >
                    <div v-if="showResearchAreaSuggestions" class="suggestions_list">
                        <button
                            v-for="area in filteredResearchAreaSuggestions"
                            :key="area"
                            type="button"
                            class="suggestion_item"
                            @mousedown.prevent="applySuggestion('researchAreas', area)"
                        >
                            {{ area }}
                        </button>
                    </div>
                </label>

                <label class="suggestion_field">
                    People
                    <input
                        ref="peopleInput"
                        v-model="peopleInput"
                        placeholder="comma, separated, people"
                        @focus="isPeopleInputFocused = true"
                        @blur="handleSuggestionBlur('people')"
                    >
                    <div v-if="showPeopleSuggestions" class="suggestions_list">
                        <button
                            v-for="person in filteredPeopleSuggestions"
                            :key="person"
                            type="button"
                            class="suggestion_item"
                            @mousedown.prevent="applySuggestion('people', person)"
                        >
                            {{ person }}
                        </button>
                    </div>
                </label>

                <label>
                    Research article titles
                    <textarea v-model="articleTitlesInput" rows="4" placeholder="comma, separated, article titles"></textarea>
                </label>

                <label>
                    Project keywords
                    <input v-model="projectKeywordsInput" placeholder="comma, separated, keywords">
                </label>

                <div class="action_row">
                    <button type="submit">{{ isSaving ? 'Saving...' : 'Save' }}</button>
                    <button v-if="!isCreating" type="button" class="secondary" @click="removeProject">Delete</button>
                </div>
            </form>
        </div>

    </section>
</template>

<script>
import ProjectsResource, { resolveProjectImageUrl } from '../../api/resource/projects';
import MembersResource from '../../api/resource/people';

function emptyProject() {
    return {
        slug: '',
        title: '',
        description: '',
        shortDescription: '',
        image: '',
        funding: '',
        researchAreas: [],
        people: [],
        articleTitles: [],
        project_key_words: []
    };
}

export default {
    name: 'AdminProjects',

    data() {
        return {
            projects: [],
            searchTerm: '',
            form: emptyProject(),
            researchAreasInput: '',
            peopleInput: '',
            articleTitlesInput: '',
            projectKeywordsInput: '',
            researchAreaSuggestions: [],
            peopleSuggestions: [],
            isResearchAreasInputFocused: false,
            isPeopleInputFocused: false,
            isCreating: true,
            isSaving: false,
            isUploadingImage: false,
            statusMessage: '',
            errorMessage: '',
            selectedImageFile: null
        };
    },

    computed: {
        imagePreviewUrl() {
            return resolveProjectImageUrl(this.form.image);
        },

        currentResearchAreaSearchTerm() {
            const segments = this.researchAreasInput.split(',');
            return (segments[segments.length - 1] || '').trim().toLowerCase();
        },

        currentPeopleSearchTerm() {
            const segments = this.peopleInput.split(',');
            return (segments[segments.length - 1] || '').trim().toLowerCase();
        },

        filteredResearchAreaSuggestions() {
            const currentSearch = this.currentResearchAreaSearchTerm;

            if (!currentSearch) {
                return [];
            }

            const alreadySelectedValues = this.researchAreasInput
                .split(',')
                .slice(0, -1)
                .map((value) => value.trim().toLowerCase())
                .filter(Boolean);

            return this.researchAreaSuggestions
                .filter((area) => {
                    const normalizedArea = area.toLowerCase();
                    return normalizedArea.includes(currentSearch) && !alreadySelectedValues.includes(normalizedArea);
                })
                .slice(0, 6);
        },

        filteredPeopleSuggestions() {
            const currentSearch = this.currentPeopleSearchTerm;

            if (!currentSearch) {
                return [];
            }

            const alreadySelectedValues = this.peopleInput
                .split(',')
                .slice(0, -1)
                .map((value) => value.trim().toLowerCase())
                .filter(Boolean);

            return this.peopleSuggestions
                .filter((person) => {
                    const normalizedPerson = person.toLowerCase();
                    return normalizedPerson.includes(currentSearch) && !alreadySelectedValues.includes(normalizedPerson);
                })
                .slice(0, 6);
        },

        showResearchAreaSuggestions() {
            return this.isResearchAreasInputFocused && this.filteredResearchAreaSuggestions.length > 0;
        },

        showPeopleSuggestions() {
            return this.isPeopleInputFocused && this.filteredPeopleSuggestions.length > 0;
        }
    },

    async created() {
        await Promise.all([
            this.loadProjects(),
            this.loadAutofillData()
        ]);
    },

    methods: {
        async loadProjects() {
            const normalizedSearch = this.searchTerm.trim();

            this.projects = normalizedSearch
                ? await ProjectsResource.getAdminProjectsByTitle(normalizedSearch)
                : await ProjectsResource.getAdminProjects();
        },

        async loadAutofillData() {
            const members = await MembersResource.getAdminMembers();
            this.peopleSuggestions = members.map((member) => `${member.firstName} ${member.lastName}`);

            const keywordSet = new Set();
            members.forEach((member) => {
                (member.research_keywords || []).forEach((keyword) => keywordSet.add(keyword));
            });

            this.researchAreaSuggestions = Array.from(keywordSet).sort((a, b) => a.localeCompare(b));
        },

        startCreate() {
            this.form = emptyProject();
            this.researchAreasInput = '';
            this.peopleInput = '';
            this.articleTitlesInput = '';
            this.projectKeywordsInput = '';
            this.isResearchAreasInputFocused = false;
            this.isPeopleInputFocused = false;
            this.isCreating = true;
            this.isUploadingImage = false;
            this.statusMessage = '';
            this.errorMessage = '';
            this.selectedImageFile = null;

            if (this.$refs.imageInput) {
                this.$refs.imageInput.value = '';
            }
        },

        selectProject(project) {
            this.form = JSON.parse(JSON.stringify(project));
            this.researchAreasInput = (project.researchAreas || []).join(', ');
            this.peopleInput = (project.people || []).join(', ');
            this.articleTitlesInput = (project.articleTitles || []).join(', ');
            this.projectKeywordsInput = (project.project_key_words || []).join(', ');
            this.isResearchAreasInputFocused = false;
            this.isPeopleInputFocused = false;
            this.isCreating = false;
            this.isUploadingImage = false;
            this.statusMessage = '';
            this.errorMessage = '';
            this.selectedImageFile = null;

            if (this.$refs.imageInput) {
                this.$refs.imageInput.value = '';
            }
        },

        handleImageSelection(event) {
            const [file] = event.target.files || [];
            this.selectedImageFile = file || null;
        },

        handleSuggestionBlur(fieldName) {
            window.setTimeout(() => {
                if (fieldName === 'researchAreas') {
                    this.isResearchAreasInputFocused = false;
                    return;
                }

                if (fieldName === 'people') {
                    this.isPeopleInputFocused = false;
                }
            }, 100);
        },

        applySuggestion(fieldName, value) {
            const sourceValue = fieldName === 'researchAreas' ? this.researchAreasInput : this.peopleInput;
            const segments = sourceValue.split(',');

            segments[segments.length - 1] = ` ${value}`;

            const updatedValue = `${segments.join(',').replace(/^\s+/, '').trim()}, `;

            if (fieldName === 'researchAreas') {
                this.researchAreasInput = updatedValue;
                this.isResearchAreasInputFocused = true;
                return;
            }

            if (fieldName === 'people') {
                this.peopleInput = updatedValue;
                this.isPeopleInputFocused = true;
            }
        },

        async uploadSelectedImage(options = {}) {
            if (!this.selectedImageFile) {
                return;
            }

            if (!this.form.slug?.trim()) {
                this.errorMessage = 'Add the project slug before uploading an image so the file can be organized correctly.';
                return;
            }

            this.isUploadingImage = true;
            this.errorMessage = '';

            try {
                const { filePath } = await ProjectsResource.uploadProjectImage(this.selectedImageFile, this.form.slug);
                this.form.image = filePath;
                this.selectedImageFile = null;

                if (this.$refs.imageInput) {
                    this.$refs.imageInput.value = '';
                }

                if (!options.preserveStatusMessage) {
                    this.statusMessage = 'Project image uploaded. Save the project to attach it permanently.';
                }
            } catch (error) {
                this.errorMessage = error.message || 'Unable to upload the project image.';
                throw error;
            } finally {
                this.isUploadingImage = false;
            }
        },

        async saveProject() {
            this.isSaving = true;
            this.statusMessage = '';
            this.errorMessage = '';

            try {
                if (this.selectedImageFile) {
                    await this.uploadSelectedImage({
                        preserveStatusMessage: true
                    });
                }

                const payload = {
                    ...this.form,
                    researchAreas: this.researchAreasInput.split(',').map((item) => item.trim()).filter(Boolean),
                    people: this.peopleInput.split(',').map((item) => item.trim()).filter(Boolean),
                    articleTitles: this.articleTitlesInput.split(',').map((item) => item.trim()).filter(Boolean),
                    project_key_words: this.projectKeywordsInput.split(',').map((item) => item.trim()).filter(Boolean)
                };

                const savedProject = await ProjectsResource.upsertProject(payload);
                await this.loadProjects();
                this.selectProject(savedProject);
                this.statusMessage = 'Project saved.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to save the project.';
            } finally {
                this.isSaving = false;
            }
        },

        async removeProject() {
            if (!this.form.slug) {
                return;
            }

            try {
                await ProjectsResource.deleteProject(this.form.slug);
                await this.loadProjects();
                this.startCreate();
                this.statusMessage = 'Project deleted.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to delete the project.';
            }
        }
    },

    watch: {
        searchTerm() {
            this.loadProjects();
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
.two_col,
.upload_row {
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

.suggestion_field {
    position: relative;
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

.suggestions_list {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #c9d3df;
    border-radius: 14px;
    box-shadow: 0 16px 36px rgba(31, 42, 61, 0.12);
    overflow: hidden;
    z-index: 5;
}

.suggestion_item {
    width: 100%;
    min-height: auto;
    padding: 12px 14px;
    border-radius: 0;
    background: white;
    color: #1f2a3d;
    text-align: left;
}

.suggestion_item + .suggestion_item {
    border-top: 1px solid #e4e9f0;
}

.suggestion_item:hover {
    background: #f5f8fb;
}

.tertiary {
    background: #2b6a8b;
}

.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6b7586;
    margin-bottom: 8px;
}

.help_text,
.file_name {
    margin: 0;
    color: #586274;
    font-size: 14px;
}

.image_preview {
    border: 1px solid #d6dee8;
    border-radius: 18px;
    overflow: hidden;
    background: #f8fbfd;
}

.image_preview img {
    display: block;
    width: 100%;
    max-height: 260px;
    object-fit: cover;
}

@media (max-width: 980px) {
    .admin_page {
        grid-template-columns: 1fr;
    }

    .two_col {
        flex-direction: column;
    }

    .upload_row {
        flex-direction: column;
        align-items: flex-start;
    }
}
</style>
