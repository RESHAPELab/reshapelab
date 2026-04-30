<template>
    <section class="admin_page">
        <div class="panel">
            <div class="panel_header">
                <div>
                    <p class="eyebrow">Content</p>
                    <h1>Research Areas</h1>
                </div>

                <button @click="startCreate">New area</button>
            </div>

            <p v-if="statusMessage" class="status">{{ statusMessage }}</p>
            <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>

            <label class="search_field">
                Search research areas
                <input v-model="searchTerm" placeholder="Search by research area title...">
            </label>

            <div class="table_like">
                <button
                    v-for="area in researchAreas"
                    :key="area.slug"
                    class="row_button"
                    @click="selectArea(area)"
                >
                    <div>
                        <strong>{{ area.title }}</strong>
                        <p>{{ area.project_key_words.join(', ') || 'No keywords listed' }}</p>
                    </div>
                    <span>{{ area.slug }}</span>
                </button>
            </div>
        </div>

        <div class="panel">
            <h2>{{ isCreating ? 'Create research area' : 'Edit research area' }}</h2>

            <form class="editor_form" @submit.prevent="saveArea">
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

                <label>
                    Upload image
                    <input
                        ref="imageInput"
                        type="file"
                        accept="image/*"
                        @change="handleImageSelection"
                    >
                </label>

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
                    Uploaded research area images are stored in the Supabase Storage bucket `research-area-images` and their path is filled in automatically.
                </p>

                <label>
                    Image path or URL
                    <input v-model="form.image" placeholder="research-area-images/research-area-slug/file.png">
                </label>

                <div v-if="imagePreviewUrl" class="image_preview">
                    <img :src="imagePreviewUrl" alt="Research area image preview">
                </div>

                <label>
                    Description
                    <textarea v-model="form.description" rows="7"></textarea>
                </label>

                <label>
                    Keywords
                    <input v-model="keywordsInput" placeholder="comma, separated, keywords">
                </label>

                <div class="action_row">
                    <button type="submit">{{ isSaving ? 'Saving...' : 'Save' }}</button>
                    <button v-if="!isCreating" type="button" class="secondary" @click="removeArea">Delete</button>
                </div>
            </form>
        </div>
    </section>
</template>

<script>
import ResearchAreasResource, { resolveResearchAreaImageUrl } from '../../api/resource/researchAreas';

function emptyResearchArea() {
    return {
        slug: '',
        title: '',
        description: '',
        image: '',
        project_key_words: []
    };
}

export default {
    name: 'AdminResearchAreas',

    data() {
        return {
            researchAreas: [],
            searchTerm: '',
            form: emptyResearchArea(),
            keywordsInput: '',
            isCreating: true,
            isSaving: false,
            isUploadingImage: false,
            selectedImageFile: null,
            statusMessage: '',
            errorMessage: ''
        };
    },

    computed: {
        imagePreviewUrl() {
            return resolveResearchAreaImageUrl(this.form.image);
        }
    },

    async created() {
        await this.loadResearchAreas();
    },

    methods: {
        async loadResearchAreas() {
            const normalizedSearch = this.searchTerm.trim();

            this.researchAreas = normalizedSearch
                ? await ResearchAreasResource.getAdminResearchAreasByTitle(normalizedSearch)
                : await ResearchAreasResource.getAdminResearchAreas();
        },

        startCreate() {
            this.form = emptyResearchArea();
            this.keywordsInput = '';
            this.isCreating = true;
            this.isUploadingImage = false;
            this.selectedImageFile = null;
            this.statusMessage = '';
            this.errorMessage = '';

            if (this.$refs.imageInput) {
                this.$refs.imageInput.value = '';
            }
        },

        selectArea(area) {
            this.form = JSON.parse(JSON.stringify(area));
            this.keywordsInput = (area.project_key_words || []).join(', ');
            this.isCreating = false;
            this.isUploadingImage = false;
            this.selectedImageFile = null;
            this.statusMessage = '';
            this.errorMessage = '';

            if (this.$refs.imageInput) {
                this.$refs.imageInput.value = '';
            }
        },

        handleImageSelection(event) {
            const [file] = event.target.files || [];
            this.selectedImageFile = file || null;
        },

        async uploadSelectedImage(options = {}) {
            if (!this.selectedImageFile) {
                return;
            }

            if (!this.form.slug?.trim()) {
                this.errorMessage = 'Add the research area slug before uploading an image so the file can be organized correctly.';
                return;
            }

            this.isUploadingImage = true;
            this.errorMessage = '';

            try {
                const { filePath } = await ResearchAreasResource.uploadResearchAreaImage(this.selectedImageFile, this.form.slug);
                this.form.image = filePath;
                this.selectedImageFile = null;

                if (this.$refs.imageInput) {
                    this.$refs.imageInput.value = '';
                }

                if (!options.preserveStatusMessage) {
                    this.statusMessage = 'Research area image uploaded. Save the research area to attach it permanently.';
                }
            } catch (error) {
                this.errorMessage = error.message || 'Unable to upload the research area image.';
                throw error;
            } finally {
                this.isUploadingImage = false;
            }
        },

        async saveArea() {
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
                    project_key_words: this.keywordsInput.split(',').map((item) => item.trim()).filter(Boolean)
                };

                const savedArea = await ResearchAreasResource.upsertResearchArea(payload);
                await this.loadResearchAreas();
                this.selectArea(savedArea);
                this.statusMessage = 'Research area saved.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to save the research area.';
            } finally {
                this.isSaving = false;
            }
        },

        async removeArea() {
            if (!this.form.slug) {
                return;
            }

            try {
                await ResearchAreasResource.deleteResearchArea(this.form.slug);
                await this.loadResearchAreas();
                this.startCreate();
                this.statusMessage = 'Research area deleted.';
            } catch (error) {
                this.errorMessage = error.message || 'Unable to delete the research area.';
            }
        }
    },

    watch: {
        searchTerm() {
            this.loadResearchAreas();
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

.tertiary {
    background: #2b6a8b;
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

    .two_col,
    .upload_row {
        flex-direction: column;
        align-items: stretch;
    }
}
</style>
