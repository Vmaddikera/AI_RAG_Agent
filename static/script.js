// Frontend JavaScript for Course Assistant

const questionForm = document.getElementById('questionForm');
const questionInput = document.getElementById('question');
const submitBtn = document.getElementById('submitBtn');
const resultsSection = document.getElementById('resultsSection');
const loadingState = document.getElementById('loadingState');
const answerOutput = document.getElementById('answerOutput');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');
const questionAsked = document.getElementById('questionAsked');
const closeResults = document.getElementById('closeResults');

// API endpoint
const API_URL = '/api/query';

// Handle form submission
questionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const question = questionInput.value.trim();
    
    if (!question) {
        alert('Please enter a question');
        return;
    }
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Show question asked
    questionAsked.innerHTML = `
        <div class="question-display">
            <strong>Your Question:</strong>
            <p>${escapeHtml(question)}</p>
        </div>
    `;
    
    // Show loading, hide answer and error
    loadingState.style.display = 'block';
    answerOutput.innerHTML = '';
    errorState.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    try {
        // Make API call
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Display answer
            displayAnswer(data.answer);
        } else {
            const errorMsg = data.error || 'Failed to get answer';
            throw new Error(errorMsg);
        }
        
    } catch (error) {
        showError(error.message || 'Failed to connect to server. Please try again.');
    } finally {
        loadingState.style.display = 'none';
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Ask Question';
    }
});

// Display answer with proper formatting
function displayAnswer(answerText) {
    let html = '<div class="answer-container">';
    
    // Split into lines for processing
    const lines = answerText.split('\n');
    
    let currentSection = '';
    let inCodeBlock = false;
    
    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        const trimmedLine = line.trim();
        
        // Skip empty lines
        if (!trimmedLine && !inCodeBlock) {
            continue;
        }
        
        // Handle code blocks
        if (trimmedLine.startsWith('```')) {
            inCodeBlock = !inCodeBlock;
            continue;
        }
        
        if (inCodeBlock) {
            html += `<div class="code-line">${escapeHtml(line)}</div>`;
            continue;
        }
        
        // Detect section headers
        if (trimmedLine.match(/^#{1,3}\s+/) || (trimmedLine.length > 0 && trimmedLine.length < 50 && trimmedLine.match(/^[A-Z][A-Z\s]+$/))) {
            // Close previous section
            if (currentSection) {
                html += '</div>';
            }
            
            // Create new section
            const headerText = trimmedLine.replace(/^#{1,3}\s+/, '').replace(/^\*\*|\*\*$/g, '');
            currentSection = headerText;
            
            const level = trimmedLine.match(/^#+/)?.[0]?.length || 2;
            html += `<div class="answer-section">
                <h${Math.min(level, 3)} class="section-header">
                    ${formatText(headerText)}
                </h${Math.min(level, 3)}>
                <div class="section-content">`;
            continue;
        }
        
        // Lists
        if (trimmedLine.match(/^[-*•]\s+/) || trimmedLine.match(/^\d+\.\s+/)) {
            if (!currentSection) {
                html += '<div class="answer-section"><div class="section-content">';
                currentSection = 'content';
            }
            
            const listItem = trimmedLine.replace(/^[-*•\d.\s]+/, '');
            const icon = '<i class="fas fa-circle"></i>';
            html += `<div class="list-item">${icon} ${formatText(listItem)}</div>`;
            continue;
        }
        
        // Bold text (markdown style)
        if (trimmedLine.includes('**')) {
            if (!currentSection) {
                html += '<div class="answer-section"><div class="section-content">';
                currentSection = 'content';
            }
            html += `<p class="answer-paragraph bold-text">${formatText(trimmedLine)}</p>`;
            continue;
        }
        
        // Regular paragraphs
        if (trimmedLine.length > 0) {
            if (!currentSection) {
                html += '<div class="answer-section"><div class="section-content">';
                currentSection = 'content';
            }
            
            html += `<p class="answer-paragraph">${formatText(trimmedLine)}</p>`;
        }
    }
    
    // Close last section
    if (currentSection) {
        html += '</div></div>';
    }
    
    html += '</div>';
    answerOutput.innerHTML = html;
    answerOutput.scrollTop = 0;
}

// Format text (highlight numbers, stats, etc.)
function formatText(text) {
    // Escape HTML first
    text = escapeHtml(text);
    
    // Format bold text (**text**)
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    
    // Highlight course names and skills
    text = text.replace(/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Course|Specialization|Certificate|Program|Track))\b/g, 
        '<span class="player-name">$1</span>');
    
    // Highlight percentages
    text = text.replace(/([\d.]+%)/g, '<span class="percentage-value">$1</span>');
    
    // Highlight skills (comma-separated skills)
    text = text.replace(/\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b(?=\s*[,;])/g, 
        '<span class="stat-value">$1</span>');
    
    // Highlight years
    text = text.replace(/\b(20\d{2})\b/g, '<span class="season-value">$1</span>');
    
    return text;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show error
function showError(message) {
    errorMessage.textContent = message;
    errorState.style.display = 'block';
}

// Close results
closeResults.addEventListener('click', () => {
    resultsSection.style.display = 'none';
});

