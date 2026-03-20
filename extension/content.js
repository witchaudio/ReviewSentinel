(() => {
  "use strict";

  const BADGE_ATTR = "data-reviewsentinel";
  let apiEndpoint = "https://reviewsentinel-api.onrender.com";

  // ── DOM helpers ────────────────────────────────────────────────────────────

  function scrapeReview(container) {
    const textEl = container.querySelector('[data-hook="review-body"] span');
    const text = textEl ? textEl.innerText.trim() : "";

    const starEl = container.querySelector('[data-hook="review-star-rating"] .a-icon-alt');
    let rating = 3;
    if (starEl) {
      const m = starEl.textContent.match(/(\d+(\.\d+)?)/);
      if (m) rating = Math.round(parseFloat(m[1]));
    }

    const verifiedEl =
      container.querySelector('[data-hook="avp-badge"]') ||
      container.querySelector('[data-hook="avp-badge-linkless"]');
    const verified = !!verifiedEl;

    const helpfulEl = container.querySelector('[data-hook="helpful-vote-statement"]');
    let helpful_votes = 0;
    if (helpfulEl) {
      const t = helpfulEl.textContent;
      if (/\bone\b/i.test(t)) {
        helpful_votes = 1;
      } else {
        const m = t.match(/(\d+)/);
        if (m) helpful_votes = parseInt(m[1], 10);
      }
    }

    return {
      id: container.id || null,
      text,
      rating,
      verified,
      helpful_votes,
      review_length: text.length,
    };
  }

  function scrapeReviews() {
    return Array.from(document.querySelectorAll('[data-hook="review"]'))
      .filter((el) => !el.hasAttribute(BADGE_ATTR));
  }

  // ── Badge injection ────────────────────────────────────────────────────────

  function injectBadge(container, result) {
    container.setAttribute(BADGE_ATTR, "1");

    const badge = document.createElement("div");
    badge.className = `rs-badge ${result.color}`;

    const verdict = document.createElement("span");
    verdict.className = "rs-verdict";
    verdict.textContent = `ReviewSentinel: ${result.verdict}`;
    badge.appendChild(verdict);

    if (result.reasons && result.reasons.length > 0) {
      const reasons = document.createElement("span");
      reasons.className = "rs-reasons";
      reasons.textContent = result.reasons.join(" · ");
      badge.appendChild(reasons);
    }

    // Insert after the review body
    const body = container.querySelector('[data-hook="review-body"]');
    if (body) {
      body.parentNode.insertBefore(badge, body.nextSibling);
    } else {
      container.prepend(badge);
    }
  }

  function injectOfflineBadge(container) {
    container.setAttribute(BADGE_ATTR, "offline");
    const badge = document.createElement("div");
    badge.className = "rs-badge grey";
    badge.innerHTML = '<span class="rs-verdict">ReviewSentinel offline</span>';
    const body = container.querySelector('[data-hook="review-body"]');
    if (body) {
      body.parentNode.insertBefore(badge, body.nextSibling);
    } else {
      container.prepend(badge);
    }
  }

  // ── API call (via background to avoid HTTPS→HTTP mixed-content block) ──────

  function scoreBatch(reviews, endpoint) {
    const payload = reviews.map(({ text, rating, verified, helpful_votes, review_length }) => ({
      text,
      rating,
      verified,
      helpful_votes,
      review_length,
    }));
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ type: "SCORE_BATCH", endpoint, payload }, (resp) => {
        if (chrome.runtime.lastError || !resp || !resp.ok) {
          resolve(null);
        } else {
          resolve(resp.results);
        }
      });
    });
  }

  // ── Main process ───────────────────────────────────────────────────────────

  async function processNewReviews() {
    const containers = scrapeReviews();
    if (containers.length === 0) return;

    // Mark immediately so concurrent MutationObserver re-triggers don't
    // re-process the same containers while we await the API response.
    containers.forEach((el) => el.setAttribute(BADGE_ATTR, "pending"));

    const reviews = containers.map(scrapeReview);
    const results = await scoreBatch(reviews, apiEndpoint);

    if (!results) {
      // API offline — show grey badge silently
      containers.forEach(injectOfflineBadge);
      return;
    }

    containers.forEach((container, i) => {
      if (results[i]) injectBadge(container, results[i]);
    });
  }

  // ── MutationObserver for infinite scroll ──────────────────────────────────

  let debounceTimer = null;

  const observer = new MutationObserver(() => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(processNewReviews, 400);
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // ── Init ───────────────────────────────────────────────────────────────────

  chrome.storage.sync.get("apiEndpoint", (data) => {
    if (data.apiEndpoint) apiEndpoint = data.apiEndpoint;
    processNewReviews();
  });
})();
