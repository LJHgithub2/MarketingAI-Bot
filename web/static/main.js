document
    .getElementById('info-form')
    .addEventListener('submit', function (event) {
        event.preventDefault();
        const inputValue = document.getElementById('info-input').value;

        // 서버로 비동기 요청 보내기
        fetch('http://localhost:8000/mysite/get_info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: inputValue }),
        })
            .then((response) => response.json())
            .then((data) => {
                console.log(data);
                renderData(data);
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    });

// JSON 데이터를 페이지에 출력하는 함수
function renderData(jsonData) {
    const section1Container = document.getElementById('section1');
    const section2Container = document.getElementById('section2');
    section1Container.innerHTML = '';
    section2Container.innerHTML = '';

    // Section 1 데이터 출력
    jsonData.section1.forEach((post) => {
        const postDiv = document.createElement('div');
        postDiv.classList.add('post');

        const img = document.createElement('img');
        img.src = post.img_path;
        img.alt = '이미지';
        postDiv.appendChild(img);

        const indexP = document.createElement('p');
        indexP.textContent = `Index: ${post.Index}`;
        postDiv.appendChild(indexP);

        const timeP = document.createElement('p');
        timeP.textContent = `생성시간: ${post['생성시간']}`;
        postDiv.appendChild(timeP);

        const contentP = document.createElement('p');
        contentP.textContent = `게시글내용: ${post['게시글내용']}`;
        postDiv.appendChild(contentP);

        const hashtagsP = document.createElement('p');
        hashtagsP.textContent = `해쉬태그: ${post['해쉬태그'].join(', ')}`;
        postDiv.appendChild(hashtagsP);

        section1Container.appendChild(postDiv);
    });

    // Section 2 데이터 출력
    const section2Div = document.createElement('div');
    section2Div.classList.add('post');
    const section2Content = document.createElement('p');
    section2Content.textContent = jsonData.section2;
    section2Div.appendChild(section2Content);
    section2Container.appendChild(section2Div);
}

// 페이지 로드 시 데이터 출력
// document.addEventListener('DOMContentLoaded', renderData);