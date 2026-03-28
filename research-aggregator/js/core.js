/**
 * ============================================
 * RESEARCH AGGREGATOR - CORE ENGINE
 * ============================================
 * Main application controller managing:
 * - RSS Feed Aggregation
 * - Glossary/Definition System
 * - Content Length Management
 * - Navigation & Routing
 * - Search Functionality
 */

// ============================================
// APPLICATION STATE
// ============================================

const AppState = {
    currentPortal: null,
    contentLength: 6, // Default: 6 pages (adjustable 1-12)
    searchQuery: '',
    activeFilters: [],
    feeds: new Map(),
    glossary: new Map(),
    guideProgress: {},
    isLoading: false,
    definitionWindowActive: false
};

// ============================================
// RSS FEED AGGREGATOR ENGINE
// ============================================

class RSSAggregator {
    constructor() {
        this.feeds = new Map();
        this.articles = [];
        this.corsProxy = 'https://api.allorigins.win/raw?url=';
        this.cacheTimeout = 15 * 60 * 1000; // 15 minutes
        this.cache = new Map();
    }

    /**
     * Add a new RSS feed source
     * @param {string} id - Unique feed identifier
     * @param {Object} config - Feed configuration
     */
    addFeed(id, config) {
        this.feeds.set(id, {
            id,
            name: config.name,
            url: config.url,
            category: config.category,
            icon: config.icon || '📰',
            description: config.description || '',
            lastFetched: null,
            articles: []
        });
    }

    /**
     * Fetch and parse RSS feed
     * @param {string} feedId - Feed identifier to fetch
     * @returns {Promise<Array>} - Parsed articles
     */
    async fetchFeed(feedId) {
        const feed = this.feeds.get(feedId);
        if (!feed) throw new Error(`Feed not found: ${feedId}`);

        // Check cache
        const cached = this.cache.get(feedId);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }

