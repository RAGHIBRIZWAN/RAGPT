// script.js (Corrected for Google Gemini Backend)

document.addEventListener('DOMContentLoaded', () => {
    // Clear history button
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete all your recipe history?')) {
                recipeHistory = [];
                localStorage.removeItem('recipeHistory');
                renderHistory();
            }
        });
    }
    // Sidebar/history elements
    const historySidebar = document.getElementById('history-sidebar');
    const historyList = document.getElementById('history-list');
    const toggleHistoryBtn = document.getElementById('toggle-history');
    const mainContent = document.getElementById('main-content');

    // Load history from localStorage
    let recipeHistory = JSON.parse(localStorage.getItem('recipeHistory') || '[]');
    renderHistory();

    toggleHistoryBtn.addEventListener('click', () => {
        if (historySidebar.style.display === 'flex') {
            historySidebar.style.display = 'none';
            mainContent.style.marginLeft = '0';
            toggleHistoryBtn.style.left = '10px';
        } else {
            historySidebar.style.display = 'flex';
            mainContent.style.marginLeft = '270px';
            toggleHistoryBtn.style.left = '280px';
        }
    });
    const generateBtn = document.getElementById('generate-btn');
    const ingredientsInput = document.getElementById('ingredients-input');
    const loader = document.getElementById('loader');
    const recipeOutput = document.getElementById('recipe-output');
    const errorMessage = document.getElementById('error-message');

    const API_ENDPOINT = 'http://127.0.0.1:8000/generate-recipe';

    generateBtn.addEventListener('click', handleRecipeGeneration);
    
    ingredientsInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleRecipeGeneration();
        }
    });

    async function handleRecipeGeneration() {
        const ingredients = ingredientsInput.value.trim();
        if (!ingredients) {
            showError("Please enter some ingredients.");
            return;
        }
        
        loader.style.display = 'flex';
        recipeOutput.style.display = 'none';
        errorMessage.style.display = 'none';

        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ingredients: ingredients }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Something went wrong on the server.');
            }

            const data = await response.json();
            
            // This is the required change: We must parse the string from the backend
            const recipeData = JSON.parse(data.recipe);
            
            displayRecipe(recipeData);
            addToHistory(recipeData);

        } catch (error) {
            console.error('Error:', error);
            showError(error.message);
        } finally {
            loader.style.display = 'none';
        }
    }

    function displayRecipe(recipe) {
        const recipeNameEl = document.getElementById('recipe-name');
        const recipeDescriptionEl = document.getElementById('recipe-description');
        const ingredientsListEl = document.getElementById('ingredients-list');
        const instructionsListEl = document.getElementById('instructions-list');

        ingredientsListEl.innerHTML = '';
        instructionsListEl.innerHTML = '';

        recipeNameEl.textContent = recipe.recipe_name;
        recipe.ingredients.forEach(ingredient => {
            const li = document.createElement('li');
            // If ingredient is an object, try to display its name or stringify it
            if (typeof ingredient === 'object' && ingredient !== null) {
                li.textContent = ingredient.name || JSON.stringify(ingredient);
            } else {
                li.textContent = ingredient;
            }
            ingredientsListEl.appendChild(li);
        });

        recipe.instructions.forEach(instruction => {
            const li = document.createElement('li');
            li.textContent = instruction;
            instructionsListEl.appendChild(li);
        });
        
        recipeOutput.style.display = 'block';
    }

    // Add recipe to history and update sidebar
    function addToHistory(recipe) {
        // Avoid duplicates by recipe name
        if (recipeHistory.some(r => r.recipe_name === recipe.recipe_name)) return;
        recipeHistory.unshift({
            recipe_name: recipe.recipe_name,
            description: recipe.description,
            ingredients: recipe.ingredients,
            instructions: recipe.instructions
        });
        // Limit history to 20
        if (recipeHistory.length > 20) recipeHistory = recipeHistory.slice(0, 20);
        localStorage.setItem('recipeHistory', JSON.stringify(recipeHistory));
        renderHistory();
    }

    // Render the sidebar history
    function renderHistory() {
        historyList.innerHTML = '';
        if (recipeHistory.length === 0) {
            const li = document.createElement('li');
            li.textContent = 'No recipes yet.';
            li.style.color = '#6b7280';
            li.style.textAlign = 'center';
            li.style.marginTop = '2.5rem';
            historyList.appendChild(li);
            return;
        }
        recipeHistory.forEach((recipe, idx) => {
            const li = document.createElement('li');
            li.className = 'history-item';
            li.style.position = 'relative';
            li.innerHTML = `
                <span class="dish-icon" aria-hidden="true">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="17" rx="7" ry="3.5" fill="#101418"/><path d="M5 17V7a7 7 0 0 1 14 0v10"/><path d="M12 12v2"/><circle cx="12" cy="9.5" r="1.2" fill="#22c55e"/></svg>
                </span>
                <span class="history-item-title">${recipe.recipe_name}</span>
                <div class="history-item-desc">${recipe.description.slice(0, 60)}${recipe.description.length > 60 ? '...' : ''}</div>
                <button class="delete-history-btn" title="Delete this recipe" style="position:absolute;bottom:10px;right:10px;background:#101418;color:#22c55e;border:1.5px solid #22c55e;border-radius:0.4em;padding:0.08em 0.5em;font-size:1.1em;cursor:pointer;box-shadow:0 1px 4px #22c55e33;transition:background 0.18s;line-height:1;">&times;</button>
            `;
            // Show recipe on click, but not when clicking delete
            li.onclick = (e) => {
                if (e.target.classList.contains('delete-history-btn')) return;
                displayRecipe(recipe);
            };
            // Delete button logic
            li.querySelector('.delete-history-btn').onclick = (e) => {
                e.stopPropagation();
                if (confirm(`Delete "${recipe.recipe_name}" from history?`)) {
                    recipeHistory.splice(idx, 1);
                    localStorage.setItem('recipeHistory', JSON.stringify(recipeHistory));
                    renderHistory();
                }
            };
            historyList.appendChild(li);
        });
    }
    
    function showError(message) {
        const errorContent = errorMessage.querySelector('p');
        errorContent.textContent = message;
        errorMessage.style.display = 'block';
    }
});