import data from '/public/members.json';

const MembersResource = { 
    getMembers() {
        const members = data.members.map(member => ({
            firstName: member.first_name,
            lastName: member.last_name,
            role: member.role,
            photos: member.photos,
            contacts: member.contacts,
            author_name: member.author_name
        }));

        members.sort((a, b) => {
            const nameA = a.firstName + ' ' + a.lastName;
            const nameB = b.firstName + ' ' + b.lastName;
            if (nameA < nameB) return -1;
            if (nameA > nameB) return 1;
            return 0;
        });

        return Promise.resolve(members);
    },

    getMembersByRole(role) {
        let members;
        if (role === 'Student') {
            members = data.members
                .filter(member => !member.role.includes('Professor'));
        } else {
            members = data.members
                .filter(member => member.role.includes(role));
        }

        members = members.map(member => ({
            firstName: member.first_name,
            lastName: member.last_name,
            role: member.role,
            photos: member.photos,
            contacts: member.contacts,
            author_name: member.author_name
        }));

        members.sort((a, b) => {
            const nameA = a.firstName + ' ' + a.lastName;
            const nameB = b.firstName + ' ' + b.lastName;
            if (nameA < nameB) return -1;
            if (nameA > nameB) return 1;
            return 0;
        });

        return Promise.resolve(members);
    },

    getMembersByEmail(email) {
        const member = data.members.find(member => member.contacts.email === email);
        const memberData = member ? {
            firstName: member.first_name,
            lastName: member.last_name,
            role: member.role,
            photos: member.photos,
            contacts: member.contacts,
            description: member.description,
            research_keywords: member.research_keywords,
            highlighted_publications: member.highlighted_publications
        } : null;
        
        return Promise.resolve(memberData);
    },

    getFirstMemberByName(full_name) {
        const member = data.members.find(member => {
            const memberName = `${member.first_name.trim()} ${member.last_name.trim()}`.replace(/ /g, '-');
            return memberName === full_name;
        });

        const memberData = member ? {
            firstName: member.first_name,
            lastName: member.last_name,
            role: member.role,
            photos: member.photos,
            contacts: member.contacts,
            description: member.description,
            research_keywords: member.research_keywords,
            highlighted_publications: member.highlighted_publications,
            author_name: member.author_name
        } : null;

        return Promise.resolve(memberData);
    },

    getMemberByAuthorName(authorNames) {
        const members = data.members
            .filter(member => {
                return member.author_name ? member.author_name.some(name => authorNames.includes(name)) : false;
            })
            .map(member => ({
                first_name: member.first_name,
                last_name: member.last_name,
                contacts: member.contacts,
                photos: member.photos
            }));

        return Promise.resolve(members);
    }
}

export default MembersResource;