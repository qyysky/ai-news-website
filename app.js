const grid = document.querySelector('#newsGrid');
const sourceFilters = document.querySelector('#sourceFilters');
let news = [];
let selectedSource = 'all';

const displayDate = (iso) => new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }).format(new Date(iso));
const displayTime = (iso) => new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date(iso));

function render() {
  const visible = selectedSource === 'all' ? news : news.filter(item => item.source === selectedSource);
  grid.innerHTML = visible.length ? visible.map(item => `
    <a class="card" href="${item.url}" target="_blank" rel="noopener noreferrer">
      <div class="card-meta"><span class="source">${item.source}</span><time>${displayTime(item.published)}</time></div>
      <h3>${item.title}</h3>
      <div class="card-bottom"><span>阅读原文</span><span class="arrow">↗</span></div>
    </a>`).join('') : '<p class="empty">这个来源暂时没有可显示的新闻。</p>';
}

function setupFilters() {
  const counts = news.reduce((map, item) => ({ ...map, [item.source]: (map[item.source] || 0) + 1 }), {});
  document.querySelector('#totalBadge').textContent = news.length;
  sourceFilters.innerHTML = Object.entries(counts).map(([source, count]) => `<button class="filter" data-source="${source}">${source} <span>${count}</span></button>`).join('');
  document.querySelectorAll('.filter').forEach(button => button.addEventListener('click', () => {
    selectedSource = button.dataset.source;
    document.querySelectorAll('.filter').forEach(el => el.classList.toggle('active', el === button));
    render();
  }));
}

async function init() {
  try {
    const response = await fetch('./data/news.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('news data unavailable');
    const data = await response.json();
    news = data.items || [];
    document.querySelector('#editionDate').textContent = displayDate(data.generated_at);
    document.querySelector('#articleCount').textContent = `${news.length} 篇资讯`;
    document.querySelector('#updatedAt').textContent = `更新于 ${displayTime(data.generated_at)}`;
    setupFilters(); render();
  } catch (_) {
    grid.innerHTML = '<p class="empty">新闻数据暂时无法加载。请稍后刷新页面。</p>';
    document.querySelector('#editionDate').textContent = '新闻数据暂时不可用';
  }
}
init();