        try {
            const response = await fetch(this.corsProxy + encodeURIComponent(feed.url));
            if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

            const text = await response.text();
            const articles = this.parseRSS(text, feed);

            // Update cache
            this.cache.set(feedId, {
                timestamp: Date.now(),
                data: articles
            });

            feed.articles = articles;
            feed.lastFetched = new Date();

            return articles;
        } catch (error) {
            console.error(`Error fetching feed ${feedId}:`, error);
            // Return cached data if available, even if stale
            if (cached) return cached.data;
            throw error;
        }
    }

    /**
     * Parse RSS/XML content into articles
     * @param {string} xmlText - Raw XML content
     * @param {Object} feed - Feed configuration
     * @returns {Array} - Parsed articles
     */
    parseRSS(xmlText, feed) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(xmlText, 'text/xml');

        // Check for parsing errors
        const parseError = doc.querySelector('parsererror');
        if (parseError) {
            throw new Error('Invalid RSS format');
        }

        const articles = [];

        // Try RSS 2.0 format first
        let items = doc.querySelectorAll('item');

        // Fall back to Atom format
        if (items.length === 0) {
            items = doc.querySelectorAll('entry');
        }

        items.forEach((item, index) => {
            const article = {
                id: `${feed.id}-${index}`,
                feedId: feed.id,
                feedName: feed.name,
                feedIcon: feed.icon,
                title: this.getElementText(item, 'title'),
                link: this.getElementText(item, 'link') || this.getAtomLink(item),
                description: this.cleanHTML(this.getElementText(item, 'description') ||
                                          this.getElementText(item, 'summary') ||
                                          this.getElementText(item, 'content')),
                pubDate: this.parseDate(this.getElementText(item, 'pubDate') ||
                                       this.getElementText(item, 'published') ||
                                       this.getElementText(item, 'updated')),
                author: this.getElementText(item, 'author') ||
                       this.getElementText(item, 'dc:creator'),
                categories: this.getCategories(item),
                thumbnail: this.getThumbnail(item)
            };

            if (article.title && article.link) {
                articles.push(article);
            }
        });

        return articles.sort((a, b) => b.pubDate - a.pubDate);
    }

    /**
     * Helper: Get text content from element
     */
    getElementText(parent, tagName) {
        const element = parent.querySelector(tagName);
        return element ? element.textContent.trim() : '';
    }

    /**
     * Helper: Get Atom link
     */
    getAtomLink(item) {
        const link = item.querySelector('link[rel="alternate"]') ||
                    item.querySelector('link');
        return link ? link.getAttribute('href') : '';
    }

    /**
     * Helper: Parse date string
     */
    parseDate(dateStr) {
        if (!dateStr) return new Date(0);
        const date = new Date(dateStr);
        return isNaN(date.getTime()) ? new Date(0) : date;
    }

    /**
     * Helper: Extract categories/tags
     */
    getCategories(item) {
        const categories = [];
        item.querySelectorAll('category').forEach(cat => {
            categories.push(cat.textContent.trim());
        });
        return categories;
    }

    /**
     * Helper: Extract thumbnail image
     */
    getThumbnail(item) {
        // Try media:thumbnail
        const mediaThumbnail = item.querySelector('media\\:thumbnail, thumbnail');
        if (mediaThumbnail) {
            return mediaThumbnail.getAttribute('url');
        }

        // Try enclosure
        const enclosure = item.querySelector('enclosure[type^="image"]');
        if (enclosure) {
            return enclosure.getAttribute('url');
        }

        // Try to extract from description/content
        const description = this.getElementText(item, 'description') ||
                           this.getElementText(item, 'content');
        const imgMatch = description.match(/<img[^>]+src=["']([^"']+)["']/i);
        if (imgMatch) {
            return imgMatch[1];
        }

        return null;
    }

    /**
     * Helper: Clean HTML from text
     */
    cleanHTML(html) {
        if (!html) return '';
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent.substring(0, 300) + (div.textContent.length > 300 ? '...' : '');
    }

    /**
     * Fetch all feeds for a category
     * @param {string} category - Category to fetch
     * @returns {Promise<Array>} - Combined articles
     */
    async fetchByCategory(category) {
        const feedsInCategory = Array.from(this.feeds.values())
            .filter(feed => feed.category === category);

        const promises = feedsInCategory.map(feed =>
            this.fetchFeed(feed.id).catch(err => {
                console.error(`Failed to fetch ${feed.id}:`, err);
                return [];
            })
        );

        const results = await Promise.all(promises);
        return results.flat().sort((a, b) => b.pubDate - a.pubDate);
    }

    /**
     * Search across all feeds
     * @param {string} query - Search query
     * @returns {Array} - Matching articles
     */
    search(query) {
        const lowerQuery = query.toLowerCase();
        const allArticles = Array.from(this.feeds.values())
            .flatMap(feed => feed.articles);

        return allArticles.filter(article =>
            article.title.toLowerCase().includes(lowerQuery) ||
            article.description.toLowerCase().includes(lowerQuery) ||
            article.categories.some(cat => cat.toLowerCase().includes(lowerQuery))
        );
    }
}

// ============================================
// GLOSSARY & DEFINITION SYSTEM
// ============================================

class GlossarySystem {
    constructor() {
        this.terms = new Map();
        this.definitionWindow = null;
        this.hideTimeout = null;
        this.currentTerm = null;
    }

    /**
     * Initialize the glossary system
     */
    init() {
        // Create definition window
        this.createDefinitionWindow();

        // Set up event delegation for glossary terms
        document.addEventListener('mouseover', this.handleMouseOver.bind(this));
        document.addEventListener('mouseout', this.handleMouseOut.bind(this));
    }

    /**
     * Create the floating definition window
     */
    createDefinitionWindow() {
        this.definitionWindow = document.createElement('div');
        this.definitionWindow.id = 'definition-window';
        this.definitionWindow.innerHTML = `
            <div class="definition-header">
                <h4>
                    <span class="term-name"></span>
                    <span class="term-category"></span>
                </h4>
            </div>
            <div class="definition-content">
                <div class="definition-text"></div>
                <div class="definition-example">
                    <div class="definition-example-label">Example</div>
                    <div class="definition-example-text"></div>
                </div>
                <div class="definition-related">
                    <div class="definition-related-label">Related Terms</div>
                    <div class="definition-related-tags"></div>
                </div>
            </div>
        `;
        document.body.appendChild(this.definitionWindow);

        // Keep window visible when hovering over it
        this.definitionWindow.addEventListener('mouseenter', () => {
            clearTimeout(this.hideTimeout);
            AppState.definitionWindowActive = true;
        });

        this.definitionWindow.addEventListener('mouseleave', () => {
            this.hideWindow();
        });

        // Handle clicks on related terms
        this.definitionWindow.addEventListener('click', (e) => {
            if (e.target.classList.contains('related-tag')) {
                const termId = e.target.dataset.term;
                if (termId && this.terms.has(termId)) {
                    this.showDefinition(termId);
                }
            }
        });
    }

