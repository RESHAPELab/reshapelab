<template>
    <section class="dashboard">
        <div class="hero_card">
            <p class="eyebrow">Prototype</p>
            <h1>Admin dashboard</h1>
            <p>
                This prototype is wired for Supabase-backed content editing. News CRUD is live, and people editing supports bios, contact links, DBLP IDs, and research keywords.
            </p>
        </div>

        <div class="grid">
            <router-link class="feature_card" to="/admin/news">
                <h2>Manage news</h2>
                <p>Add, edit, publish, or remove front-page news posts.</p>
            </router-link>

            <router-link class="feature_card" to="/admin/people">
                <h2>Manage people</h2>
                <p>Update people, research keywords, contacts, and profile metadata.</p>
            </router-link>
        </div>
    </section>
</template>

<style scoped>
.dashboard {
    display: grid;
    gap: 20px;
}

.hero_card,
.feature_card {
    background: white;
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 16px 36px rgba(31, 42, 61, 0.08);
    text-decoration: none;
    color: inherit;
}

.grid {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6b7586;
    margin-bottom: 8px;
}
</style>
