let weaponData = null;
let state = {
    currentNodeId: null,
    path: [],
    cantTellCount: 0,
    consecutiveCantTell: 0,
    history: []
};

// Initialize app
async function init() {
    try {
        const response = await fetch('data.yaml');
        const yamlText = await response.text();
        weaponData = jsyaml.load(yamlText);
        renderLanding();
    } catch (e) {
        console.error("Failed to load YAML data", e);
        document.getElementById('app').innerHTML = `<p class="p-10 text-red-500 text-center">Error loading classification data.</p>`;
    }
}

function renderLanding() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="fade-in">
            <div class="text-center mb-12 mt-8">
                <h2 class="text-3xl font-extrabold text-slate-800">Visual Classification Start</h2>
                <p class="text-slate-500 mt-2 italic">Select the category that best matches your primary observation.</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div onclick="startFlow('group_handguns')" class="group cursor-pointer bg-white border rounded-xl overflow-hidden hover:ring-2 hover:ring-blue-500 transition-all shadow-sm">
                    <img src="https://raw.githubusercontent.com/paigemoody/weapons_classification_resources/main/small_arms_survey/visuals/Figure_3.2_Typical%20features%20of%20a%20modern%20handgun.png" class="w-full h-48 object-cover bg-slate-100 p-4">
                    <div class="p-5">
                        <h3 class="font-bold text-lg group-hover:text-blue-600">Handguns</h3>
                        <p class="text-sm text-slate-500">One-handed fire, no shoulder stock.</p>
                    </div>
                </div>

                <div onclick="startFlow('group_long_guns')" class="group cursor-pointer bg-white border rounded-xl overflow-hidden hover:ring-2 hover:ring-blue-500 transition-all shadow-sm">
                    <div class="w-full h-48 bg-slate-200 flex items-center justify-center text-slate-400 font-bold italic">RIFLES / LONG GUNS</div>
                    <div class="p-5">
                        <h3 class="font-bold text-lg group-hover:text-blue-600">Long Guns</h3>
                        <p class="text-sm text-slate-500">Shoulder stock and long barrel.</p>
                    </div>
                </div>

                <div onclick="renderFeatureJump()" class="cursor-pointer border-2 border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center p-8 hover:bg-slate-100 transition-all">
                    <span class="text-3xl mb-2">🔍</span>
                    <h3 class="font-bold">Feature Jump</h3>
                    <p class="text-xs text-center text-slate-400">Jump directly to muzzle, feed, or stock details.</p>
                </div>
            </div>
        </div>
    `;
}

function startFlow(nodeId) {
    state.currentNodeId = nodeId;
    renderNode(nodeId);
}

function renderNode(nodeId) {
    const node = weaponData.nodes.find(n => n.id === nodeId);
    const app = document.getElementById('app');

    app.innerHTML = `
        <div class="fade-in max-w-2xl mx-auto">
            <div class="mb-6 flex justify-between items-center text-[10px] font-mono uppercase tracking-widest text-slate-400">
                <span>Path: ${state.path.join(' > ') || 'Start'}</span>
                <span>Uncertainty: ${state.cantTellCount}/6</span>
            </div>

            <div class="bg-white border rounded-2xl shadow-lg p-8">
                <h2 class="text-2xl font-bold mb-6 text-slate-800">${node.prompt}</h2>
                
                ${node.visuals ? `
                    <div class="mb-8 rounded-lg overflow-hidden border bg-slate-50">
                        <img src="https://raw.githubusercontent.com/paigemoody/weapons_classification_resources/main/small_arms_survey/visuals/Figure_3.2_Typical%20features%20of%20a%20modern%20handgun.png" class="w-full max-h-80 object-contain p-4">
                        <div class="bg-slate-100 p-2 text-[10px] text-slate-500 text-center uppercase tracking-tighter">
                            ${node.visuals[0].caption} | ${node.visuals[0].source} p. ${node.visuals[0].page}
                        </div>
                    </div>
                ` : ''}

                <div class="grid grid-cols-1 gap-3">
                    <button onclick="handleChoice('yes')" class="w-full py-4 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition">YES</button>
                    <button onclick="handleChoice('no')" class="w-full py-4 bg-slate-100 text-slate-700 rounded-xl font-bold hover:bg-slate-200 transition">NO</button>
                    <button onclick="handleChoice('cant_tell')" class="w-full py-4 border-2 border-dashed border-slate-200 text-slate-400 rounded-xl font-bold hover:bg-slate-50 transition">CAN'T TELL</button>
                </div>
            </div>
        </div>
    `;
}

function handleChoice(choice) {
    const node = weaponData.nodes.find(n => n.id === state.currentNodeId);
    const nextId = node.answers[choice];

    if (choice === 'cant_tell') {
        state.cantTellCount++;
        state.consecutiveCantTell++;
    } else {
        state.consecutiveCantTell = 0;
    }

    if (state.consecutiveCantTell >= 3 || state.cantTellCount >= 6) {
        renderObservationMode();
    } else {
        state.path.push(node.level);
        state.currentNodeId = nextId;
        renderNode(nextId);
    }
}

function resetFlow() {
    if (confirm("Restart classification? This will clear your current path.")) {
        state = { currentNodeId: null, path: [], cantTellCount: 0, consecutiveCantTell: 0, history: [] };
        renderLanding();
    }
}

function renderObservationMode() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="fade-in max-w-2xl mx-auto bg-amber-50 border border-amber-200 p-8 rounded-2xl shadow-inner">
            <h2 class="text-2xl font-black text-amber-800 mb-4 uppercase">Observation Mode Triggered</h2>
            <p class="mb-6 text-amber-900">High uncertainty threshold reached. Based on your answers, the lowest defensible level is:</p>
            <div class="bg-white p-4 rounded border border-amber-200 font-mono text-xl mb-6">${state.path.join(' > ') || 'Unknown Class'}</div>
            <button onclick="renderFeatureJump()" class="w-full py-4 bg-amber-600 text-white rounded-xl font-bold">Review Specific Features</button>
        </div>
    `;
}

function renderFeatureJump() {
    // Simplified Feature Jump for demo
    const app = document.getElementById('app');
    app.innerHTML = `<div class="text-center p-20"><h2 class="text-2xl font-bold">Feature Jump Menu</h2><p class="text-slate-500">Spec Section 6: Select features (Muzzle, Feed, etc.) to continue.</p><button onclick="renderLanding()" class="mt-4 text-blue-500 underline">Back</button></div>`;
}

init();