    /**
     * Add term to glossary
     * @param {string} id - Term identifier
     * @param {Object} definition - Term definition object
     */
    addTerm(id, definition) {
        this.terms.set(id, {
            id,
            term: definition.term,
            category: definition.category || 'General',
            definition: definition.definition,
            example: definition.example || null,
            relatedTerms: definition.relatedTerms || []
        });
    }

    /**
     * Add multiple terms at once
     * @param {Object} termsObject - Object with term definitions
     */
    addTerms(termsObject) {
        Object.entries(termsObject).forEach(([id, definition]) => {
            this.addTerm(id, definition);
        });
    }

    /**
     * Handle mouseover on glossary terms
     */
    handleMouseOver(e) {
        const termElement = e.target.closest('.glossary-term');
        if (termElement) {
            clearTimeout(this.hideTimeout);
            const termId = termElement.dataset.term;
            if (termId && this.terms.has(termId)) {
                this.showDefinition(termId);
            }
        }
    }

    /**
     * Handle mouseout from glossary terms
     */
    handleMouseOut(e) {
        const termElement = e.target.closest('.glossary-term');
        if (termElement && !this.isHoveringWindow(e)) {
            this.scheduleHide();
        }
    }

    /**
     * Check if mouse is moving to definition window
     */
    isHoveringWindow(e) {
        const rect = this.definitionWindow.getBoundingClientRect();
        return (
            e.clientX >= rect.left - 20 &&
            e.clientX <= rect.right + 20 &&
            e.clientY >= rect.top - 20 &&
            e.clientY <= rect.bottom + 20
        );
    }

    /**
     * Show definition for a term
     * @param {string} termId - Term identifier
     */
    showDefinition(termId) {
        const term = this.terms.get(termId);
        if (!term) return;

        this.currentTerm = termId;

        // Update window content
        const nameEl = this.definitionWindow.querySelector('.term-name');
        const categoryEl = this.definitionWindow.querySelector('.term-category');
        const textEl = this.definitionWindow.querySelector('.definition-text');
        const exampleContainer = this.definitionWindow.querySelector('.definition-example');
        const exampleTextEl = this.definitionWindow.querySelector('.definition-example-text');
        const relatedContainer = this.definitionWindow.querySelector('.definition-related');
        const relatedTagsEl = this.definitionWindow.querySelector('.definition-related-tags');

        nameEl.textContent = term.term;
        categoryEl.textContent = term.category;
        textEl.textContent = term.definition;

        // Show/hide example
        if (term.example) {
            exampleContainer.style.display = 'block';
            exampleTextEl.textContent = term.example;
        } else {
            exampleContainer.style.display = 'none';
        }

        // Show/hide related terms
        if (term.relatedTerms.length > 0) {
            relatedContainer.style.display = 'block';
            relatedTagsEl.innerHTML = term.relatedTerms
                .filter(rt => this.terms.has(rt))
                .map(rt => `<span class="related-tag" data-term="${rt}">${this.terms.get(rt).term}</span>`)
                .join('');
        } else {
            relatedContainer.style.display = 'none';
        }

        // Show window with animation
        this.definitionWindow.classList.add('active');
        AppState.definitionWindowActive = true;
    }

    /**
     * Schedule hiding the definition window
     */
    scheduleHide() {
        this.hideTimeout = setTimeout(() => {
            this.hideWindow();
        }, 300);
    }

    /**
     * Hide the definition window
     */
    hideWindow() {
        this.definitionWindow.classList.remove('active');
        AppState.definitionWindowActive = false;
        this.currentTerm = null;
    }

