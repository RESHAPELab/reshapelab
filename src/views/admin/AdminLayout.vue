<template>
    <section class="admin_layout">
        <aside class="sidebar">
            <div class="sidebar_top">
                <p class="brand">RESHAPE Admin</p>
                <p v-if="profile?.email" class="profile">{{ profile.email }}</p>
            </div>

            <nav class="nav">
                <router-link to="/admin">Overview</router-link>
                <router-link to="/admin/news">News</router-link>
                <router-link to="/admin/people">People</router-link>
                <router-link to="/admin/projects">Projects</router-link>
            </nav>

            <button class="sign_out" @click="handleSignOut">Sign out</button>
        </aside>

        <main class="content">
            <router-view />
        </main>
    </section>
</template>

<script>
import { getAdminContext, signOutAdmin } from '../../lib/adminAuth';

export default {
    name: 'AdminLayout',

    data() {
        return {
            profile: null
        };
    },

    async created() {
        const context = await getAdminContext();
        this.profile = context.profile;
    },

    methods: {
        async handleSignOut() {
            await signOutAdmin();
            this.$router.push('/admin/login');
        }
    }
}
</script>

<style scoped>
.admin_layout {
    min-height: 100vh;
    display: grid;
    grid-template-columns: 260px 1fr;
    background: #edf2f7;
    align-items: start;
}

.sidebar {
    position: sticky;
    top: 0;
    height: 100vh;
    background: #1f2a3d;
    color: white;
    padding: 28px 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    gap: 24px;
    overflow-y: auto;
    box-sizing: border-box;
}

.sidebar_top {
    display: grid;
    gap: 6px;
}

.brand {
    font-size: 28px;
    margin: 0 0 6px;
}

.profile {
    color: #c7d2e3;
    margin: 0;
    word-break: break-word;
}

.nav {
    display: grid;
    gap: 10px;
}

.nav a {
    color: white;
    text-decoration: none;
    padding: 12px 14px;
    border-radius: 14px;
}

.nav a.router-link-exact-active {
    background: rgba(255, 255, 255, 0.12);
}

.sign_out {
    min-height: 44px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: transparent;
    color: white;
    border-radius: 999px;
    cursor: pointer;
}

.content {
    padding: 28px;
    min-width: 0;
}

@media (max-width: 900px) {
    .admin_layout {
        grid-template-columns: 1fr;
    }

    .sidebar {
        position: static;
        height: auto;
        gap: 16px;
    }
}
</style>
