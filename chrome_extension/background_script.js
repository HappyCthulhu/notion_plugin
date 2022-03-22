chrome.runtime.onInstalled.addListener(() => {
    chrome.alarms.create('refresh', {periodInMinutes: 0.1});
});

chrome.alarms.onAlarm.addListener((alarm) => {

    function removeBookmarks(ids) {
        ids.forEach(function (id) {
            chrome.bookmarks.remove(id['bookmark_id']);

        });
        console.log("Страницы успешно удалены");
}

    const createBookmarks = (requestText) => {

        requestText.forEach(function (notion_page) {
            console.log("notion_page", notion_page)
            chrome.bookmarks.create({
                'parentId': '189',
                'title': notion_page.title,
                'url': notion_page.link,
            });
        });
    }

    let timerId = setInterval(async () => {
// {
//     "title": "test",
//     "link": "https://vk.com",
//     "last_edited_time": "2022-03-19T16:55:16",
//     "created_time": "2022-03-19T16:55:15",
//     "page_id": 4
// }
        let response = await fetch("http://127.0.0.1:5000/pages/add");
        let requestText = await response.json()
        console.log("requestText", requestText)


        if (Object.keys(requestText).length === 0) {
            console.log("Новых страниц нет");

        } else {
            console.log("Есть новые страницы");
            createBookmarks(requestText)
        }


        let remove_response = await fetch("http://127.0.0.1:5000/pages/remove");
        let remove_requestText = await remove_response.json()
        console.log("remove_requestText", remove_requestText)


        if (remove_requestText.length === 0) {
            console.log("Новых страниц для удаления нет");

        } else {
            console.log("Есть новые страницы для удаления");
            removeBookmarks(remove_requestText)
        }


    }, 2000);

});

