function renderDetails(item) {
    let details = document.createElement('div');
    details.className = "details";
    details.style.display = "none"; // Ensure the details are hidden initially

    let keywordsDiv = document.createElement('div');
    item.keywords.forEach(keyword => {
        let keywordBox = document.createElement('div');
        keywordBox.className = "keyword-box";
        keywordBox.innerText = keyword;
        keywordsDiv.appendChild(keywordBox);
    });
    let description = document.createElement('p');
    description.innerHTML = item.description;
    details.appendChild(keywordsDiv);
    details.appendChild(description);
    return details;
}

function renderResult(item) {
    let wrapper = document.createElement('div');
    wrapper.className = "result";
    let img = document.createElement('img');
    img.src = item.image_url;
    img.width = 270;

    let details = renderDetails(item);
    wrapper.appendChild(img);
    wrapper.appendChild(details);

    wrapper.addEventListener('mouseover', function () {
        details.style.display = "block";
    });
    wrapper.addEventListener('mouseout', function () {
        details.style.display = "none";
    });
    return wrapper;
}