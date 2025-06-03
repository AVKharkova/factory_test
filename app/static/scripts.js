const API_BASE_URL = '';

const entityCache = {
    factories: [],
    sections: [],
    equipment: []
};

function displayResponse(elementId, data, isError = false) {
    const responseEl = document.getElementById(elementId);
    if (!responseEl) return;
    const content = data ? JSON.stringify(data, null, 2) : (isError ? 'Произошла ошибка' : 'Успешно');
    responseEl.innerHTML = `<pre class="${isError ? 'error' : 'success'}">${content}</pre>`;
}

async function callApi(url, method, body = null, responseElementId = null) {
    const responseDisplay = responseElementId ? document.getElementById(responseElementId) : null;
    if (responseDisplay) responseDisplay.innerHTML = '<p>Загрузка...</p>';

    try {
        const fetchOptions = {
            method: method,
            headers: { 'Accept': 'application/json' },
        };
        if (body !== null && (method === 'POST' || method === 'PUT')) {
            fetchOptions.headers['Content-Type'] = 'application/json';
            fetchOptions.body = JSON.stringify(body);
        }

        const response = await fetch(url, fetchOptions);
        let responseData;
        if (response.status === 204) { 
            responseData = { detail: "Операция выполнена успешно" };
        } else {
            responseData = await response.json();
        }
        
        if (!response.ok) {
            throw { status: response.status, data: responseData };
        }
        if (responseDisplay) displayResponse(responseElementId, responseData);
        return responseData;
    } catch (error) {
        console.error('API Error:', error);
        if (responseDisplay) displayResponse(responseElementId, error.data || { detail: error.message || "Неизвестная ошибка" }, true);
        throw error;
    }
}

async function populateSelect(selectElementId, entityType, includeInactive = false, prompt = "Выберите...") {
    const selectEl = document.getElementById(selectElementId);
    if (!selectEl) return;
    
    const currentVal = selectEl.value; 
    selectEl.innerHTML = `<option value="">${prompt}</option>`; 
    
    try {
        let items = entityCache[entityType];
        let needsFetch = !items || items.length === 0;
        if (items && items.length > 0 && includeInactive && !items.some(it => !it.is_active)) {
            needsFetch = true;
        }
        if (items && items.length > 0 && !includeInactive && items.some(it => !it.is_active)) {
            needsFetch = true;
        }

        if (needsFetch) {
            console.log(`Populating select ${selectElementId} for ${entityType} from API (includeInactive: ${includeInactive})`);
            items = await callApi(`${API_BASE_URL}/${entityType}/?limit=1000&include_inactive=${includeInactive}`, 'GET');
            entityCache[entityType] = items ? (includeInactive ? items : items.filter(it => it.is_active)) : [];
        } else {
            console.log(`Populating select ${selectElementId} for ${entityType} from CACHE (includeInactive: ${includeInactive})`);
            items = includeInactive ? entityCache[entityType] : entityCache[entityType].filter(it => it.is_active);
        }
        
        if (items) {
            items.forEach(item => {
                if (item.is_active || includeInactive) {
                    const option = document.createElement('option');
                    option.value = item.id;
                    option.textContent = `${item.name} (ID: ${item.id})${item.is_active ? '' : ' - неактив.'}`;
                    if (!item.is_active) {
                        option.classList.add('inactive-option-item');
                    }
                    selectEl.appendChild(option);
                }
            });
        }
        if (currentVal) selectEl.value = currentVal; 
    } catch (error) {
        console.error(`Error populating select ${selectElementId}:`, error);
        const option = document.createElement('option');
        option.value = "";
        option.textContent = "Ошибка загрузки";
        option.disabled = true;
        selectEl.appendChild(option);
    }
}

async function handleDataFormSubmit(event, method, entityType, responseElementId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const dataForPost = {}; 
    let entityId = null;

    formData.forEach((value, key) => {
        if (key === 'id') {
            entityId = value;
            return;
        }

        let parsedValue;
        if (form.elements[key] && form.elements[key].multiple) {
            parsedValue = formData.getAll(key).map(id => parseInt(id.trim())).filter(id => !isNaN(id));
        } else if (key.endsWith('_id') && value === "" && form.elements[key] && form.elements[key].tagName === 'SELECT' ) {
            if (method === 'POST' && form.elements[key].required) {
                parsedValue = null; 
            } else {
                parsedValue = undefined;
            }
        } else if (form.elements[key] && form.elements[key].type === 'number' && value !== '') {
            parsedValue = parseFloat(value);
        } else {
            parsedValue = value;
        }
        
        if (method === 'POST' && parsedValue !== undefined) {
            dataForPost[key] = parsedValue;
        }
    });
    
    const body = dataForPost;
    console.log(`Submitting ${method} for ${entityType} with ID ${entityId}. Body:`, JSON.stringify(body));
    const url = entityId ? `${API_BASE_URL}/${entityType}/${entityId}` : `${API_BASE_URL}/${entityType}/`;

    try {
        await callApi(url, method, body, responseElementId);
        if (method === 'POST' && form.classList.contains('create-form')) {
            form.reset();
            if (entityType === 'sections') {
                populateSelect('factory_id_section_create_select', 'factories', false, 'Выберите фабрику');
                populateSelect('equipment_ids_section_create_select', 'equipment', false, 'Выберите оборудование');
            } else if (entityType === 'equipment') {
                populateSelect('section_ids_equipment_create_select', 'sections', false, 'Выберите участки');
            }
        }

        const includeInactiveCheckbox = document.getElementById(`includeInactive${entityType.charAt(0).toUpperCase() + entityType.slice(1)}`);
        const shouldIncludeInactive = includeInactiveCheckbox ? includeInactiveCheckbox.checked : false;
        loadEntityList(entityType, shouldIncludeInactive); 
    } catch (error) {
    }
}