    /**
     * Mark glossary terms in HTML content
     * @param {string} html - HTML content
     * @returns {string} - HTML with marked glossary terms
     */
    markTermsInContent(html) {
        let result = html;

        this.terms.forEach((termDef, termId) => {
            const term = termDef.term;
            // Create regex that matches whole words only, case insensitive
            const regex = new RegExp(`\\b(${this.escapeRegex(term)})\\b`, 'gi');

            result = result.replace(regex, (match) => {
                return `<span class="glossary-term" data-term="${termId}">${match}</span>`;
            });
        });

        return result;
    }

    /**
     * Escape special regex characters
     */
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
}

// ============================================
// CONTENT LENGTH MANAGER
// ============================================

class ContentLengthManager {
    constructor() {
        this.maxPages = 12;
        this.minPages = 1;
        this.currentLength = 6;
        this.wordsPerPage = 500; // Approximate words per page
    }

    /**
     * Initialize content length controls
     */
    init() {
        const slider = document.querySelector('.content-length-slider');
        const valueDisplay = document.querySelector('.content-length-value');

        if (slider) {
            slider.min = this.minPages;
            slider.max = this.maxPages;
            slider.value = this.currentLength;

            slider.addEventListener('input', (e) => {
                this.setLength(parseInt(e.target.value));
                if (valueDisplay) {
                    valueDisplay.textContent = `${this.currentLength} pages`;
                }
            });
        }
    }

    /**
     * Set content length
     * @param {number} pages - Number of pages
     */
    setLength(pages) {
        this.currentLength = Math.max(this.minPages, Math.min(this.maxPages, pages));
        AppState.contentLength = this.currentLength;
        this.updateContentVisibility();
    }

    /**
     * Update visibility of content sections based on length
     */
    updateContentVisibility() {
        const sections = document.querySelectorAll('.guide-section');
        const totalSections = sections.length;
        const visibleSections = Math.ceil((this.currentLength / this.maxPages) * totalSections);

        sections.forEach((section, index) => {
            if (index < visibleSections) {
                section.style.display = 'block';
                section.classList.remove('content-hidden');
            } else {
                section.style.display = 'none';
                section.classList.add('content-hidden');
            }
        });

        // Update progress
        this.updateProgress(visibleSections, totalSections);
    }

    /**
     * Update progress indicator
     */
    updateProgress(visible, total) {
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');

        if (progressFill) {
            progressFill.style.width = `${(visible / total) * 100}%`;
        }

        if (progressText) {
            progressText.textContent = `Showing ${visible} of ${total} sections`;
        }
    }

    /**
     * Get word limit based on current length
     */
    getWordLimit() {
        return this.currentLength * this.wordsPerPage;
    }

    /**
     * Truncate content to fit page limit
     * @param {string} content - Full content
     * @returns {string} - Truncated content
     */
    truncateContent(content) {
        const wordLimit = this.getWordLimit();
        const words = content.split(/\s+/);

        if (words.length <= wordLimit) {
            return content;
        }

        return words.slice(0, wordLimit).join(' ') + '...';
    }
}

// ============================================
// GUIDE INDEX SYSTEM
// ============================================

class GuideIndexSystem {
    constructor() {
        this.sections = [];
        this.currentSection = null;
        this.observer = null;
    }

    /**
     * Initialize the guide index
     */
    init() {
        this.buildIndex();
        this.setupScrollSpy();
        this.setupNavigation();
    }

    /**
     * Build index from page sections
     */
    buildIndex() {
        const indexContainer = document.querySelector('.guide-index-list');
        if (!indexContainer) return;

        const sections = document.querySelectorAll('.guide-section');
        this.sections = Array.from(sections);

        indexContainer.innerHTML = this.sections.map((section, index) => {
            const title = section.querySelector('.guide-section-title')?.textContent || `Section ${index + 1}`;
            const id = section.id || `section-${index}`;
            section.id = id;

            // Check for subsections
            const subsections = section.querySelectorAll('h3');
            const nestedHTML = subsections.length > 0 ? `
                <ul class="guide-index-nested">
                    ${Array.from(subsections).map((sub, subIndex) => {
                        const subId = `${id}-sub-${subIndex}`;
                        sub.id = subId;
                        return `
                            <li class="guide-index-item">
                                <a href="#${subId}" class="guide-index-link">
                                    <span class="guide-index-number">${index + 1}.${subIndex + 1}</span>
                                    ${sub.textContent}
                                </a>
                            </li>
                        `;
                    }).join('')}
                </ul>
            ` : '';

            return `
                <li class="guide-index-item">
                    <a href="#${id}" class="guide-index-link" data-section="${index}">
                        <span class="guide-index-number">${index + 1}</span>
                        ${title}
                    </a>
                    ${nestedHTML}
                </li>
            `;
        }).join('');
    }

