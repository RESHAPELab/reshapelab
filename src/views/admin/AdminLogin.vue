<template>
    <section class="admin_shell">
        <div class="auth_card">
            <p class="eyebrow">RESHAPE Admin</p>
            <h1>Sign in</h1>
            <p class="subtitle">
                Use your Supabase email/password account to manage news and people.
            </p>

            <p v-if="!isConfigured" class="status error">
                Supabase is not configured yet. Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` before using admin mode.
            </p>

            <p v-if="errorMessage" class="status error">{{ errorMessage }}</p>

            <form class="auth_form" @submit.prevent="submitLogin">
                <label>
                    Email
                    <input v-model="email" type="email" autocomplete="email" required>
                </label>

                <label>
                    Password
                    <input v-model="password" type="password" autocomplete="current-password" required>
                </label>

                <button :disabled="isSubmitting || !isConfigured" type="submit">
                    {{ isSubmitting ? 'Signing in...' : 'Sign in' }}
                </button>
            </form>
        </div>
    </section>
</template>

<script>
import { signInAdmin } from '../../lib/adminAuth';
import { isSupabaseConfigured } from '../../lib/supabase';

export default {
    name: 'AdminLogin',

    data() {
        return {
            email: '',
            password: '',
            errorMessage: '',
            isSubmitting: false,
            isConfigured: isSupabaseConfigured
        };
    },

    methods: {
        async submitLogin() {
            this.errorMessage = '';
            this.isSubmitting = true;

            try {
                await signInAdmin(this.email, this.password);
                this.$router.push(this.$route.query.redirect || '/admin');
            } catch (error) {
                this.errorMessage = error.message || 'Unable to sign in.';
            } finally {
                this.isSubmitting = false;
            }
        }
    }
}
</script>

<style scoped>
.admin_shell {
    min-height: 100vh;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, #f3f6fb 0%, #dbe4ee 100%);
    padding: 24px;
}

.auth_card {
    width: min(460px, 100%);
    background: white;
    border-radius: 28px;
    box-shadow: 0 18px 50px rgba(18, 28, 45, 0.14);
    padding: 32px;
}

.eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6b7586;
    margin-bottom: 10px;
}

h1 {
    margin: 0 0 10px;
}

.subtitle {
    color: #586274;
    margin-bottom: 20px;
}

.auth_form {
    display: grid;
    gap: 16px;
}

label {
    display: grid;
    gap: 8px;
    color: #2b3442;
}

input {
    min-height: 46px;
    border-radius: 14px;
    border: 1px solid #c9d3df;
    padding: 0 14px;
}

button {
    min-height: 48px;
    border: 0;
    border-radius: 999px;
    background: #3c485e;
    color: white;
    cursor: pointer;
}

button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.status {
    border-radius: 14px;
    padding: 12px 14px;
    margin-bottom: 16px;
}

.status.error {
    background: #ffe9e7;
    color: #8a2d24;
}
</style>