async function loadEntityList(entityType, includeInactive = false) {
    const listElId = `${entityType}List`;
    const listEl = document.getElementById(listElId);
    if (!listEl) return;
    listEl.innerHTML = '<li>Загрузка...</li>';
    try {
        if (typeof callApi !== 'function') {
            console.error('callApi is not defined when loadEntityList is called for', entityType);
            listEl.innerHTML = '<li><span class="error">Ошибка: функция callApi не определена.</span></li>';
            return;
        }
        const apiUrl = `${API_BASE_URL}/${entityType}/?limit=1000&include_inactive=${includeInactive}`;
        const itemsToDisplay = await callApi(apiUrl, 'GET');

        if (!entityCache[entityType] || entityCache[entityType].length === 0 || includeInactive) {
            const allItemsForCache = await callApi(`${API_BASE_URL}/${entityType}/?limit=1000&include_inactive=true`, 'GET');
            entityCache[entityType] = allItemsForCache || [];
        }

        listEl.innerHTML = ''; 
        if (itemsToDisplay && itemsToDisplay.length > 0) {
            itemsToDisplay.forEach(item => {
                const li = document.createElement('li');
                li.className = item.is_active ? '' : 'inactive-item';
                let itemDetails = '';
                if (entityType === 'sections') {
                    itemDetails = `(Ф-ID: ${item.factory_id || 'N/A'})`;
                    if (item.equipment && Array.isArray(item.equipment) && item.equipment.length > 0) {
                        itemDetails += `<br><small>Оборудование: ${item.equipment.map(eq => eq.name).join(', ')}</small>`;
                    }
                } else if (entityType === 'equipment') {
                    if (item.description) itemDetails += `<br><small>Описание: ${item.description}</small>`;
                    if (item.sections && Array.isArray(item.sections) && item.sections.length > 0) {
                         itemDetails += `<br><small>Участки: ${item.sections.map(s => s.name).join(', ')}</small>`;
                    }
                }

                li.innerHTML = `
                    <div class="item-info">
                        ID: ${item.id} - <strong>${item.name}</strong>
                        ${itemDetails}
                    </div>
                    <div class="item-actions">
                        ${item.is_active 
                            ? `<button class="action-btn delete" onclick="deactivateEntity('${entityType}', ${item.id})">Деакт.</button>`
                            : `<button class="action-btn activate" onclick="activateEntity('${entityType}', ${item.id})">Актив.</button>`
                        }
                    </div>
                `;
                listEl.appendChild(li);
            });
        } else {
            listEl.innerHTML = '<li>Нет данных для отображения.</li>';
        }
    } catch (error) {
        listEl.innerHTML = `<li><span class="error">Ошибка загрузки списка: ${error.data?.detail || error.message}</span></li>`;
    }
}

async function deactivateEntity(entityType, id) {
    if (!confirm(`Вы уверены, что хотите деактивировать ${entityType} с ID ${id}?`)) return;
    const responseElementId = `${entityType}Response`;
    try {
        await callApi(`${API_BASE_URL}/${entityType}/${id}`, 'DELETE', null, responseElementId);
        const includeInactiveCheckbox = document.getElementById(`includeInactive${entityType.charAt(0).toUpperCase() + entityType.slice(1)}`);
        loadEntityList(entityType, includeInactiveCheckbox ? includeInactiveCheckbox.checked : false);
    } catch (error) {/* error handled by callApi */}
}

async function activateEntity(entityType, id) {
    const responseElementId = `${entityType}Response`;
    try {
        await callApi(`${API_BASE_URL}/${entityType}/${id}/activate`, 'PUT', null, responseElementId);
        const includeInactiveCheckbox = document.getElementById(`includeInactive${entityType.charAt(0).toUpperCase() + entityType.slice(1)}`);
        loadEntityList(entityType, includeInactiveCheckbox ? includeInactiveCheckbox.checked : false);
    } catch (error) {/* error handled by callApi */}
}

async function submitHierarchyForm(event) {
    event.preventDefault();
    const form = event.target;
    const entityType = form.elements['entity_type_hierarchy'].value; 
    const entityId = form.elements['entity_id_hierarchy'].value;
    const responseDisplay = document.getElementById('hierarchy_response');
    if (!responseDisplay) return;
    responseDisplay.innerHTML = '<p>Загрузка...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/hierarchy/?entity_type=${entityType}&entity_id=${entityId}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`Ошибка ${response.status}: ${errorData.detail || 'Не удалось получить данные'}`);
        }
        const data = await response.json();
        responseDisplay.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    } catch (error) {
        responseDisplay.innerHTML = '<p style="color: red;">' + error.message + '</p>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const initPromises = [
        populateSelect('factory_id_section_create_select', 'factories', false, 'Выберите фабрику'),
        populateSelect('equipment_ids_section_create_select', 'equipment', false, 'Выберите оборудование'),
        populateSelect('section_ids_equipment_create_select', 'sections', false, 'Выберите участки')
    ];

    Promise.all(initPromises)
    .then(() => {
        console.log("All select dropdowns populated initially.");
        return Promise.all([
            loadEntityList('factories'),
            loadEntityList('sections'),
            loadEntityList('equipment')
        ]);
    })
    .catch(error => {
        console.error("Error during initial population or list loading:", error);
        loadEntityList('factories');
        loadEntityList('sections');
        loadEntityList('equipment');
    });

    const hierarchyForm = document.getElementById('hierarchyForm');
    if (hierarchyForm) {
        hierarchyForm.addEventListener('submit', submitHierarchyForm);
    }
});
