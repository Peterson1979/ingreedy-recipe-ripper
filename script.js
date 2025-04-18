document.addEventListener('DOMContentLoaded', () => {
    // Config
    const BACKEND_URL = 'https://ingreedy-recipe-ripper.onrender.com/api/rip-recipe';
    const STORAGE_KEY = 'ingreedyShoppingList';

    // DOM Elements
    const urlInput = document.getElementById('urlInput');
    const ripButton = document.getElementById('ripButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsSection = document.getElementById('resultsSection');
    const ingredientsTextarea = document.getElementById('ingredientsTextarea');
    const sourceInfo = document.getElementById('sourceInfo');
    const sourceUrlLink = document.getElementById('sourceUrlLink');
    const copyToShoppingListButton = document.getElementById('copyToShoppingListButton');
    const shoppingListUL = document.getElementById('shoppingList');
    const shoppingListPlaceholder = shoppingListUL.querySelector('.placeholder');
    const errorSection = document.getElementById('errorSection');
    const errorType = document.getElementById('errorType');
    const errorMessage = document.getElementById('errorMessage');
    const infoSection = document.getElementById('infoSection');
    const infoMessage = document.getElementById('infoMessage');
    const saveStatus = document.getElementById('saveStatus');
    const addItemButton = document.getElementById('addItemButton');
    const clearCheckedButton = document.getElementById('clearCheckedButton');
    const clearAllButton = document.getElementById('clearAllButton');
    const copyButton = document.getElementById('copyButton');
    const saveTextButton = document.getElementById('saveTextButton');
    const saveImageButton = document.getElementById('saveImageButton');
    const shareGenericButton = document.getElementById('shareGenericButton');
    const shareButtonsContainer = document.querySelector('.share-buttons');
    const listActionButtons = [copyButton, saveTextButton, saveImageButton, shareGenericButton, clearCheckedButton, clearAllButton];
    const shareLinks = shareButtonsContainer ? shareButtonsContainer.querySelectorAll('a') : [];

    let currentSourceUrl = ''; let scrapedSourceUrl = ''; let saveTimeout = null;

    // --- Initial Load ---
    loadShoppingList();
    updateActionButtonsState();
    updateCopyButtonState(); // Set initial button state

    // --- Main Rip Function ---
    ripButton.addEventListener('click', async () => {
        const url = urlInput.value.trim(); currentSourceUrl = url; scrapedSourceUrl = '';
        if (!url) { showError("Input Required", "Please enter a Recipe URL."); return; }
        try { new URL(url); } catch (_) { showError("Invalid Input", "Invalid URL format. Please include http:// or https://"); return; }
        resultsSection.classList.add('hidden'); ingredientsTextarea.value = ''; sourceUrlLink.textContent = ''; sourceUrlLink.href = '#'; sourceInfo.classList.add('hidden'); errorSection.classList.add('hidden'); infoSection.classList.add('hidden'); loadingIndicator.classList.remove('hidden');
        copyToShoppingListButton.disabled = true; // Ensure disabled during fetch

        const requestBody = JSON.stringify({ url: url }); const requestHeaders = { 'Content-Type': 'application/json' };
        try {
            console.log(`Sending request to ${BACKEND_URL}`);
            const response = await fetch(BACKEND_URL, { method: 'POST', headers: requestHeaders, body: requestBody });
            const data = await response.json();
            console.log(`Received response status: ${response.status}`);

            if (!response.ok) {
                let errorPrefix="Error";const message=data.error||`Request failed with status ${response.status}`;if(response.status===403||message.includes("Forbidden")){errorPrefix="Access Denied";}else if(response.status===404||message.includes("not found")||message.includes("missing")){errorPrefix="Not Found";}else if(message.includes("Could not connect")||message.includes("timed out")){errorPrefix="Connection Issue";}else if(message.includes("Could not find ingredients")){errorPrefix="Extraction Failed";}else if(message.includes("Could not find the source recipe link")){errorPrefix="Pinterest Issue";}else if(response.status>=400&&response.status<500){errorPrefix="Client Error";}else if(response.status>=500){errorPrefix="Server Error";}throw{name:errorPrefix,message:message};
            }

            if (data.ingredients && data.ingredients.trim() !== "") {
                ingredientsTextarea.value = data.ingredients;
                scrapedSourceUrl = data.source_url_scraped || currentSourceUrl;
                sourceUrlLink.textContent = scrapedSourceUrl; sourceUrlLink.href = scrapedSourceUrl.startsWith('http') ? scrapedSourceUrl : '#';
                sourceInfo.classList.remove('hidden'); resultsSection.classList.remove('hidden'); errorSection.classList.add('hidden'); infoSection.classList.add('hidden');
                // Explicitly update copy button state HERE after ingredients are populated
                updateCopyButtonState();
            } else {
                scrapedSourceUrl = data.source_url_scraped || currentSourceUrl;
                sourceUrlLink.textContent = scrapedSourceUrl; sourceUrlLink.href = scrapedSourceUrl.startsWith('http') ? scrapedSourceUrl : '#';
                sourceInfo.classList.remove('hidden'); resultsSection.classList.add('hidden'); errorSection.classList.add('hidden');
                showInfoMessage(`Successfully accessed ${scrapedSourceUrl}, but no ingredients were found after cleaning.`);
                // Ensure copy button remains disabled if no ingredients found
                updateCopyButtonState();
            }
        } catch (error) {
            console.error("Fetch or processing error:", error); currentSourceUrl = ''; scrapedSourceUrl = '';
            showError(error.name || "Error", error.message || "An unexpected error occurred."); resultsSection.classList.add('hidden');
            // Ensure copy button state is correct on error (it should be disabled)
            updateCopyButtonState();
        } finally {
            loadingIndicator.classList.add('hidden'); urlInput.value = '';
            // updateCopyButtonState(); // Call was already added above
        }
    });

    // --- Copy Extracted Ingredients ---
    copyToShoppingListButton.addEventListener('click', () => {
        if (copyToShoppingListButton.disabled) return;
        const ingredients = ingredientsTextarea.value.split('\n').filter(line => line.trim() !== '');
        if (ingredients.length === 0) { alert("No ingredients were extracted to copy."); return; }
        if (getShoppingListItemsAsArray(true).length > 0) { if (!confirm("This will replace your current shopping list. Are you sure?")) { return; } }
        clearShoppingList(); shoppingListPlaceholder.classList.add('hidden');
        ingredients.forEach(itemText => { const isHeader = looksLikeHeader(itemText); addShoppingListItem(itemText, false, isHeader); });
        saveShoppingList(); updateActionButtonsState(); updateCopyButtonState();
    });

    // --- Add New Item Button ---
     addItemButton.addEventListener('click', () => { const newItemText = prompt("Enter new shopping list item:"); if (newItemText && newItemText.trim() !== "") { shoppingListPlaceholder.classList.add('hidden'); addShoppingListItem(newItemText.trim(), false, false); saveShoppingList(); updateActionButtonsState(); } });

     // --- Clear Checked Items Button (Immediate Remove) ---
     clearCheckedButton.addEventListener('click', () => {
        if (clearCheckedButton.disabled) return;
        const checkedItems = shoppingListUL.querySelectorAll('li.checked:not(.list-header)');
        if (checkedItems.length > 0) {
            if (confirm(`Are you sure you want to remove ${checkedItems.length} checked item(s)?`)) {
                 checkedItems.forEach(li => li.remove()); // Remove immediately
                 saveShoppingList();
                 updateActionButtonsState();
            }
        } else { alert("No ingredient items are checked off."); }
     });

     // --- Clear All Button ---
      clearAllButton.addEventListener('click', () => { if (clearAllButton.disabled) return; const allItems = shoppingListUL.querySelectorAll('li:not(.placeholder)'); if (allItems.length > 0) { if (confirm("Are you sure you want to clear the entire shopping list?")) { clearShoppingList(); shoppingListPlaceholder.classList.remove('hidden'); saveShoppingList(); updateActionButtonsState(); updateCopyButtonState(); } } else { alert("Shopping list is already empty."); } });

    // --- Utility Functions ---
    function showError(type="Error", message) { errorType.textContent=type+":"; errorMessage.textContent=message; errorSection.classList.remove('hidden'); infoSection.classList.add('hidden'); resultsSection.classList.add('hidden'); sourceInfo.classList.add('hidden'); }
    function showInfoMessage(message) { infoMessage.textContent=message; infoSection.classList.remove('hidden'); errorSection.classList.add('hidden'); }
    function clearShoppingList() { shoppingListUL.querySelectorAll('li:not(.placeholder)').forEach(li => li.remove()); }
    function looksLikeHeader(text) { const trimmed=text.trim(); if(!trimmed)return false; if(trimmed.endsWith(':')&&trimmed.length<50)return true; if(trimmed.toLowerCase().startsWith('for the ')&&trimmed.length<50)return true; return false; }
    // Add list item with fade-in animation class
    function addShoppingListItem(text, isChecked = false, isHeader = false) { const li=document.createElement('li'); li.classList.add('fade-in'); if(isHeader){li.classList.add('list-header');const span=document.createElement('span');span.textContent=text;li.appendChild(span);}else{li.setAttribute('draggable','true');if(isChecked){li.classList.add('checked');}const handle=document.createElement('span');handle.className='drag-handle';handle.title='Drag to reorder';li.appendChild(handle);const checkbox=document.createElement('input');checkbox.setAttribute('type','checkbox');checkbox.checked=isChecked;checkbox.addEventListener('change',()=>{li.classList.toggle('checked',checkbox.checked);saveShoppingList();updateActionButtonsState();});const span=document.createElement('span');span.className='item-text';span.textContent=text;span.setAttribute('contenteditable','true');span.addEventListener('keydown',(e)=>{if(e.key==='Enter'){e.preventDefault();span.blur();}});span.addEventListener('blur',()=>{const newText=span.textContent.trim();if(newText===""){li.remove();}else{span.textContent=newText;}saveShoppingList();updateActionButtonsState();});li.appendChild(checkbox);li.appendChild(span);addDeleteButton(li);}addDragDropListeners(li);shoppingListUL.appendChild(li);updateCopyButtonState();}
    // Delete button function (Immediate Remove)
    function addDeleteButton(li) {
        if (li.classList.contains('list-header')) return;
        const deleteBtn = document.createElement('button');
        deleteBtn.innerHTML = '×';
        deleteBtn.className = 'delete-item';
        deleteBtn.setAttribute('aria-label', 'Delete item');
        deleteBtn.title = 'Delete this item';
        deleteBtn.onclick = () => {
            li.remove(); // Remove immediately
            saveShoppingList();
            updateActionButtonsState(); // Update buttons after deletion
        };
        li.appendChild(deleteBtn);
    }

    // --- Drag and Drop Implementation ---
    let draggedItem=null; function addDragDropListeners(item){ const handle=item.querySelector('.drag-handle'); const target=handle||item; if(item.getAttribute('draggable')==='true'){ target.addEventListener('dragstart',handleDragStart); item.addEventListener('dragover',handleDragOver); item.addEventListener('dragleave',handleDragLeave); item.addEventListener('drop',handleDrop); target.addEventListener('dragend',handleDragEnd); }} function handleDragStart(e){ draggedItem=this.closest('li'); e.dataTransfer.effectAllowed='move'; setTimeout(()=>{if(draggedItem)draggedItem.classList.add('dragging');},0); } function handleDragOver(e){ e.preventDefault(); e.dataTransfer.dropEffect='move'; const targetItem=e.target.closest('li:not(.list-header)'); if(targetItem&&draggedItem&&targetItem!==draggedItem&&!targetItem.classList.contains('placeholder')){ const rect=targetItem.getBoundingClientRect(); const offsetY=e.clientY-rect.top; const isOverTopHalf=offsetY<rect.height/2; shoppingListUL.querySelectorAll('li.drag-over').forEach(li=>li.classList.remove('drag-over')); targetItem.classList.add('drag-over'); targetItem.dataset.dropPosition=isOverTopHalf?'before':'after'; } shoppingListUL.classList.add('drag-container-over'); } function handleDragLeave(e){ const targetItem=e.target.closest('li'); if(targetItem){ targetItem.classList.remove('drag-over'); delete targetItem.dataset.dropPosition; } if(!shoppingListUL.contains(e.relatedTarget)){ shoppingListUL.classList.remove('drag-container-over'); }} function handleDrop(e){ e.preventDefault(); e.stopPropagation(); const targetItem=e.target.closest('li:not(.placeholder):not(.list-header)'); if(targetItem&&draggedItem&&targetItem!==draggedItem){ const dropPosition=targetItem.dataset.dropPosition; if(dropPosition==='before'){ shoppingListUL.insertBefore(draggedItem,targetItem); }else{ targetItem.parentNode.insertBefore(draggedItem,targetItem.nextSibling); }}else if(draggedItem){ shoppingListUL.appendChild(draggedItem); } if(targetItem){ targetItem.classList.remove('drag-over'); delete targetItem.dataset.dropPosition; } saveShoppingList(); } function handleDragEnd(){ if(draggedItem){draggedItem.classList.remove('dragging');} shoppingListUL.querySelectorAll('li.drag-over').forEach(li=>li.classList.remove('drag-over')); shoppingListUL.querySelectorAll('li').forEach(li=>delete li.dataset.dropPosition); shoppingListUL.classList.remove('drag-container-over'); draggedItem=null; }

    // --- Get List Items Functions ---
    function getShoppingListItemsAsText(){ const items=[]; shoppingListUL.querySelectorAll('li:not(.placeholder)').forEach(li=>{ if(li.classList.contains('list-header')){ items.push('\n'+li.textContent.trim()); }else{ const span=li.querySelector('span.item-text'); const text=span?span.textContent.trim():''; if(text){items.push(text);}} }); return items.join('\n').trim(); }
    function getShoppingListItemsAsArray(includeHeaders=false){ const items = []; const selector = includeHeaders ? 'li:not(.placeholder)' : 'li:not(.placeholder):not(.list-header)'; shoppingListUL.querySelectorAll(selector).forEach(li => { const span = li.querySelector('span.item-text') || li.querySelector('span'); const text = span ? span.textContent.trim() : ''; if (text) { items.push(text); } }); return items; }

    // --- Persistence Functions ---
    function saveShoppingList(){ const items=[]; shoppingListUL.querySelectorAll('li:not(.placeholder)').forEach(li=>{ const isHeader=li.classList.contains('list-header'); const textSpan=li.querySelector('span'); const text=textSpan?textSpan.textContent.trim():''; if(text){ if(isHeader){ items.push({text:text,isHeader:true}); }else{ const checkbox=li.querySelector('input[type="checkbox"]'); items.push({text:text,checked:checkbox?checkbox.checked:false,isHeader:false});}} }); localStorage.setItem(STORAGE_KEY,JSON.stringify(items)); console.log("Shopping list saved."); showSaveStatus(); }
    function loadShoppingList(){ const savedList=localStorage.getItem(STORAGE_KEY); clearShoppingList(); if(savedList){ try{ const items=JSON.parse(savedList); if(items&&items.length>0){ shoppingListPlaceholder.classList.add('hidden'); items.forEach(item=>{ const isHeader=item.isHeader===true; addShoppingListItem(item.text,item.checked||false,isHeader); }); console.log("Shopping list loaded."); }else{ shoppingListPlaceholder.classList.remove('hidden'); }}catch(e){ console.error("Error parsing saved list:",e); localStorage.removeItem(STORAGE_KEY); shoppingListPlaceholder.classList.remove('hidden'); }} else{ shoppingListPlaceholder.classList.remove('hidden'); } /* updateActionButtonsState called by addShoppingListItem */}
    function showSaveStatus(){ if(saveTimeout)clearTimeout(saveTimeout); saveStatus.textContent="List saved ✓"; saveStatus.classList.add('visible'); saveTimeout=setTimeout(()=>{saveStatus.classList.remove('visible');},1500); }

    // --- Manage Button States ---
    function updateActionButtonsState() {
        const hasAnyItems = shoppingListUL.querySelectorAll('li:not(.placeholder)').length > 0;
        const hasIngredientItems = shoppingListUL.querySelectorAll('li:not(.placeholder):not(.list-header)').length > 0;
        const hasCheckedItems = shoppingListUL.querySelectorAll('li.checked:not(.list-header)').length > 0;

        listActionButtons.forEach(button => button.disabled = !hasAnyItems);
        addItemButton.disabled = false;
        clearCheckedButton.disabled = !hasCheckedItems;
        shareButtonsContainer.setAttribute('aria-disabled', !hasAnyItems);

        if (hasAnyItems) { shoppingListPlaceholder.classList.add('hidden'); }
        else { shoppingListPlaceholder.classList.remove('hidden'); }
    }
    function updateCopyButtonState() {
        const extractedText = ingredientsTextarea.value.trim();
        const listHasItems = shoppingListUL.querySelectorAll('li:not(.placeholder)').length > 0;

        if (!extractedText) {
             copyToShoppingListButton.disabled = true;
             copyToShoppingListButton.innerHTML = `<img src="copy-icon.svg" alt="Copy"> Extract Ingredients First`;
        } else {
            copyToShoppingListButton.disabled = false;
            const buttonText = listHasItems ? 'Replace Shopping List Below' : 'Create Shopping List Below';
            copyToShoppingListButton.innerHTML = `<img src="copy-icon.svg" alt="Copy"> ${buttonText}`;
        }
         updateActionButtonsState(); // Ensure other buttons updated too
    }

    // --- Action Button Event Listeners ---
    copyButton.addEventListener('click', ()=>{ if(copyButton.disabled)return; const textToCopy=getShoppingListItemsAsText(); if(!textToCopy)return; navigator.clipboard.writeText(textToCopy).then(()=>{ const originalHTML=copyButton.innerHTML; const copyIcon=copyButton.querySelector('img'); const originalAlt=copyIcon?copyIcon.alt:"Copy"; copyButton.innerHTML=`<img src="${copyIcon?copyIcon.src:'copy-icon.svg'}" alt="Copied"> Copied!`; setTimeout(()=>{copyButton.innerHTML=`<img src="${copyIcon?copyIcon.src:'copy-icon.svg'}" alt="${originalAlt}"> Copy List`},2000); }).catch(err=>{console.error('Failed to copy text: ',err);alert('Failed to copy text.');}); });
    saveTextButton.addEventListener('click', ()=>{ if(saveTextButton.disabled)return; const textToSave=getShoppingListItemsAsText(); if(!textToSave)return; const textBlob=new Blob([textToSave],{type:'text/plain'}); const downloadLink=document.createElement('a'); downloadLink.href=URL.createObjectURL(textBlob); downloadLink.download='shopping-list.txt'; document.body.appendChild(downloadLink); downloadLink.click(); document.body.removeChild(downloadLink); URL.revokeObjectURL(downloadLink.href); });
    saveImageButton.addEventListener('click', ()=>{ if(saveImageButton.disabled)return; const lines=getShoppingListItemsAsArray(); if(lines.length===0)return; const ctx=imageCanvas.getContext('2d'); const padding=20; const lineHeight=24; const fontSize=16; const fontFamily='monospace'; ctx.font=`${fontSize}px ${fontFamily}`; let maxWidth=0; lines.forEach(line=>{const width=ctx.measureText(line).width;if(width>maxWidth)maxWidth=width;}); const minWidth=200; const canvasWidth=Math.max(maxWidth+padding*2,minWidth); const canvasHeight=lines.length*lineHeight+padding*2; imageCanvas.width=canvasWidth; imageCanvas.height=canvasHeight; ctx.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--primary-bg-light').trim()||'#EBF8FF'; ctx.fillRect(0,0,canvasWidth,canvasHeight); ctx.fillStyle=getComputedStyle(document.documentElement).getPropertyValue('--text-dark').trim()||'#2D3748'; ctx.font=`${fontSize}px ${fontFamily}`; ctx.textBaseline='top'; lines.forEach((line,index)=>{ctx.fillText(line,padding,padding+index*lineHeight);}); const downloadLink=document.createElement('a'); try{downloadLink.href=imageCanvas.toDataURL('image/png'); downloadLink.download='shopping-list.png'; document.body.appendChild(downloadLink); downloadLink.click(); document.body.removeChild(downloadLink);}catch(e){console.error("Canvas error:",e);alert("Could not save image.");}});

    // --- Share Button Listeners ---
    shareGenericButton.addEventListener('click', async () => { if(shareGenericButton.disabled)return; const listText=getShoppingListItemsAsText(); if(!listText){alert("Shopping list is empty, nothing to share.");return;} const sourceUrl=(scrapedSourceUrl&&scrapedSourceUrl.startsWith('http'))?scrapedSourceUrl:null; const shareTitle="INGREEDY Shopping List"; let shareBody=listText; if(sourceUrl){shareBody+=`\n\n(From: ${sourceUrl})`;} const shareData={title:shareTitle,text:shareBody,}; if(sourceUrl){shareData.url=sourceUrl;} if(navigator.share){try{await navigator.share(shareData);console.log('Content shared successfully');}catch(err){console.error('Share failed:',err.message);if(err.name!=='AbortError'){copyListToClipboardAndNotify(listText,sourceUrl);}}}else{console.log('Web Share API not supported, falling back to clipboard.');copyListToClipboardAndNotify(listText,sourceUrl);}});
    function copyListToClipboardAndNotify(listText, sourceUrl){ let textToCopy=listText; if(sourceUrl){textToCopy+=`\n\n(From: ${sourceUrl})`;} navigator.clipboard.writeText(textToCopy).then(()=>{alert('Web Share not supported.\nShopping list text copied to clipboard! Paste it where you want to share.');}).catch(err=>{console.error('Fallback clipboard copy failed: ',err);alert('Could not copy list to clipboard.');});}
    function getShareContent(maxLength=500){ let text=getShoppingListItemsAsText();if(!text)return"";const prefix="My Shopping List (from INGREEDY):\n";const availableLength=maxLength-prefix.length;if(text.length>availableLength){text=text.substring(0,availableLength-3)+"...";}let shareText=prefix+text;const sourceUrlToShare=(scrapedSourceUrl&&scrapedSourceUrl.startsWith('http'))?scrapedSourceUrl:null;if(sourceUrlToShare){const sourceSuffix=`\n(From: ${sourceUrlToShare})`;if(shareText.length+sourceSuffix.length<=maxLength){shareText+=sourceSuffix;}}return encodeURIComponent(shareText); }
    shareTwitter.addEventListener('click', (e)=>{ if(shareButtonsContainer.getAttribute('aria-disabled')==='true')return; e.preventDefault();const text=getShareContent(280);if(!text)return;window.open(`https://twitter.com/intent/tweet?text=${text}`,'_blank'); });
    shareFacebook.addEventListener('click', (e)=>{ if(shareButtonsContainer.getAttribute('aria-disabled')==='true')return; e.preventDefault();const text=getShareContent();if(!text)return;const urlToShare=(scrapedSourceUrl&&scrapedSourceUrl.startsWith('http'))?encodeURIComponent(scrapedSourceUrl):encodeURIComponent(window.location.href);window.open(`https://www.facebook.com/sharer/sharer.php?u=${urlToShare}"e=${text}`,'_blank'); });
    shareEmail.addEventListener('click', (e)=>{ if(shareButtonsContainer.getAttribute('aria-disabled')==='true')return; e.preventDefault();const fullText=getShoppingListItemsAsText();if(!fullText)return;const subject=encodeURIComponent("My Shopping List (from INGREEDY)");let body="Here's my shopping list:\n\n"+fullText;const sourceUrlToShare=(scrapedSourceUrl&&scrapedSourceUrl.startsWith('http'))?scrapedSourceUrl:null;if(sourceUrlToShare){body+=`\n\nOriginally from: ${sourceUrlToShare}`;}const encodedBody=encodeURIComponent(body);window.location.href=`mailto:?subject=${subject}&body=${encodedBody}`; });
    sharePinterest.addEventListener('click', (e)=>{ if(shareButtonsContainer.getAttribute('aria-disabled')==='true')return; e.preventDefault();const description=getShareContent(500);if(!description)return;const pageUrl=(scrapedSourceUrl&&scrapedSourceUrl.startsWith('http'))?encodeURIComponent(scrapedSourceUrl):encodeURIComponent(window.location.href);const pinterestUrl=`https://www.pinterest.com/pin/create/button/?url=${pageUrl}&description=${description}`;window.open(pinterestUrl,'_blank'); });

}); // End DOMContentLoaded
