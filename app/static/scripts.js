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
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                responseData = await response.json();
            } else {
                responseData = { detail: await response.text() };
                 if (!response.ok) throw { status: response.status, data: responseData };
            }
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
    if (!selectEl) {
        console.warn(`Select element with ID ${selectElementId} not found for populateSelect.`);
        return;
    }
    
    const currentValues = selectEl.multiple ? Array.from(selectEl.selectedOptions).map(opt => opt.value) : [selectEl.value];
    selectEl.innerHTML = `<option value="">${prompt}</option>`; 
    
    try {
        let items = entityCache[entityType];
        if (!items || items.length === 0) {
            items = await callApi(`${API_BASE_URL}/${entityType}/?limit=1000&include_inactive=true`, 'GET');
            entityCache[entityType] = items || [];
        }
        
        (items || []).forEach(item => {
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

        if (selectEl.multiple) {
            Array.from(selectEl.options).forEach(opt => {
                if (currentValues.includes(opt.value)) {
                    opt.selected = true;
                }
            });
        } else if (currentValues.length > 0 && currentValues[0] !== "") {
            selectEl.value = currentValues[0];
        }

    } catch (error) {
        console.error(`Error populating select ${selectElementId}:`, error);
        selectEl.innerHTML = `<option value="">Ошибка загрузки</option>`;
    }
}

async function handleDataFormSubmit(event, method, entityType, responseElementId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const dataPayload = {}; 
    let entityId = formData.get('id'); 

    formData.forEach((value, key) => {
        if (key === 'id') return; 

        let parsedValue;
        const formElement = form.elements[key];

        if (formElement && formElement.multiple) {
            parsedValue = formData.getAll(key).map(idStr => parseInt(idStr.trim())).filter(idNum => !isNaN(idNum));
        } else if (key.endsWith('_id') && value === "" && formElement && formElement.tagName === 'SELECT') {
            parsedValue = (method === 'PUT') ? undefined : null; 
        } else if (formElement && formElement.type === 'number' && value !== '') {
            parsedValue = parseFloat(value);
        } else if (formElement && (formElement.type === 'text' || formElement.type === 'textarea')) {
            if (method === 'PUT' && value === '' && key !== 'description') { 
                 parsedValue = undefined;
            } else {
                parsedValue = value;
            }
        } else {
            parsedValue = value;
        }
        
        if (parsedValue !== undefined) {
            dataPayload[key] = parsedValue;
        }
    });
    
    console.log(`Submitting ${method} for ${entityType} with ID ${entityId}. Body:`, JSON.stringify(dataPayload));
    const url = entityId ? `${API_BASE_URL}/${entityType}/${entityId}` : `${API_BASE_URL}/${entityType}/`;

    try {
        await callApi(url, method, dataPayload, responseElementId);
        
        if (method === 'POST' && form.classList.contains('create-form')) {
            form.reset();
            const detailsContainer = form.closest('details');
            if (detailsContainer) detailsContainer.open = false;
            if (entityType === 'sections') {
                populateSelect('factory_id_section_create_select', 'factories', false, 'Выберите фабрику');
                populateSelect('equipment_ids_section_create_select', 'equipment', false, 'Выберите оборудование');
            } else if (entityType === 'equipment') {
                populateSelect('section_ids_equipment_create_select', 'sections', false, 'Выберите участки');
            }
        }
        if (method === 'PUT') {
            const updateFormContainer = document.getElementById(`update${entityType.charAt(0).toUpperCase() + entityType.slice(1)}FormContainer`);
            if (updateFormContainer && updateFormContainer.tagName === 'DETAILS') {
                 updateFormContainer.open = false; 
            }
            form.reset(); 
            if(form.elements['id']) form.elements['id'].value = ''; 
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
        const allItemsForCache = await callApi(`${API_BASE_URL}/${entityType}/?limit=1000&include_inactive=true`, 'GET');
        entityCache[entityType] = allItemsForCache || [];

        const itemsToDisplay = includeInactive 
            ? entityCache[entityType] 
            : entityCache[entityType].filter(it => it.is_active);

        listEl.innerHTML = ''; 
        if (itemsToDisplay && itemsToDisplay.length > 0) {
            itemsToDisplay.forEach(item => {
                const li = document.createElement('li');
                li.className = item.is_active ? '' : 'inactive-item';
                let itemDetails = '';
                if (entityType === 'sections') {
                    const factory = entityCache.factories.find(f => f.id === item.factory_id);
                    itemDetails = `(Фабрика: ${factory ? factory.name : 'ID ' + item.factory_id || 'N/A'})`;
                    if (item.equipment && Array.isArray(item.equipment) && item.equipment.length > 0) {
                        itemDetails += `<br><small>Оборудование: ${item.equipment.map(eq => eq.name).join(', ')}</small>`;
                    }
                } else if (entityType === 'equipment') {
                    if (item.description) itemDetails += `<br><small>Описание: ${item.description || ""}</small>`;
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
                        <button class="action-btn edit" onclick="showUpdateForm('${entityType}', ${item.id})">Ред.</button>
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

async function showUpdateForm(entityType, itemId) {
    console.log(`[showUpdateForm] Called for ${entityType}, ID: ${itemId}`);
    
    let singularEntityTypeCapitalized;
    if (entityType === 'factories') {
        singularEntityTypeCapitalized = 'Factory';
    } else if (entityType === 'sections') {
        singularEntityTypeCapitalized = 'Section';
    } else if (entityType === 'equipment') {
        singularEntityTypeCapitalized = 'Equipment';
    } else {
        console.error(`[showUpdateForm] Unknown entityType: ${entityType}`);
        return;
    }

    const formContainerId = `update${singularEntityTypeCapitalized}FormContainer`;
    const formContainer = document.getElementById(formContainerId);
    const formId = `update${singularEntityTypeCapitalized}Form`;
    const form = document.getElementById(formId);

    if (!formContainer || !form) {
        console.error(`[showUpdateForm] Form container or form not found. Container ID: ${formContainerId}, Form ID: ${formId}`);
        const generalResponseArea = document.getElementById(`${entityType.slice(0, -1)}Response`) || document.getElementById(`${entityType}Response`); // factories -> factoryResponse
        if(generalResponseArea) displayResponse(generalResponseArea.id, {detail: `Ошибка UI: не найден контейнер (${formContainerId}) или форма (${formId}) для редактирования.`}, true);
        return;
    }
    console.log(`[showUpdateForm] Form container and form found for ${entityType}.`);

    const selectPopulationPromises = [];
    if (entityType === 'sections') {
        selectPopulationPromises.push(populateSelect('factory_id_section_update_select', 'factories', false, 'Выберите фабрику'));
        selectPopulationPromises.push(populateSelect('equipment_ids_section_update_select', 'equipment', false, 'Выберите оборудование'));
    } else if (entityType === 'equipment') {
        selectPopulationPromises.push(populateSelect('section_ids_equipment_update_select', 'sections', false, 'Выберите участки'));
    }

    try {
        if (selectPopulationPromises.length > 0) {
            console.log(`[showUpdateForm] Waiting for ${selectPopulationPromises.length} select(s) to populate for ${entityType}...`);
            await Promise.all(selectPopulationPromises);
            console.log(`[showUpdateForm] Selects populated for ${entityType} update form.`);
        } else {
            console.log(`[showUpdateForm] No select fields to populate for ${entityType}.`);
        }
        
        populateFormFields(entityType, itemId, form); 

        if (formContainer.tagName === 'DETAILS') {
            if (!formContainer.open) {
                console.log(`[showUpdateForm] Opening details container for ${entityType}.`);
                formContainer.open = true;
            }
        }
        formContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        console.error(`[showUpdateForm] Error during select/field population for ${entityType} ID ${itemId}:`, error);
        displayResponse(`${entityType.slice(0, -1)}Response`, {detail: `Ошибка подготовки формы редактирования: ${error.message || 'Неизвестная ошибка'}`}, true);
    }
}

function populateFormFields(entityType, itemId, form) {
    const item = (entityCache[entityType] || []).find(i => i.id === itemId);
    if (!item) {
        console.error(`[populateFormFields] Item with ID ${itemId} not found in ${entityType} cache.`);
        const responseAreaId = entityType === "factories" ? "factoryResponse" : (entityType === "sections" ? "sectionResponse" : "equipmentResponse");
        displayResponse(responseAreaId, { detail: `Элемент ${entityType} с ID ${itemId} для редактирования не найден в кэше.` }, true);
        return;
    }
    console.log(`[populateFormFields] Populating fields for ${entityType} ID ${itemId}. Item:`, item);

    form.reset(); 
    form.querySelectorAll('select[multiple]').forEach(select => {
        for (let i = 0; i < select.options.length; i++) {
            select.options[i].selected = false;
        }
    });
    
    form.elements['id'].value = itemId; 

    const nameInput = form.elements['name']; 
    if (nameInput && item.name !== undefined) {
         nameInput.value = item.name;
         console.log(`[populateFormFields] Set name to: "${item.name}" for element:`, nameInput);
    } else {
        console.warn(`[populateFormFields] Name field (name="name") not found in form or item.name is undefined for ${entityType}. Form name input: `, nameInput);
    }

    if (entityType === 'equipment') {
        const descriptionInput = form.elements['description'];
        if (descriptionInput && item.description !== undefined) {
            descriptionInput.value = item.description === null ? '' : item.description;
            console.log(`[populateFormFields] Set description to: "${descriptionInput.value}"`);
        }
    }

    if (entityType === 'sections') {
        const factorySelect = form.elements['factory_id']; 
        if (factorySelect && item.factory_id !== undefined) {
             factorySelect.value = item.factory_id || "";
             console.log(`[populateFormFields] Set factory_id to: "${factorySelect.value}"`);
        }

        const equipmentSelect = form.elements['equipment_ids']; 
        if (equipmentSelect && item.equipment && Array.isArray(item.equipment)) { 
            const selectedEquipmentIds = item.equipment.map(eq => String(eq.id));
            for (let i = 0; i < equipmentSelect.options.length; i++) {
                equipmentSelect.options[i].selected = selectedEquipmentIds.includes(equipmentSelect.options[i].value);
            }
            console.log(`[populateFormFields] Set equipment_ids. Selected:`, selectedEquipmentIds);
        }
    } 
    else if (entityType === 'equipment') {
        const sectionSelect = form.elements['section_ids']; 
        if (sectionSelect && item.sections && Array.isArray(item.sections)) { 
            const selectedSectionIds = item.sections.map(s => String(s.id));
            for (let i = 0; i < sectionSelect.options.length; i++) {
                sectionSelect.options[i].selected = selectedSectionIds.includes(sectionSelect.options[i].value);
            }
            console.log(`[populateFormFields] Set section_ids. Selected:`, selectedSectionIds);
        }
    }
     console.log(`[populateFormFields] Form for ${entityType} ID ${itemId} populated.`);
}


async function deactivateEntity(entityType, id) {
    if (!confirm(`Вы уверены, что хотите деактивировать ${entityType} с ID ${id}?`)) return;
    const responseElementId = `${entityType}Response`;
    try {
        await callApi(`${API_BASE_URL}/${entityType}/${id}`, 'DELETE', null, responseElementId);
        const includeInactiveCheckbox = document.getElementById(`includeInactive${entityType.charAt(0).toUpperCase() + entityType.slice(1)}`);
        loadEntityList(entityType, includeInactiveCheckbox ? includeInactiveCheckbox.checked : false);
    } catch (error) {}
}

async function activateEntity(entityType, id) {
    const responseElementId = `${entityType}Response`;
    try {
        await callApi(`${API_BASE_URL}/${entityType}/${id}/activate`, 'PUT', null, responseElementId);
        const includeInactiveCheckbox = document.getElementById(`includeInactive${entityType.charAt(0).toUpperCase() + entityType.slice(1)}`);
        loadEntityList(entityType, includeInactiveCheckbox ? includeInactiveCheckbox.checked : false);
    } catch (error) {}
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
    const createFormSelectPromises = [
        populateSelect('factory_id_section_create_select', 'factories', false, 'Выберите фабрику'),
        populateSelect('equipment_ids_section_create_select', 'equipment', false, 'Выберите оборудование'),
        populateSelect('section_ids_equipment_create_select', 'sections', false, 'Выберите участки')
    ];

    Promise.all(createFormSelectPromises)
    .then(() => {
        console.log("Create form select dropdowns populated initially.");
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

    ['Factory', 'Section', 'Equipment'].forEach(type => {
        const updateFormContainer = document.getElementById(`update${type}FormContainer`);
        const form = document.getElementById(`update${type}Form`);

        if (form && !form.querySelector('button.cancel-button')) {
            const cancelButton = document.createElement('button');
            cancelButton.type = 'button'; 
            cancelButton.textContent = 'Отмена';
            cancelButton.classList.add('action-btn', 'cancel-button'); 
            cancelButton.style.backgroundColor = '#777'; 
            cancelButton.onclick = () => {
                form.reset();
                if(form.elements['id']) form.elements['id'].value = ''; 
                if (updateFormContainer && updateFormContainer.tagName === 'DETAILS') {
                    updateFormContainer.open = false;
                }
            };
            form.appendChild(cancelButton);
        }
    });
});