    /**
     * Setup intersection observer for scroll spy
     */
    setupScrollSpy() {
        if (!this.sections.length) return;

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.setActiveSection(entry.target.id);
                }
            });
        }, {
            threshold: 0.2,
            rootMargin: '-20% 0px -70% 0px'
        });

        this.sections.forEach(section => {
            this.observer.observe(section);
        });
    }

    /**
     * Set active section in index
     * @param {string} sectionId - Active section ID
     */
    setActiveSection(sectionId) {
        this.currentSection = sectionId;

        document.querySelectorAll('.guide-index-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${sectionId}`) {
                link.classList.add('active');
            }
        });

        // Update progress
        const sectionIndex = this.sections.findIndex(s => s.id === sectionId);
        if (sectionIndex >= 0) {
            const progress = ((sectionIndex + 1) / this.sections.length) * 100;
            const progressFill = document.querySelector('.progress-fill');
            if (progressFill) {
                progressFill.style.width = `${progress}%`;
            }
        }
    }

    /**
     * Setup click navigation
     */
    setupNavigation() {
        document.querySelectorAll('.guide-index-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href').substring(1);
                const target = document.getElementById(targetId);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    }
}

// ============================================
// SEARCH SYSTEM
// ============================================

class SearchSystem {
    constructor(aggregator) {
        this.aggregator = aggregator;
        this.searchInput = null;
        this.resultsContainer = null;
        this.debounceTimeout = null;
    }

