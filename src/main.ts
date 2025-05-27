import './style.css'

type Car = {
    title?: string;
    price?: string;
    region?: string;
    exchange?: number | string;
    panel?: number | string;
    corrosion?: number | string;
    url?: string;
};

const root = document.getElementById('car-list-root') as HTMLElement;

function groupByTitle(cars: Car[]): Record<string, Car[]> {
    return cars.reduce((acc, car) => {
        const title = car.title || '제목 없음';
        if (!acc[title]) acc[title] = [];
        acc[title].push(car);
        return acc;
    }, {} as Record<string, Car[]>);
}

function renderTabs(cars: Car[]): void {
    if (!cars.length) {
        root.innerHTML = `<div class="empty-message">조건에 맞는 차량이 없습니다.</div>`;
        return;
    }
    const grouped = groupByTitle(cars);
    const titles = Object.keys(grouped);
    let activeIdx = 0;

    // 탭 바와 컨텐츠 영역을 분리해서 렌더링
    root.innerHTML = `
        <div class="tab-bar"></div>
        <div id="tab-content"></div>
    `;
    const tabBar = root.querySelector('.tab-bar')!;
    const tabContent = root.querySelector('#tab-content')!;

    // 탭 바 버튼 생성
    tabBar.innerHTML = titles.map((title, i) => `
        <button class="tab-btn${i === activeIdx ? ' active' : ''}" data-idx="${i}">${title}</button>
    `).join('');

    // 컨텐츠 렌더 함수
    function renderContent(idx: number) {
        const titleKey = titles[idx] ?? '';
        const group: Car[] = (titleKey && grouped[titleKey]) ? grouped[titleKey] : [];
        tabContent.innerHTML = `
            <section class="car-group">
                <div class="table-wrap">
                    <table class="car-table">
                        <thead>
                            <tr>
                                <th>가격</th>
                                <th>지역</th>
                                <th>교환</th>
                                <th>판금</th>
                                <th>부식</th>
                                <th>링크</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${group.map((car: Car) => `
                                <tr>
                                    <td>${car.price || '-'}</td>
                                    <td>${car.region || '-'}</td>
                                    <td>${car.exchange ?? '-'}</td>
                                    <td>${car.panel ?? '-'}</td>
                                    <td>${car.corrosion ?? '-'}</td>
                                    <td>${car.url ? `<a class=\"car-link\" href=\"${car.url}\" target=\"_blank\">바로가기</a>` : '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </section>
        `;
    }

    // 최초 컨텐츠 렌더
    renderContent(activeIdx);

    // 탭 버튼 이벤트 바인딩
    const tabBtns = tabBar.querySelectorAll<HTMLButtonElement>('.tab-btn');
    tabBtns.forEach(btn => {
        btn.onclick = () => {
            const idx = Number(btn.dataset.idx);
            if (idx !== activeIdx) {
                if (tabBtns[activeIdx]) {
                    tabBtns[activeIdx].classList.remove('active');
                }
                btn.classList.add('active');
                activeIdx = idx;
                renderContent(activeIdx);
                btn.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
            }
        };
    });
}

function renderError(message: string): void {
    root.innerHTML = `<div class="empty-message">${message}</div>`;
}

fetch('good_cars.json')
    .then(res => {
        if (!res.ok) throw new Error('파일 없음');
        return res.json();
    })
    .then((data: { cars?: Car[] }) => {
        const cars = Array.isArray(data.cars) ? data.cars : [];
        renderTabs(cars);
    })
    .catch(() => {
        renderError('good_cars.json 파일이 존재하지 않거나<br>차량 데이터가 없습니다.');
    });
