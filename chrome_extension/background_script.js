chrome.runtime.onInstalled.addListener(() => {
    chrome.alarms.create('refresh', {periodInMinutes: 0.1});
});

chrome.alarms.onAlarm.addListener((alarm) => {
    function helloWorld() {
        console.log("Hello, world!");
    }

    function removeBookmarks(ids) {
        ids.forEach(function (id, ids) {
            console.log("removeBookmark work!");

            var bookmarkId = id;
            var removingBookmark = chrome.bookmarks.remove(bookmarkId);
        });
        console.log("Страницы успешно удалены");

    }

    const createBookmarks = (requestText) => {

        requestText.forEach(function (item, requestText) {
            console.log("item", item)
            chrome.bookmarks.create({
                'parentId': '2279',
                'title': item.title,
                'url': item.page_url,
            });
        });
    }

    let timerId = setInterval(async () => {

        let response = await fetch("http://127.0.0.1:5000/add");
        let requestText = await response.json()
        console.log("requestText", requestText)


        if (Object.keys(requestText).length === 0) {
            console.log("Новых страниц нет");

        } else {
            console.log("Есть новые страницы");
            createBookmarks(requestText)
        }


        let remove_response = await fetch("http://127.0.0.1:5000/remove");
        let remove_requestText = await remove_response.json()
        console.log("remove_requestText", remove_requestText)


        if (Object.keys(remove_requestText).length === 0) {
            console.log("Новых страниц для удаления нет");

        } else {
            console.log("Есть новые страницы для удаления");
            removeBookmarks(remove_requestText)
        }


        console.log('It worked!');
    }, 2000);

});

