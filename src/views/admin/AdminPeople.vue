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

            <label class="search_field">
                Search people names
                <input v-model="searchTerm" placeholder="Search by first or last name...">
            </label>

            <div class="table_like">
                <button
                    v-for="member in filteredMembers"
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
                        <input :value="derivedSlug" disabled readonly>
                    </label>

                    <label>
                        Role
                        <input v-model="form.role" required>
                    </label>
                </div>

                <label>
                    Bio / description
                    <textarea v-model="form.description" placeholder="Write using raw text..." rows="6"></textarea>
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

                <div class="two_col upload_inputs">
                    <label>
                        Upload with background
                        <input
                            ref="backgroundPhotoInput"
                            type="file"
                            accept="image/*"
                            @change="handlePhotoSelection($event, 'photo_with_background')"
                        >
                    </label>

                    <label>
                        Upload without background
                        <input
                            ref="transparentPhotoInput"
                            type="file"
                            accept="image/*"
                            @change="handlePhotoSelection($event, 'photo_without_background')"
                        >
                    </label>
                </div>

                <div class="two_col upload_row">
                    <div>
                        <button
                            type="button"
                            class="tertiary"
                            :disabled="!selectedPhotoFiles.photo_with_background || isUploadingPhotos.photo_with_background"
                            @click="uploadSelectedPhoto('photo_with_background')"
                        >
                            {{ isUploadingPhotos.photo_with_background ? 'Uploading...' : 'Upload with background' }}
                        </button>
                        <p v-if="selectedPhotoFiles.photo_with_background" class="file_name">{{ selectedPhotoFiles.photo_with_background.name }}</p>
                    </div>

                    <div>
                        <button
                            type="button"
                            class="tertiary"
                            :disabled="!selectedPhotoFiles.photo_without_background || isUploadingPhotos.photo_without_background"
                            @click="uploadSelectedPhoto('photo_without_background')"
                        >
                            {{ isUploadingPhotos.photo_without_background ? 'Uploading...' : 'Upload without background' }}
                        </button>
                        <p v-if="selectedPhotoFiles.photo_without_background" class="file_name">{{ selectedPhotoFiles.photo_without_background.name }}</p>
                    </div>
                </div>

                <p class="help_text">
                    Uploaded profile images are stored in the Supabase Storage bucket `people-images` and their path is filled in automatically.
                </p>

                <div class="two_col preview_grid">
                    <div v-if="photoPreviewUrls.photo_with_background" class="image_preview">
                        <img :src="photoPreviewUrls.photo_with_background" alt="Photo with background preview">
                    </div>

                    <div v-if="photoPreviewUrls.photo_without_background" class="image_preview">
                        <img :src="photoPreviewUrls.photo_without_background" alt="Photo without background preview">
                    </div>
                </div>

                <div class="two_col">
                    <label>
                        Photo with background
                        <input v-model="form.photos.photo_with_background" placeholder="images/people/member/image_with_background.png or people-images/member/file.png">
                    </label>

                    <label>
                        Photo without background
                        <input v-model="form.photos.photo_without_background" placeholder="images/people/member/image_without_background.png or people-images/member/file.png">
                    </label>
                </div>

                <label>
                    DBLP PID
                    <input v-model="form.dblpPid" placeholder="">
                </label>

                <p class="help_text">
                    DBLP.org shows the PID in the URL for any author. For example, Igor's PID would be 70/3474, as his URL is https://dblp.org/pid/70/3474.html.
                </p>

                <div class="action_row">
                    <button type="submit">{{ isSaving ? 'Saving...' : 'Save' }}</button>
                    <button v-if="!isCreating" type="button" class="secondary" @click="removeMember">Delete</button>
                </div>
            </form>
        </div>
    </section>
</template>

<script>
import MembersResource, { resolveMemberImageUrl } from '../../api/resource/people';

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

function slugifyName(firstName, lastName) {
    return `${firstName || ''} ${lastName || ''}`
        .trim()
        .replace(/\s+/g, '-');
}

