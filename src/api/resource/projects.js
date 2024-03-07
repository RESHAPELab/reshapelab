import data from '/public/projects.json';
import data_people from '/public/members.json';

const ProjectsResource = {
    getProjects() {
        const projects = data.projects.map(project => ({
            title: project.project_name,
            description: project.project_description,
            image: project.images.small_image,
        }));
        
        return Promise.resolve(projects);
    },

    getProjectsByTitle(title) {
        const projects = data.projects
            .filter(project => project.project_name.includes(title))
            .map(project => ({
                title: project.project_name,
                description: project.project_description,
                image: project.images.small_image,
                project_key_words: project.project_key_words,
            }));
    
        return Promise.resolve(projects);
    },
    
    getProjectsByUser(user) {
        const userFullName = `${user.first_name} ${user.last_name}`.toLowerCase();
        
        const userProjects = data_people.members
            .filter(member => `${member.first_name} ${member.last_name}`.toLowerCase() === userFullName)
            .flatMap(member => member.projects);
    
        const projects = data.projects
            .filter(project => userProjects.includes(project.project_name))
            .map(project => ({
                title: project.project_name,
                description: project.project_description,
                image: project.images.small_image,
                links: project.links
            }));
    
        return Promise.resolve(projects);
    },

    getUsersByProject(projectTitle) {
        const members = data_people.members
            .filter(member => member.projects ? member.projects.includes(projectTitle) : false)
            .map(member => ({
                firstName: member.first_name,
                lastName: member.last_name,
                role: member.role,
                photos: member.photos,
                contacts: member.contacts
            }));
            
        return Promise.resolve(members);
    }
}

export default ProjectsResource;