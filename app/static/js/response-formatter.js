/**
 * Enhanced Response Formatter for Al-Huda
 * Adds advanced formatting features for better AI response presentation
 */

// ============================================================================
// KEY TAKEAWAY SECTION
// ============================================================================

function createKeyTakeaway(title, items) {
    let itemsHTML = items.map(item => 
        `<div class="key-takeaway-item">${escapeHtml(item)}</div>`
    ).join('\n');

    return `
<div class="key-takeaway">
    <div class="key-takeaway-title">
        <span class="material-symbols-outlined">lightbulb</span>
        ${escapeHtml(title)}
    </div>
    <div class="key-takeaway-content">
        ${itemsHTML}
    </div>
</div>`;
}

// ============================================================================
// CALLOUT BOXES
// ============================================================================

function createCallout(type, content) {
    const calloutTypes = {
        info: { class: 'callout-info', icon: 'info', title: 'Note' },
        success: { class: 'callout-success', icon: 'check_circle', title: 'Key Point' },
        warning: { class: 'callout-warning', icon: 'warning', title: 'Important' },
        concept: { class: 'callout-concept', icon: 'auto_awesome', title: 'Concept' }
    };

    const config = calloutTypes[type] || calloutTypes.info;

    return `
<div class="${config.class}">
    <div class="callout-icon">
        <span class="material-symbols-outlined">${config.icon}</span>
        ${config.title}
    </div>
    ${formatInlineText(content)}
</div>`;
}

// ============================================================================
// DEFINITION BOX
// ============================================================================

function createDefinition(term, definition) {
    return `
<div class="definition-box">
    <div class="definition-term">${escapeHtml(term)}</div>
    <div class="definition-text">${formatInlineText(definition)}</div>
</div>`;
}

// ============================================================================
// SIDE NOTE
// ============================================================================

function createSideNote(content) {
    return `<div class="side-note">💡 ${formatInlineText(content)}</div>`;
}

// ============================================================================
// PROCESS/STEP FORMAT
// ============================================================================

function createProcessStep(number, title, description) {
    return `
<div class="process-step">
    <div class="process-number">${number}</div>
    <div class="process-content">
        <div class="process-title">${escapeHtml(title)}</div>
        <div class="process-description">${formatInlineText(description)}</div>
    </div>
</div>`;
}

// ============================================================================
// COMPARISON CARDS
// ============================================================================

function createComparisonCards(items) {
    const cardsHTML = items.map(item => `
<div class="comparison-item">
    <div class="comparison-label">${escapeHtml(item.label)}</div>
    <div class="comparison-value">${formatInlineText(item.value)}</div>
</div>`).join('\n');

    return `<div class="comparison-card">${cardsHTML}</div>`;
}

// ============================================================================
// INSPIRATION QUOTE
// ============================================================================

function createInspirationQuote(quote, source = null) {
    return `
<div class="inspiration-quote">
    ${formatInlineText(quote)}
    ${source ? `<div style="margin-top: 10px; font-size: 0.95em; opacity: 0.8;">— ${escapeHtml(source)}</div>` : ''}
</div>`;
}

// ============================================================================
// RESPONSE HEADER
// ============================================================================

function createResponseHeader(text, icon = 'smart_toy') {
    return `
<div class="message-response-header">
    <span class="material-symbols-outlined">${icon}</span>
    <span>${escapeHtml(text)}</span>
</div>`;
}

// ============================================================================
// RESPONSE CONTAINER
// ============================================================================

function createResponseContainer(content) {
    return `<div class="message-response-container">${content}</div>`;
}

// ============================================================================
// ISLAMIC TERM MARKUP
// ============================================================================

function markIslamicTerms(text) {
    // List of common Islamic terms to highlight
    const islamicTerms = [
        'Allah', 'Prophet', 'Sunnah', 'Hadith', 'Quran', 'Sha\'riah', 'Ijma\'',
        'Qiyas', 'Ijtihad', 'Fatwa', 'Tafsir', 'Ulama', 'Sahaba', 'Khalifah',
        'Ummah', 'Dakwah', 'Hijab', 'Salah', 'Zakat', 'Hajj', 'Wudu',
        'Tawhid', 'Ihsan', 'Taqwa', 'Ummah', 'Salam'
    ];

    let result = text;
    islamicTerms.forEach(term => {
        const regex = new RegExp(`\\b(${term})\\b`, 'g');
        result = result.replace(regex, '<span class="islamic-term">$1</span>');
    });

    return result;
}

// ============================================================================
// CITATIONS/SOURCES
// ============================================================================

function createCitationList(sources) {
    if (!sources || sources.length === 0) return '';

    const citationsHTML = sources.map((source, index) => `
<div class="citation-item">
    <div class="citation-number">${index + 1}</div>
    <div class="citation-content">
        <strong>${escapeHtml(source.title || 'Source')}</strong>
        ${source.description ? `<div>${escapeHtml(source.description)}</div>` : ''}
    </div>
</div>`).join('\n');

    return `
<div style="margin-top: 24px;">
    <div style="font-weight: 700; font-size: 14px; color: #059669; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <span class="material-symbols-outlined">sources</span>
        Sources & References
    </div>
    <div class="citation-list">${citationsHTML}</div>
</div>`;
}

// ============================================================================
// RESPONSE METADATA
// ============================================================================

function createResponseMetadata(metadata) {
    if (!metadata) return '';

    const tags = [];
    if (metadata.language) tags.push(`<span class="metadata-tag"><span class="material-symbols-outlined">translate</span> ${metadata.language}</span>`);
    if (metadata.difficulty) tags.push(`<span class="metadata-tag"><span class="material-symbols-outlined">grade</span> ${metadata.difficulty}</span>`);
    if (metadata.topic) tags.push(`<span class="metadata-tag"><span class="material-symbols-outlined">label</span> ${metadata.topic}</span>`);

    if (tags.length === 0) return '';

    return `<div class="response-metadata">${tags.join('')}</div>`;
}

// ============================================================================
// EXPORT FUNCTIONS FOR GLOBAL USE
// ============================================================================

window.ResponseFormatter = {
    createKeyTakeaway,
    createCallout,
    createDefinition,
    createSideNote,
    createProcessStep,
    createComparisonCards,
    createInspirationQuote,
    createResponseHeader,
    createResponseContainer,
    markIslamicTerms,
    createCitationList,
    createResponseMetadata
};
