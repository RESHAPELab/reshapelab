import data from '/public/posts.json';

const NewsResource = {
    getNews() {
        const news = data.posts.map(news => ({
            title: news.title,
            date: news.date,
            person: news.person,
            tag: news.tag,
            image: news.image,
            description: news.description
        }));

        return Promise.resolve(news);
    }
}

export default NewsResource;