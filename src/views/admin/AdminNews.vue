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

            <label class="search_field">
                Search news titles
                <input v-model="searchTerm" placeholder="Search by title...">
            </label>

            <div class="table_like">
                <button
                    v-for="item in filteredNewsItems"
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
                    <input v-model="form.id" placeholder="YYYYMMDD_KEYWORD" required>
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
                    Uploaded images are stored in the Supabase Storage bucket `news-images` and their path is filled in automatically.
                </p>

                <label>
                    Image path or URL
                    <input v-model="form.image" placeholder="news-images/post-id/file.png">
                </label>

                <div v-if="imagePreviewUrl" class="image_preview">
                    <img :src="imagePreviewUrl" alt="News image preview">
                </div>

                <label class="people_field">
                    People
                    <input
                        ref="peopleInput"
                        v-model="peopleInput"
                        placeholder="comma,separated,names"
                        @focus="isPeopleInputFocused = true"
                        @blur="handlePeopleInputBlur"
                    >
                    <div v-if="showPeopleSuggestions" class="suggestions_list">
                        <button
                            v-for="person in filteredPeopleSuggestions"
                            :key="person.slug"
                            type="button"
                            class="suggestion_item"
                            @mousedown.prevent="applyPersonSuggestion(person)"
                        >
                            {{ person.firstName }} {{ person.lastName }}
                        </button>
                    </div>
                </label>

                <label>
                    Description HTML
                    <textarea v-model="form.description" placeholder="<p>Start writing using HTML tags...<p>" rows="10"></textarea>
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
import NewsResource, { resolveNewsImageUrl } from '../../api/resource/news';
import MembersResource from '../../api/resource/people';

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
            peopleOptions: [],
            searchTerm: '',
            originalId: '',
            form: emptyForm(),
            peopleInput: '',
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
            return resolveNewsImageUrl(this.form.image);
        },

        filteredNewsItems() {
            const normalizedSearch = this.searchTerm.trim().toLowerCase();

            if (!normalizedSearch) {
                return this.newsItems;
            }

            return this.newsItems.filter((item) => {
                return `${item.title || ''}`.toLowerCase().includes(normalizedSearch);
            });
        },

        currentPeopleSearchTerm() {
            const segments = this.peopleInput.split(',');
            return (segments[segments.length - 1] || '').trim().toLowerCase();
        },

        filteredPeopleSuggestions() {
            const currentSearch = this.currentPeopleSearchTerm;

            if (!currentSearch) {
                return [];
            }

            const alreadySelectedNames = this.peopleInput
                .split(',')
                .slice(0, -1)
                .map((name) => name.trim().toLowerCase())
                .filter(Boolean);

            return this.peopleOptions
                .filter((person) => {
                    const fullName = `${person.firstName || ''} ${person.lastName || ''}`.trim();
                    const normalizedName = fullName.toLowerCase();

                    return normalizedName.includes(currentSearch) && !alreadySelectedNames.includes(normalizedName);
                })
                .slice(0, 6);
        },

        showPeopleSuggestions() {
            return this.isPeopleInputFocused && this.filteredPeopleSuggestions.length > 0;
        }
    },

    async created() {
        await this.loadNews();
        await this.loadPeopleOptions();
    },

    methods: {
        async loadNews() {
            this.newsItems = await NewsResource.getAdminNews();
        },

        async loadPeopleOptions() {
            this.peopleOptions = await MembersResource.getAdminMembers();
        },

        startCreate() {
            this.form = emptyForm();
            this.originalId = '';
            this.peopleInput = '';
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

        selectItem(item) {
            this.form = { ...item };
            this.originalId = item.id;
            this.peopleInput = (item.person || []).join(', ');
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

        handlePeopleInputBlur() {
            window.setTimeout(() => {
                this.isPeopleInputFocused = false;
            }, 100);
        },

        applyPersonSuggestion(person) {
            const fullName = `${person.firstName || ''} ${person.lastName || ''}`.trim();
            const segments = this.peopleInput.split(',');

            segments[segments.length - 1] = ` ${fullName}`;
            this.peopleInput = `${segments.join(',').replace(/^\s+/, '').trim()}, `;
            this.isPeopleInputFocused = true;
        },

        async uploadSelectedImage(options = {}) {
            if (!this.selectedImageFile) {
                return;
            }

            if (!this.form.id?.trim()) {
                this.errorMessage = 'Add the post ID before uploading an image so the file can be organized correctly.';
                return;
            }

            this.isUploadingImage = true;
            this.errorMessage = '';

            try {
                const { filePath } = await NewsResource.uploadNewsImage(this.selectedImageFile, this.form.id);
                this.form.image = filePath;
                this.selectedImageFile = null;

                if (this.$refs.imageInput) {
                    this.$refs.imageInput.value = '';
                }

                if (!options.preserveStatusMessage) {
                    this.statusMessage = 'Image uploaded. Save the news post to attach it permanently.';
                }
            } catch (error) {
                this.errorMessage = error.message || 'Unable to upload the image.';
                throw error;
            } finally {
                this.isUploadingImage = false;
            }
        },

        async saveItem() {
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
                    person: this.peopleInput
                        .split(',')
                        .map((name) => name.trim())
                        .filter(Boolean)
                };

                const savedItem = this.isCreating
                    ? await NewsResource.upsertNewsItem(payload)
                    : await NewsResource.updateNewsItem(this.originalId || this.form.id, payload);
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

.tertiary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
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

.people_field {
    position: relative;
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

    .upload_row {
        flex-direction: column;
        align-items: flex-start;
    }
}
</style>
