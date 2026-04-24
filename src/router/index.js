import { 
    createRouter, 
    createWebHistory 
} from 'vue-router'

import Home from '../views/Home.vue';
import People from '../views/People.vue';
import Research from '../views/Research.vue';
import Funding from '../views/Funding.vue';
import Projects from '../views/Projects.vue';
import ProjectDetail from '../views/ProjectDetail.vue';
import Project from '../views/Project.vue';
import Researcher from '../views/Researcher.vue';
import Publications from '../views/Publications.vue';
import PublicationDetail from '../views/PublicationDetail.vue';
import News from '../views/News.vue';
import AdminLogin from '../views/admin/AdminLogin.vue';
import AdminLayout from '../views/admin/AdminLayout.vue';
import AdminDashboard from '../views/admin/AdminDashboard.vue';
import AdminNews from '../views/admin/AdminNews.vue';
import AdminPeople from '../views/admin/AdminPeople.vue';
import AdminProjects from '../views/admin/AdminProjects.vue';
import AdminFunding from '../views/admin/AdminFunding.vue';
import AdminResearchAreas from '../views/admin/AdminResearchAreas.vue';
import { requireAdminSession } from '../lib/adminAuth';

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
            path: '/funding',
            name: 'funding',
            component: Funding,
        },
        {
            path: '/projects',
            name: 'projects',
            component: Projects,
        },
        {
            path: '/projects/:slug',
            name: 'project-detail',
            component: ProjectDetail,
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
            path: '/publications/:publication_id',
            name: 'publication-detail',
            component: PublicationDetail,
        },
        {
            path: '/news/:news_id',
            name: 'news',
            component: News,
        },
        {
            path: '/admin/login',
            name: 'admin-login',
            component: AdminLogin,
            meta: {
                hideSiteChrome: true
            }
        },
        {
            path: '/admin',
            component: AdminLayout,
            meta: {
                requiresAdminAuth: true,
                hideSiteChrome: true
            },
            children: [
                {
                    path: '',
                    name: 'admin-dashboard',
                    component: AdminDashboard,
                    meta: {
                        requiresAdminAuth: true,
                        hideSiteChrome: true
                    }
                },
                {
                    path: 'news',
                    name: 'admin-news',
                    component: AdminNews,
                    meta: {
                        requiresAdminAuth: true,
                        hideSiteChrome: true
                    }
                },
                {
                    path: 'people',
                    name: 'admin-people',
                    component: AdminPeople,
                    meta: {
                        requiresAdminAuth: true,
                        hideSiteChrome: true
                    }
                },
                {
                    path: 'projects',
                    name: 'admin-projects',
                    component: AdminProjects,
                    meta: {
                        requiresAdminAuth: true,
                        hideSiteChrome: true
                    }
                },
                {
                    path: 'funding',
                    name: 'admin-funding',
                    component: AdminFunding,
                    meta: {
                        requiresAdminAuth: true,
                        hideSiteChrome: true
                    }
                },
                {
                    path: 'research-areas',
                    name: 'admin-research-areas',
                    component: AdminResearchAreas,
                    meta: {
                        requiresAdminAuth: true,
                        hideSiteChrome: true
                    }
                }
            ]
        }
    ],
})
router.beforeEach(async (to, from, next) => {
    if (to.meta?.requiresAdminAuth) {
        const authState = await requireAdminSession();

        if (!authState.ok) {
            next({
                name: 'admin-login',
                query: {
                    redirect: to.fullPath
                }
            });
            return;
        }
    }

    window.scrollTo(0, 0)
    next()
})

export default router
