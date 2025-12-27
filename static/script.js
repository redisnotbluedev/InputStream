const resultsContainer = document.getElementById("results");
const paginationContainer = document.getElementById("pagination");
const searchForm = document.getElementById("searchForm");
const searchQuery = document.getElementById("searchQuery");

let currentPage = 1;
let currentQuery = "";
let currentPerPage = 20;

// I have no idea what this is.
function highlightText(text, tokens) {
	if (!tokens || tokens.length === 0) return text;

	tokens.sort((a, b) => b.length - a.length);
	const regex = new RegExp(`(${tokens.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "g");

	return text.replace(regex, `<span class="result-match">$1</span>`);
}

async function getData(page, perPage) {
	const response = await fetch("/search", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			query: currentQuery,
			page: page,
			per_page: perPage
		})
	});
	if (!response.ok) {
		throw new Error(response.status);
	} else {
		return await response.json();
	}
}

function displayResults(results, tokens) {
	resultsContainer.innerHTML = "";
	results.forEach(result => {
		const item = document.createElement("li");

		const isoStart = result.start.replace(",", ".")
		const isoEnd = result.end.replace(",", ".");

		item.innerHTML = `
			<h3 class="result-name">
				<span class="result-title">${result.show}</span>
				<span>Season ${result.season}, Episode ${result.episode}</span>
			</h3>
			<p class="result-text">
				${highlightText(result.text, tokens)}
			</p>
			<small class="result-time">
				(from
					<time datetime="${isoStart}">${result.start}</time>
				to
					<time datetime="${isoEnd}">${result.end}</time>)
			</small>`;
		resultsContainer.appendChild(item);
	});
}

function displayPagination(data) {
	paginationContainer.innerHTML = "";
	if (currentPage > 1) {
		const prevButton = document.createElement("button");
		prevButton.textContent = "Previous";
		prevButton.onclick = () => {
			currentPage--;
			loadPage();
		};
		paginationContainer.appendChild(prevButton);
	}

	const pageNumber = document.createElement("span");
	pageNumber.innerText = `Page ${currentPage}`;
	paginationContainer.appendChild(pageNumber);

	if (data.has_more) {
		const nextButton = document.createElement("button");
		nextButton.textContent = "Next";
		nextButton.onclick = () => {
			currentPage++;
			loadPage();
		};
		paginationContainer.appendChild(nextButton);
	}
}

async function loadPage() {
	const data = await getData(currentPage, currentPerPage);
	displayResults(data.results, data.query_tokens);
	displayPagination(data);
}

searchForm.addEventListener("submit", async event => {
	event.preventDefault();
	currentQuery = searchQuery.value;
	currentPage = 1;

	loadPage();
});