export default {
    name: 'AdminPeople',

    data() {
        return {
            members: [],
            searchTerm: '',
            originalSlug: '',
            form: emptyMember(),
            researchKeywordsInput: '',
            authorNamesInput: '',
            projectsInput: '',
            isCreating: true,
            isSaving: false,
            isUploadingPhotos: {
                photo_with_background: false,
                photo_without_background: false
            },
            selectedPhotoFiles: {
                photo_with_background: null,
                photo_without_background: null
            },
            statusMessage: '',
            errorMessage: ''
        };
    },

    computed: {
        derivedSlug() {
            return slugifyName(this.form.firstName, this.form.lastName);
        },

        filteredMembers() {
            const normalizedSearch = this.searchTerm.trim().toLowerCase();

            if (!normalizedSearch) {
                return this.members;
            }

            return this.members.filter((member) => {
                const fullName = `${member.firstName || ''} ${member.lastName || ''}`.trim().toLowerCase();
                return fullName.includes(normalizedSearch);
            });
        },

        photoPreviewUrls() {
            return {
                photo_with_background: resolveMemberImageUrl(this.form.photos.photo_with_background),
                photo_without_background: resolveMemberImageUrl(this.form.photos.photo_without_background)
            };
        }
    },

    async created() {
        await this.loadMembers();
    },

    methods: {
        async loadMembers() {
            try {
                this.members = await MembersResource.getAdminMembers();
            } catch (error) {
                this.members = [];
                this.errorMessage = error.message || 'Unable to load people.';
            }
        },

        startCreate() {
            this.form = emptyMember();
            this.form.slug = '';
            this.originalSlug = '';
            this.researchKeywordsInput = '';
            this.authorNamesInput = '';
            this.projectsInput = '';
            this.isCreating = true;
            this.statusMessage = '';
            this.errorMessage = '';
            this.selectedPhotoFiles = {
                photo_with_background: null,
                photo_without_background: null
            };
            this.isUploadingPhotos = {
                photo_with_background: false,
                photo_without_background: false
            };
            this.clearPhotoInputs();
        },

        selectMember(member) {
            this.form = JSON.parse(JSON.stringify(member));
            this.form.slug = slugifyName(member.firstName, member.lastName);
            this.originalSlug = member.slug;
            this.researchKeywordsInput = (member.research_keywords || []).join(', ');
            this.authorNamesInput = (member.author_name || []).join(', ');
            this.projectsInput = (member.projects || []).join(', ');
            this.isCreating = false;
            this.statusMessage = '';
            this.errorMessage = '';
            this.selectedPhotoFiles = {
                photo_with_background: null,
                photo_without_background: null
            };
            this.isUploadingPhotos = {
                photo_with_background: false,
                photo_without_background: false
            };
            this.clearPhotoInputs();
        },

        clearPhotoInputs() {
            if (this.$refs.backgroundPhotoInput) {
                this.$refs.backgroundPhotoInput.value = '';
            }

            if (this.$refs.transparentPhotoInput) {
                this.$refs.transparentPhotoInput.value = '';
            }
        },

        handlePhotoSelection(event, photoVariant) {
            const [file] = event.target.files || [];
            this.selectedPhotoFiles = {
                ...this.selectedPhotoFiles,
                [photoVariant]: file || null
            };
        },

        async uploadSelectedPhoto(photoVariant, options = {}) {
            const selectedFile = this.selectedPhotoFiles[photoVariant];

            if (!selectedFile) {
                return;
            }

            const memberSlug = this.derivedSlug.trim();

            if (!memberSlug) {
                this.errorMessage = 'Add the member slug before uploading an image so the file can be organized correctly.';
                return;
            }

            this.isUploadingPhotos = {
                ...this.isUploadingPhotos,
                [photoVariant]: true
            };
            this.errorMessage = '';

            try {
                const { filePath } = await MembersResource.uploadMemberImage(selectedFile, memberSlug, photoVariant);
                this.form.photos = {
                    ...this.form.photos,
                    [photoVariant]: filePath
                };
                this.selectedPhotoFiles = {
                    ...this.selectedPhotoFiles,
                    [photoVariant]: null
                };

                const inputRef = photoVariant === 'photo_with_background' ? 'backgroundPhotoInput' : 'transparentPhotoInput';

                if (this.$refs[inputRef]) {
                    this.$refs[inputRef].value = '';
                }

                if (!options.preserveStatusMessage) {
                    this.statusMessage = 'Profile image uploaded. Save the person to attach it permanently.';
                }
            } catch (error) {
                this.errorMessage = error.message || 'Unable to upload the profile image.';
                throw error;
            } finally {
                this.isUploadingPhotos = {
                    ...this.isUploadingPhotos,
                    [photoVariant]: false
                };
            }
        },

        async saveMember() {
            this.isSaving = true;
            this.statusMessage = '';
            this.errorMessage = '';

            try {
                if (this.selectedPhotoFiles.photo_with_background) {
                    await this.uploadSelectedPhoto('photo_with_background', {
                        preserveStatusMessage: true
                    });
                }

                if (this.selectedPhotoFiles.photo_without_background) {
                    await this.uploadSelectedPhoto('photo_without_background', {
                        preserveStatusMessage: true
                    });
                }

                const payload = {
                    ...this.form,
                    slug: this.derivedSlug,
                    research_keywords: this.researchKeywordsInput.split(',').map((item) => item.trim()).filter(Boolean),
                    author_name: this.authorNamesInput.split(',').map((item) => item.trim()).filter(Boolean),
                    projects: this.projectsInput.split(',').map((item) => item.trim()).filter(Boolean)
                };

                const savedMember = this.isCreating
                    ? await MembersResource.upsertMember(payload)
                    : await MembersResource.updateMember(this.originalSlug || payload.slug, payload);
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
            const memberSlug = this.form.slug || this.derivedSlug;

            if (!memberSlug) {
                return;
            }

            try {
                await MembersResource.deleteMember(memberSlug);
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
    background: #5f6b80;
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

.search_field {
    margin-top: 18px;
}

.upload_inputs,
.preview_grid {
    align-items: flex-start;
}

.help_text,
.file_name {
    color: #6b7586;
    font-size: 0.95rem;
}

.image_preview {
    background: #f5f8fb;
    border-radius: 18px;
    padding: 12px;
}

.image_preview img {
    width: 100%;
    max-height: 220px;
    object-fit: contain;
    display: block;
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
