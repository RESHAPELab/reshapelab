import Cite from 'citation-js';
import MembersResource from '../resource/people.js';

let jsonData;

async function fetchData() {
    const response = await fetch('/papers.bib');
    const data = await response.text();
    jsonData = Cite.input(data);
}

const ArticlesResource = {
    async getArticlesByAuthor(names) {
        await fetchData();

        return jsonData.filter(article => {
            
            if (!article.author) {
                return false;
            }

            return article.author.some(author => {
                const authorStr = Object.values(author).join(' ').toLowerCase();
                return names.some(name => authorStr.includes(name.toLowerCase()));
            });
        });
    },

    async getAllArticles() {
        await fetchData();

        return jsonData.sort((a, b) => {
            const yearA = a.issued['date-parts'][0][0];
            const yearB = b.issued['date-parts'][0][0];
            return yearB - yearA;
        });
    },

    async getArticlesByYear(year) {
        await fetchData();
    
        const filteredArticles = jsonData.filter(article => {
            return article.issued['date-parts'][0][0] === year;
        });
    
        const articlesWithAuthors = await Promise.all(filteredArticles.map(async article => {
            const authorNames = article.author ? article.author.map(author => Object.values(author).join(' ')) : [];
            const nau_authors = await MembersResource.getMemberByAuthorName(authorNames);
            return { ...article, nau_authors };
        }));
    
        return articlesWithAuthors;
    },

};

export default ArticlesResource;