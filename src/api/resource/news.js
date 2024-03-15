import data from '/public/posts.json';

const NewsResource = {
    getNews() {
        const news = data.posts.map(news => ({
            id: news.id,
            title: news.title,
            date: news.date,
            person: news.person,
            tag: news.tag,
            image: news.image,
            description: news.description
        }));

        return Promise.resolve(news);
    },

    getNewsById(id) {
        const news = data.posts.find(news => news.id === id);
        const newsData = news ? {
            title: news.title,
            date: news.date,
            person: news.person,
            tag: news.tag,
            image: news.image,
            description: news.description
        } : null;

        return Promise.resolve(newsData);
    }
}

export default NewsResource;