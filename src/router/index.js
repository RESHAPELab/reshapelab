import { 
    createRouter, 
    createWebHistory 
} from 'vue-router'

import Home from '../views/Home.vue';
import People from '../views/People.vue';
import Research from '../views/Research.vue';
import Project from '../views/Project.vue';
import Researcher from '../views/Researcher.vue';
import Publications from '../views/Publications.vue';
import News from '../views/News.vue';

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    mode: 'history',
    routes: [
        {
            path: '/',
            name: 'home',
            component: Home,
        },
        {
            path: '/people',
            name: 'members',
            component: People,
        },
        {
            path: '/research',
            name: 'research',
            component: Research,
        },
        {
            path: '/research/:projectName',
            name: 'project',
            component: Project,
        },
        {
            path: '/people/:researcher_name',
            name: 'researcher',
            component: Researcher,
        },
        {
            path: '/publications/',
            name: 'publications',
            component: Publications,
        },
        {
            path: '/news/:news_id',
            name: 'news',
            component: News,
        }
    ],
})
router.beforeEach((to, from, next) => {
    window.scrollTo(0, 0)
    next()
})

export default router