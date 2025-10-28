// WebSocket connection
let ws = null;
let reconnectInterval = null;

// Connect to WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket connected');
        updateConnectionStatus(true);
        
        // Clear reconnect interval if it exists
        if (reconnectInterval) {
            clearInterval(reconnectInterval);
            reconnectInterval = null;
        }
        
        // Send ping every 30 seconds to keep connection alive
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
        
        // Attempt to reconnect every 5 seconds
        if (!reconnectInterval) {
            reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                connectWebSocket();
            }, 5000);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'initial_data':
            updateStats(data.stats);
            renderTasks(data.tasks);
            break;
        case 'task_update':
            updateStats(data.stats);
            updateTask(data.task);
            break;
        case 'stats_update':
            updateStats(data.stats);
            break;
    }
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const indicator = document.getElementById('connection-indicator');
    const text = document.getElementById('connection-text');
    
    if (connected) {
        indicator.classList.remove('disconnected');
        indicator.classList.add('connected');
        text.textContent = 'Connected';
    } else {
        indicator.classList.remove('connected');
        indicator.classList.add('disconnected');
        text.textContent = 'Disconnected';
    }
}

// Update statistics
function updateStats(stats) {
    document.getElementById('stat-total').textContent = stats.total_tasks;
    document.getElementById('stat-pending').textContent = stats.pending;
    document.getElementById('stat-processing').textContent = stats.processing;
    document.getElementById('stat-completed').textContent = stats.completed;
    document.getElementById('stat-failed').textContent = stats.failed;
    document.getElementById('stat-retrying').textContent = stats.retrying;
}

// Render all tasks
function renderTasks(tasks) {
    const tasksList = document.getElementById('tasks-list');
    tasksList.innerHTML = '';
    
    if (tasks.length === 0) {
        tasksList.innerHTML = '<p style="text-align: center; color: #9ca3af; padding: 2rem;">No tasks yet. Create one to get started!</p>';
        return;
    }
    
    tasks.forEach(task => {
        const taskCard = createTaskCard(task);
        tasksList.appendChild(taskCard);
    });
}

// Update a single task
function updateTask(task) {
    const existingCard = document.querySelector(`[data-task-id="${task.task_id}"]`);
    
    if (existingCard) {
        const newCard = createTaskCard(task);
        existingCard.replaceWith(newCard);
        
        // Scroll into view if processing
        if (task.status === 'processing') {
            newCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    } else {
        // New task, add to top of list
        const tasksList = document.getElementById('tasks-list');
        const newCard = createTaskCard(task);
        tasksList.insertBefore(newCard, tasksList.firstChild);
    }
}

// Create task card element
function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = `task-card ${task.status}`;
    card.setAttribute('data-task-id', task.task_id);
    
    const createdAt = new Date(task.created_at).toLocaleString();
    const taskType = task.task_type.replace('_', ' ').toUpperCase();
    
    card.innerHTML = `
        <div class="task-header">
            <div class="task-info">
                <div class="task-name">${escapeHtml(task.name)}</div>
                <div class="task-id">${task.task_id}</div>
            </div>
            <span class="task-status ${task.status}">${task.status}</span>
        </div>
        <div class="task-details">
            <div class="task-detail">
                <span class="task-detail-label">Type</span>
                <span class="task-detail-value">${taskType}</span>
            </div>
            <div class="task-detail">
                <span class="task-detail-label">Priority</span>
                <span class="task-detail-value">${task.priority}</span>
            </div>
            <div class="task-detail">
                <span class="task-detail-label">Created</span>
                <span class="task-detail-value">${createdAt}</span>
            </div>
            <div class="task-detail">
                <span class="task-detail-label">Retries</span>
                <span class="task-detail-value">${task.retry_count}</span>
            </div>
        </div>
        ${task.status === 'processing' || task.status === 'retrying' ? `
            <div class="task-progress">
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: ${task.progress}%"></div>
                </div>
                <div class="progress-text">${task.progress}% complete</div>
            </div>
        ` : ''}
        ${task.error ? `
            <div class="task-error">
                <strong>Error:</strong> ${escapeHtml(task.error)}
            </div>
        ` : ''}
    `;
    
    return card;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Create task form submission
document.getElementById('create-task-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('task-name').value,
        task_type: document.getElementById('task-type').value,
        priority: parseInt(document.getElementById('task-priority').value),
        payload: {}
    };
    
    // Parse payload JSON
    const payloadText = document.getElementById('task-payload').value.trim();
    if (payloadText) {
        try {
            formData.payload = JSON.parse(payloadText);
        } catch (error) {
            alert('Invalid JSON in payload field');
            return;
        }
    }
    
    try {
        const response = await fetch('/api/tasks/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const task = await response.json();
            console.log('Task created:', task);
            
            // Reset form
            document.getElementById('create-task-form').reset();
            document.getElementById('task-payload').value = '{}';
            
            // Show success feedback
            showNotification('Task created successfully!', 'success');
        } else {
            const error = await response.json();
            alert(`Failed to create task: ${error.detail}`);
        }
    } catch (error) {
        console.error('Error creating task:', error);
        alert('Failed to create task. Please try again.');
    }
});

// Refresh button
document.getElementById('refresh-btn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/tasks/');
        if (response.ok) {
            const tasks = await response.json();
            renderTasks(tasks);
            
            // Also refresh stats
            const statsResponse = await fetch('/api/tasks/stats/overview');
            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                updateStats(stats);
            }
            
            showNotification('Refreshed successfully!', 'success');
        }
    } catch (error) {
        console.error('Error refreshing tasks:', error);
        showNotification('Failed to refresh tasks', 'error');
    }
});

// Show notification
function showNotification(message, type = 'success') {
    // Simple notification - you can enhance this with a better UI
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize WebSocket connection on page load
connectWebSocket();