    /**
     * Initialize search functionality
     */
    init() {
        this.searchInput = document.querySelector('.search-input');
        this.resultsContainer = document.querySelector('.search-results');

        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });

            this.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.clearSearch();
                }
            });
        }
    }

    /**
     * Handle search input with debouncing
     * @param {string} query - Search query
     */
    handleSearch(query) {
        clearTimeout(this.debounceTimeout);

        if (query.length < 2) {
            this.clearResults();
            return;
        }

        this.debounceTimeout = setTimeout(() => {
            this.performSearch(query);
        }, 300);
    }

    /**
     * Perform search
     * @param {string} query - Search query
     */
    performSearch(query) {
        AppState.searchQuery = query;

        // Search RSS articles
        const articleResults = this.aggregator.search(query);

        // Search guide content (if available)
        const guideResults = this.searchGuideContent(query);

        this.displayResults(articleResults, guideResults);
    }

    /**
     * Search within guide content
     * @param {string} query - Search query
     * @returns {Array} - Matching sections
     */
    searchGuideContent(query) {
        const results = [];
        const lowerQuery = query.toLowerCase();

        document.querySelectorAll('.guide-section').forEach(section => {
            const title = section.querySelector('.guide-section-title')?.textContent || '';
            const content = section.textContent;

            if (title.toLowerCase().includes(lowerQuery) ||
                content.toLowerCase().includes(lowerQuery)) {
                results.push({
                    id: section.id,
                    title: title,
                    excerpt: this.getExcerpt(content, query),
                    type: 'guide'
                });
            }
        });

        return results;
    }

    /**
     * Get excerpt around search match
     * @param {string} content - Full content
     * @param {string} query - Search query
     * @returns {string} - Excerpt with context
     */
    getExcerpt(content, query) {
        const lowerContent = content.toLowerCase();
        const lowerQuery = query.toLowerCase();
        const index = lowerContent.indexOf(lowerQuery);

        if (index === -1) return content.substring(0, 150) + '...';

        const start = Math.max(0, index - 50);
        const end = Math.min(content.length, index + query.length + 100);
        let excerpt = content.substring(start, end);

        if (start > 0) excerpt = '...' + excerpt;
        if (end < content.length) excerpt = excerpt + '...';

        return excerpt;
    }

    /**
     * Display search results
     * @param {Array} articles - RSS article results
     * @param {Array} guides - Guide section results
     */
    displayResults(articles, guides) {
        if (!this.resultsContainer) return;

        const totalResults = articles.length + guides.length;

        if (totalResults === 0) {
            this.resultsContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <h4 class="empty-state-title">No results found</h4>
                    <p class="empty-state-description">Try different keywords or browse the categories</p>
                </div>
            `;
            return;
        }

        this.resultsContainer.innerHTML = `
            <div class="search-results-header">
                <h3>Found ${totalResults} results</h3>
            </div>
            ${guides.length > 0 ? `
                <div class="search-results-section">
                    <h4>Guide Sections (${guides.length})</h4>
                    <div class="search-results-list">
                        ${guides.slice(0, 5).map(guide => `
                            <a href="#${guide.id}" class="search-result-item">
                                <span class="search-result-type">📖</span>
                                <div class="search-result-content">
                                    <div class="search-result-title">${guide.title}</div>
                                    <div class="search-result-excerpt">${guide.excerpt}</div>
                                </div>
                            </a>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            ${articles.length > 0 ? `
                <div class="search-results-section">
                    <h4>Articles (${articles.length})</h4>
                    <div class="search-results-list">
                        ${articles.slice(0, 10).map(article => `
                            <a href="${article.link}" target="_blank" class="search-result-item">
                                <span class="search-result-type">${article.feedIcon}</span>
                                <div class="search-result-content">
                                    <div class="search-result-title">${article.title}</div>
                                    <div class="search-result-meta">${article.feedName} · ${this.formatDate(article.pubDate)}</div>
                                </div>
                            </a>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    }

    /**
     * Format date for display
     */
    formatDate(date) {
        if (!date || date.getTime() === 0) return 'Unknown date';
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    }

    /**
     * Clear search results
     */
    clearResults() {
        if (this.resultsContainer) {
            this.resultsContainer.innerHTML = '';
        }
    }

    /**
     * Clear search
     */
    clearSearch() {
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        this.clearResults();
        AppState.searchQuery = '';
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

const Utils = {
    /**
     * Format relative time
     * @param {Date} date - Date to format
     * @returns {string} - Relative time string
     */
    formatRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
        if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        return 'Just now';
    },

    /**
     * Debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function} - Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function
     * @param {Function} func - Function to throttle
     * @param {number} limit - Time limit in ms
     * @returns {Function} - Throttled function
     */
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func(...args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Copy text to clipboard
     * @param {string} text - Text to copy
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Failed to copy:', err);
            return false;
        }
    },

    /**
     * Generate unique ID
     * @returns {string} - Unique ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    /**
     * Escape HTML entities
     * @param {string} text - Text to escape
     * @returns {string} - Escaped text
     */
    escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// ============================================
// NAVIGATION SYSTEM
// ============================================

class NavigationSystem {
    constructor() {
        this.sidebar = null;
        this.mobileMenuBtn = null;
    }

    /**
     * Initialize navigation
     */
    init() {
        this.sidebar = document.querySelector('.sidebar');
        this.mobileMenuBtn = document.querySelector('.mobile-menu-btn');

        // Mobile menu toggle
        if (this.mobileMenuBtn) {
            this.mobileMenuBtn.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }

        // Close sidebar on navigation (mobile)
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                if (window.innerWidth <= 1024) {
                    this.closeSidebar();
                }
            });
        });

        // Handle resize
        window.addEventListener('resize', Utils.debounce(() => {
            if (window.innerWidth > 1024) {
                this.openSidebar();
            }
        }, 250));
    }

    toggleSidebar() {
        this.sidebar?.classList.toggle('open');
    }

    openSidebar() {
        this.sidebar?.classList.add('open');
    }

    closeSidebar() {
        this.sidebar?.classList.remove('open');
    }
}

// ============================================
// MAIN APPLICATION
// ============================================

class ResearchAggregator {
    constructor() {
        this.rssAggregator = new RSSAggregator();
        this.glossary = new GlossarySystem();
        this.contentLength = new ContentLengthManager();
        this.guideIndex = new GuideIndexSystem();
        this.search = new SearchSystem(this.rssAggregator);
        this.navigation = new NavigationSystem();
    }

