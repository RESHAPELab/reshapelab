import data from '/public/research_areas.json';
import dataPeople from '/public/members.json';

const ResearchAreasResource = {
    getResearchAreas() {
        const researchAreas = data.projects.map((project) => ({
            title: project.project_name,
            description: project.project_description,
            image: project.images.small_image
        }));

        return Promise.resolve(researchAreas);
    },

    getResearchAreaByTitle(title) {
        const researchAreas = data.projects
            .filter((project) => project.project_name.includes(title))
            .map((project) => ({
                title: project.project_name,
                description: project.project_description,
                image: project.images.small_image,
                project_key_words: project.project_key_words
            }));

        return Promise.resolve(researchAreas);
    },

    getUsersByResearchArea(projectTitle) {
        const members = dataPeople.members
            .filter((member) => member.projects ? member.projects.includes(projectTitle) : false)
            .map((member) => ({
                firstName: member.first_name,
                lastName: member.last_name,
                role: member.role,
                photos: member.photos,
                contacts: member.contacts
            }));

        return Promise.resolve(members);
    }
};

export default ResearchAreasResource;
