(function () {
  const numberOfPartnersLabel = document.querySelector(
    ".js-find-a-partner__number"
  );
  const searchBox = document.querySelector(".js-find-a-partner__search-input");
  const urlParams = new URLSearchParams(window.location.search);
  const partners = document.querySelectorAll(".js-find-a-partner__partner");
  const checkboxes = document.querySelectorAll(".js-find-a-partner__filter");
  const searchResetButton = document.querySelector(".p-search-box__reset");
  const noResults = document.querySelector(".js-find-a-partner__no-results");

  var filters = [];

  function init() {
    revealSearch();

    if (searchBox) {
      populateTextbox();
      searchDom();
      searchBox.addEventListener("keyup", searchHandler);
    }

    populateCheckboxes();

    updateFilterList();

    if (checkboxes) {
      filterDom();
      checkboxes.forEach(function (checkbox) {
        checkbox.addEventListener("change", filterHandler);
      });
    }

    if (searchResetButton) {
      searchResetButton.addEventListener("click", searchHandler);
    }

    updateNumberOfPartners();
    updateNoResultsMessage();
  }

  // Display no reults message
  function updateNoResultsMessage() {
    if (noResults) {
      if (numberOfPartnersLabel.innerHTML === "0") {
        noResults.classList.remove("u-hide");
      } else {
        noResults.classList.add("u-hide");
      }
    }
  }

  // Show search and filter functionality if JS is available
  function revealSearch() {
    var searchForm = document.querySelector(".js-search-form");
    if (searchForm) {
      searchForm.classList.remove("u-hide");
    }
  }

  // Debounced search handler function
  searchHandler = debounce(function (e) {
    searchDom();
    updateNumberOfPartners();
    updateNoResultsMessage();
    updateUrl("search", searchBox.value);
  }, 350);

  function searchDom() {
    if (partners) {
      partners.forEach(function (partner) {
        partner.classList.remove("js-searched");
        var searchText = partner.getAttribute("data-searchText").toLowerCase();
        if (searchText.includes(searchBox.value)) {
          partner.classList.add("js-searched");
        }
      });
    }
  }

  function filterHandler() {
    updateFilterList();
    filterDom();
    updateNumberOfPartners();
    updateNoResultsMessage();
    updateUrl("filters", filters);
  }

  function filterDom() {
    if (filters.length === 0 && partners) {
      partners.forEach((partner) => {
        partner.classList.add("js-filtered");
      });
    } else if (partners) {
      partners.forEach((partner) => {
        partner.classList.remove("js-filtered");
        var filterText = partner.getAttribute("data-filter").toLowerCase();
        if (filterCheck(filterText)) {
          partner.classList.add("js-filtered");
        }
      });
    }
  }

  function debounce(func, wait, immediate) {
    var timeout;
    return function () {
      var context = this,
        args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(function () {
        timeout = null;
        if (!immediate) func.apply(context, args);
      }, wait);
      if (immediate && !timeout) func.apply(context, args);
    };
  }

  // Update browser url updateUrl
  function updateUrl(type, value) {
    const currentUrl = window.location.href;
    const baseUrl = currentUrl.split("?")[0];
    var newUrl = baseUrl;

    if (!(searchBox.value === "") && filters.length > 0) {
      filtersString = "";
      filters.forEach((filter, i) => {
        if (i === filters.length - 1) {
          filtersString += filter;
        } else {
          filtersString += `${filter},`;
        }
      });
      newUrl = `${baseUrl}?search=${searchBox.value}&filters=${filtersString}`;
    }
    if (!(searchBox.value === "") && filters.length === 0) {
      newUrl = `${baseUrl}?search=${searchBox.value}`;
    }
    if (searchBox.value === "" && filters.length > 0) {
      filtersString = "";
      filters.forEach((filter, i) => {
        if (i === filters.length - 1) {
          filtersString += filter;
        } else {
          filtersString += `${filter},`;
        }
      });
      newUrl = `${baseUrl}?filters=${filtersString}`;
    }
    window.history.pushState(
      { search: searchBox.value, filters: filters },
      "",
      newUrl
    );
  }

  // Check if element should be filtered
  function filterCheck(filterText) {
    var match = false;
    filters.forEach((filter) => {
      if (filterText.includes(filter.toLowerCase()) && !match) {
        match = true;
      }
    });
    return match;
  }

  // Update filters array to match checked checkboxes
  function updateFilterList() {
    if (checkboxes) {
      filters = [];
      checkboxes.forEach((checkbox) => {
        if (checkbox.checked) {
          filters.push(checkbox.name);
        }
      });
    }
  }

  // Check any checkboxes that match URL filters query
  function populateCheckboxes() {
    const queryFilters = urlParams.get("filters");
    if (queryFilters) {
      queryFilters.split(",").forEach((filter) => {
        var checkboxObject = document.querySelector("#" + filter.toLocaleLowerCase());
        if (checkboxObject) {
          checkboxObject.checked = true;
        }
      });
    }
  }

  // Update search box text with data from query params
  function populateTextbox() {
    const querySearchText = urlParams.get("search");
    if (searchBox && querySearchText) {
      searchBox.focus();
      searchBox.value = querySearchText;
    }
  }

  // Update number of partners mtachig search and/or filter criteria
  function updateNumberOfPartners() {
    if (numberOfPartnersLabel) {
      numberOfPartnersLabel.innerHTML = document.querySelectorAll(
        ".js-find-a-partner__partner.js-searched.js-filtered"
      ).length;
    }
  }

  init();
})();