    /**
     * Initialize the application
     */
    async init() {
        console.log('🚀 Research Aggregator initializing...');

        // Initialize all systems
        this.glossary.init();
        this.contentLength.init();
        this.guideIndex.init();
        this.search.init();
        this.navigation.init();

        // Load portal-specific configuration
        const portal = document.body.dataset.portal;
        if (portal) {
            await this.loadPortalConfig(portal);
        }

        console.log('✅ Research Aggregator ready!');
    }

    /**
     * Load portal-specific configuration
     * @param {string} portalId - Portal identifier
     */
    async loadPortalConfig(portalId) {
        try {
            // Load feeds configuration
            const feedsResponse = await fetch(`../data/feeds-${portalId}.json`);
            if (feedsResponse.ok) {
                const feedsConfig = await feedsResponse.json();
                feedsConfig.feeds.forEach(feed => {
                    this.rssAggregator.addFeed(feed.id, feed);
                });
            }

            // Load glossary
            const glossaryResponse = await fetch(`../data/glossary-${portalId}.json`);
            if (glossaryResponse.ok) {
                const glossaryConfig = await glossaryResponse.json();
                this.glossary.addTerms(glossaryConfig.terms);
            }

            // Fetch initial feeds
            await this.refreshFeeds();

        } catch (error) {
            console.error('Error loading portal config:', error);
        }
    }

    /**
     * Refresh all RSS feeds
     */
    async refreshFeeds() {
        const feedContainer = document.querySelector('.rss-feed-list');
        if (!feedContainer) return;

        feedContainer.innerHTML = '<div class="loading"><div class="loading-spinner"></div><p class="loading-text">Loading feeds...</p></div>';

        try {
            const feeds = Array.from(this.rssAggregator.feeds.values());
            const allArticles = [];

            for (const feed of feeds) {
                try {
                    const articles = await this.rssAggregator.fetchFeed(feed.id);
                    allArticles.push(...articles);
                } catch (err) {
                    console.warn(`Failed to fetch ${feed.id}:`, err);
                }
            }

            // Sort by date and display
            allArticles.sort((a, b) => b.pubDate - a.pubDate);
            this.displayArticles(allArticles.slice(0, 20), feedContainer);

        } catch (error) {
            feedContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">❌</div>
                    <h4 class="empty-state-title">Failed to load feeds</h4>
                    <p class="empty-state-description">${error.message}</p>
                </div>
            `;
        }
    }

    /**
     * Display articles in container
     * @param {Array} articles - Articles to display
     * @param {HTMLElement} container - Container element
     */
    displayArticles(articles, container) {
        if (articles.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <h4 class="empty-state-title">No articles found</h4>
                    <p class="empty-state-description">Check back later for new content</p>
                </div>
            `;
            return;
        }

        container.innerHTML = articles.map(article => `
            <article class="rss-article">
                ${article.thumbnail ? `<img src="${article.thumbnail}" alt="" class="rss-article-image" loading="lazy">` : ''}
                <div class="rss-article-content">
                    <div class="rss-article-source">
                        <span>${article.feedIcon}</span>
                        <span>${article.feedName}</span>
                    </div>
                    <h3 class="rss-article-title">
                        <a href="${article.link}" target="_blank" rel="noopener">${Utils.escapeHTML(article.title)}</a>
                    </h3>
                    <p class="rss-article-excerpt">${Utils.escapeHTML(article.description)}</p>
                    <div class="rss-article-footer">
                        <span class="rss-article-date">${Utils.formatRelativeTime(article.pubDate)}</span>
                        <div class="rss-article-tags">
                            ${article.categories.slice(0, 3).map(cat => `<span class="rss-tag">${Utils.escapeHTML(cat)}</span>`).join('')}
                        </div>
                    </div>
                </div>
            </article>
        `).join('');
    }
}

// ============================================
// INITIALIZE ON DOM READY
// ============================================

let app;

document.addEventListener('DOMContentLoaded', () => {
    app = new ResearchAggregator();
    app.init();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ResearchAggregator,
        RSSAggregator,
        GlossarySystem,
        ContentLengthManager,
        GuideIndexSystem,
        SearchSystem,
        Utils
    };
}
