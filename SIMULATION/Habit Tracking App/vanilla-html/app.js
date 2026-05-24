// App State
const appState = {
    currentPage: 'form',
    budgetData: {
        totalBudget: 4500000,
        participants: 2,
        duration: 2
    },
    selectedPackage: 'hemat',
    expandedCard: null,
    copiedCoord: null,
    mapZoom: 13,
    hoveredPin: null
};

// Package Data
const packagesData = [
    {
        type: 'hemat',
        badge: 'HEMAT',
        badgeColor: 'bg-green-500',
        status: 'Budget: Hemat',
        title: 'Opsi 1 (Hemat)',
        hotel: {
            name: 'SUPER OYO Flagship 90502 Holistay...',
            fullName: 'SUPER OYO Flagship 90502 Holistay Malang New',
            price: 347052,
            coords: '-7.9666, 112.6326',
            lat: -7.9666,
            lng: 112.6326
        },
        wisata: {
            name: 'Masjid Tiban Malang',
            fullName: 'Masjid Tiban Malang (pp.Salafiah Bihaaru Bahri)',
            price: 10000,
            coords: '-8.0045, 112.6789',
            lat: -8.0045,
            lng: 112.6789
        },
        makan: {
            name: 'Depot Gang Djangkrik Kawi Atas',
            fullName: 'Depot Gang Djangkrik Kawi Atas Malang',
            price: 27049,
            coords: '-7.9756, 112.6298',
            lat: -7.9756,
            lng: 112.6298
        },
        totalHotel: 347052,
        totalWisata: 20000,
        totalMakan: 324588,
        totalPrice: 691640
    },
    {
        type: 'balanced',
        badge: 'BALANCED',
        badgeColor: 'bg-blue-500',
        status: 'Budget: Pas',
        title: 'Opsi 2 (Balanced)',
        hotel: {
            name: 'OYO Life 91931 Permata Brantas',
            fullName: 'OYO Life 91931 Permata Brantas',
            price: 590409,
            coords: '-7.9556, 112.6198',
            lat: -7.9556,
            lng: 112.6198
        },
        wisata: {
            name: 'Makam Ki Ageng Gribig',
            fullName: 'Makam Ki Ageng Gribig',
            price: 5000,
            coords: '-8.0123, 112.6543',
            lat: -8.0123,
            lng: 112.6543
        },
        makan: {
            name: 'Resto 52',
            fullName: 'Resto 52',
            price: 117331,
            coords: '-7.9623, 112.6412',
            lat: -7.9623,
            lng: 112.6412
        },
        totalHotel: 590409,
        totalWisata: 10000,
        totalMakan: 1407972,
        totalPrice: 2008381
    },
    {
        type: 'premium',
        badge: 'PREMIUM',
        badgeColor: 'bg-amber-500',
        status: 'Budget: Fancy',
        title: 'Opsi 3 (Premium)',
        hotel: {
            name: 'Villa Malang MARRY IND Puncak Buring',
            fullName: 'Villa Malang MARRY IND Puncak Buring',
            price: 3644629,
            coords: '-7.9234, 112.6789',
            lat: -7.9234,
            lng: 112.6789
        },
        wisata: {
            name: 'Pura Luhur Giri Arjuno',
            fullName: 'Pura Luhur Giri Arjuno',
            price: 2000,
            coords: '-7.8956, 112.7012',
            lat: -7.8956,
            lng: 112.7012
        },
        makan: {
            name: 'Harmoni Cafe & Resto',
            fullName: 'Harmoni Cafe & Resto',
            price: 144714,
            coords: '-7.9445, 112.6534',
            lat: -7.9445,
            lng: 112.6534
        },
        totalHotel: 3644629,
        totalWisata: 4000,
        totalMakan: 1736568,
        totalPrice: 5385197
    }
];

// Utility Functions
function formatCurrency(number) {
    return new Intl.NumberFormat('id-ID').format(number);
}

function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Earth's radius in km
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLng = ((lng2 - lng1) * Math.PI) / 180;
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLng / 2) *
        Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return (R * c).toFixed(1);
}

// Page Renderers
function renderFormPage() {
    const template = document.getElementById('form-page-template');
    const content = template.content.cloneNode(true);

    // Set initial values
    const budgetInput = content.getElementById('total-budget');
    const participantsInput = content.getElementById('participants');
    const durationInput = content.getElementById('duration');

    budgetInput.value = formatCurrency(appState.budgetData.totalBudget);
    participantsInput.value = appState.budgetData.participants;
    durationInput.value = appState.budgetData.duration;

    // Update auto calculations
    updateAutoCalculations(content);

    return content;
}

function updateAutoCalculations(container) {
    const participants = parseInt(document.getElementById('participants')?.value || appState.budgetData.participants);
    const duration = parseInt(document.getElementById('duration')?.value || appState.budgetData.duration);
    const budgetInput = document.getElementById('total-budget')?.value || '';
    const totalBudget = parseInt(budgetInput.replace(/\D/g, '')) || appState.budgetData.totalBudget;

    const budgetPerPerson = Math.floor(totalBudget / participants);
    const hotelRooms = Math.ceil(participants / 2);
    const mealCount = participants * duration * 3;

    const budgetPerPersonEl = container.getElementById ? container.getElementById('budget-per-person') : document.getElementById('budget-per-person');
    const hotelRoomsEl = container.getElementById ? container.getElementById('hotel-rooms') : document.getElementById('hotel-rooms');
    const mealCountEl = container.getElementById ? container.getElementById('meal-count') : document.getElementById('meal-count');

    if (budgetPerPersonEl) {
        budgetPerPersonEl.textContent = `Budget Per Orang: Rp ${formatCurrency(budgetPerPerson)}`;
    }
    if (hotelRoomsEl) {
        hotelRoomsEl.textContent = `Kebutuhan Kamar Hotel: ${hotelRooms} kamar`;
    }
    if (mealCountEl) {
        mealCountEl.textContent = `Kebutuhan Makan: ${mealCount} kali`;
    }
}

function setupFormHandlers() {
    const budgetInput = document.getElementById('total-budget');
    const participantsInput = document.getElementById('participants');
    const durationInput = document.getElementById('duration');
    const form = document.getElementById('budget-form');

    // Budget input handler
    budgetInput.addEventListener('input', (e) => {
        const value = e.target.value.replace(/\D/g, '');
        e.target.value = value ? formatCurrency(parseInt(value)) : '';
        appState.budgetData.totalBudget = value ? parseInt(value) : 0;
        updateAutoCalculations(document);
    });

    // Participants handlers
    participantsInput.addEventListener('input', (e) => {
        const value = Math.max(1, parseInt(e.target.value) || 1);
        e.target.value = value;
        appState.budgetData.participants = value;
        updateAutoCalculations(document);
    });

    document.getElementById('participants-minus').addEventListener('click', () => {
        const newValue = Math.max(1, appState.budgetData.participants - 1);
        participantsInput.value = newValue;
        appState.budgetData.participants = newValue;
        updateAutoCalculations(document);
    });

    document.getElementById('participants-plus').addEventListener('click', () => {
        const newValue = appState.budgetData.participants + 1;
        participantsInput.value = newValue;
        appState.budgetData.participants = newValue;
        updateAutoCalculations(document);
    });

    // Duration handlers
    durationInput.addEventListener('input', (e) => {
        const value = Math.max(1, parseInt(e.target.value) || 1);
        e.target.value = value;
        appState.budgetData.duration = value;
        updateAutoCalculations(document);
    });

    document.getElementById('duration-minus').addEventListener('click', () => {
        const newValue = Math.max(1, appState.budgetData.duration - 1);
        durationInput.value = newValue;
        appState.budgetData.duration = newValue;
        updateAutoCalculations(document);
    });

    document.getElementById('duration-plus').addEventListener('click', () => {
        const newValue = appState.budgetData.duration + 1;
        durationInput.value = newValue;
        appState.budgetData.duration = newValue;
        updateAutoCalculations(document);
    });

    // Form submit
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        appState.currentPage = 'results';
        renderPage();
    });
}

function renderResultsPage() {
    const container = document.createElement('div');
    container.className = 'min-h-screen py-12 px-4';

    container.innerHTML = `
        <div class="max-w-7xl mx-auto">
            <!-- Header -->
            <div class="text-center mb-8">
                <button id="back-to-form" class="text-teal-600 hover:text-teal-700 mb-4 inline-flex items-center gap-2 font-medium">
                    ← Kembali ke Form
                </button>
                <h1 class="text-4xl font-bold text-gray-900 mb-3">
                    Rekomendasi Paket Wisata Untuk Anda
                </h1>
                <p class="text-lg text-gray-600">
                    Pilih paket yang sesuai dengan budget dan preferensi Anda
                </p>
            </div>
            
            <!-- Package Cards -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6" id="packages-container">
            </div>
        </div>
    `;

    const packagesContainer = container.querySelector('#packages-container');

    packagesData.forEach(pkg => {
        const card = createPackageCard(pkg);
        packagesContainer.appendChild(card);
    });

    return container;
}

function createPackageCard(pkg) {
    const remaining = appState.budgetData.totalBudget - pkg.totalPrice;
    const isAffordable = remaining >= 0;

    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow overflow-hidden';

    card.innerHTML = `
        <div class="${pkg.badgeColor} text-white text-center py-2 font-bold text-sm tracking-wider">
            ${pkg.badge}
        </div>
        
        <div class="p-6">
            <div class="text-gray-600 mb-6 font-medium">${pkg.status}</div>
            
            <!-- Hotel -->
            <div class="mb-5">
                <div class="flex items-start gap-2 mb-1">
                    <svg class="text-teal-600 mt-1 flex-shrink-0" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                    </svg>
                    <div class="flex-1">
                        <div class="font-bold text-xs text-gray-500 mb-1">HOTEL</div>
                        <div class="font-medium text-gray-900 text-sm mb-1">${pkg.hotel.name}</div>
                        <div class="text-teal-600 font-bold">Rp ${formatCurrency(pkg.hotel.price)} /malam</div>
                        <div class="flex items-center gap-1 text-xs text-gray-500 mt-1">
                            <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            </svg>
                            <span>${pkg.hotel.coords}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Wisata -->
            <div class="mb-5">
                <div class="flex items-start gap-2 mb-1">
                    <svg class="text-teal-600 mt-1 flex-shrink-0" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    <div class="flex-1">
                        <div class="font-bold text-xs text-gray-500 mb-1">WISATA</div>
                        <div class="font-medium text-gray-900 text-sm mb-1">${pkg.wisata.name}</div>
                        <div class="text-teal-600 font-bold">Rp ${formatCurrency(pkg.wisata.price)} /orang</div>
                        <div class="flex items-center gap-1 text-xs text-gray-500 mt-1">
                            <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            </svg>
                            <span>${pkg.wisata.coords}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Makan -->
            <div class="mb-5">
                <div class="flex items-start gap-2 mb-1">
                    <svg class="text-teal-600 mt-1 flex-shrink-0" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path>
                    </svg>
                    <div class="flex-1">
                        <div class="font-bold text-xs text-gray-500 mb-1">MAKAN</div>
                        <div class="font-medium text-gray-900 text-sm mb-1">${pkg.makan.name}</div>
                        <div class="text-teal-600 font-bold">Rp ${formatCurrency(pkg.makan.price)} /porsi</div>
                        <div class="flex items-center gap-1 text-xs text-gray-500 mt-1">
                            <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            </svg>
                            <span>${pkg.makan.coords}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Rincian Biaya Toggle -->
            <button class="toggle-details w-full flex items-center justify-between text-sm font-bold text-gray-700 py-2 border-t border-gray-200 hover:bg-gray-50 transition-colors" data-package="${pkg.type}">
                <span>Rincian Biaya</span>
                <svg class="chevron" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
            </button>
            
            <!-- Expandable Cost Details -->
            <div class="cost-details hidden mt-3 pt-3 border-t border-gray-200 space-y-2 text-sm">
                <div class="flex justify-between">
                    <span class="text-gray-600">Total Biaya Hotel:</span>
                    <span class="font-medium">Rp ${formatCurrency(pkg.totalHotel)}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600">Total Biaya Wisata:</span>
                    <span class="font-medium">Rp ${formatCurrency(pkg.totalWisata)}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-600">Total Biaya Makan:</span>
                    <span class="font-medium">Rp ${formatCurrency(pkg.totalMakan)}</span>
                </div>
                <div class="border-t-2 border-gray-300 pt-2 mt-2"></div>
            </div>
            
            <!-- Total Price -->
            <div class="bg-teal-50 rounded-lg p-4 mt-4 border-2 border-teal-100">
                <div class="text-xs font-bold text-gray-600 mb-1">TOTAL HARGA PAKET</div>
                <div class="text-2xl font-bold text-teal-700">Rp ${formatCurrency(pkg.totalPrice)}</div>
            </div>
            
            <!-- Remaining Budget -->
            <div class="rounded-lg p-4 mt-3 border-2 ${isAffordable ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}">
                <div class="text-xs font-bold text-gray-600 mb-1">SISA ANGGARAN</div>
                <div class="text-xl font-bold ${isAffordable ? 'text-green-700' : 'text-red-700'}">
                    ${remaining >= 0 ? '+' : ''}Rp ${formatCurrency(remaining)}
                </div>
                ${!isAffordable ? '<div class="text-xs text-red-600 mt-1">Melebihi budget Anda</div>' : ''}
            </div>
            
            <!-- Action Button -->
            <button class="view-detail w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 px-4 rounded-lg transition-colors mt-4" data-package="${pkg.type}">
                Lihat Detail & Peta
            </button>
        </div>
    `;

    return card;
}

function setupResultsHandlers() {
    document.getElementById('back-to-form').addEventListener('click', () => {
        appState.currentPage = 'form';
        renderPage();
    });

    // Toggle details buttons
    document.querySelectorAll('.toggle-details').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const button = e.currentTarget;
            const details = button.nextElementSibling;
            const isHidden = details.classList.contains('hidden');

            // Close all other details
            document.querySelectorAll('.cost-details').forEach(d => d.classList.add('hidden'));

            if (isHidden) {
                details.classList.remove('hidden');
            }
        });
    });

    // View detail buttons
    document.querySelectorAll('.view-detail').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const packageType = e.currentTarget.getAttribute('data-package');
            appState.selectedPackage = packageType;
            appState.currentPage = 'detail';
            renderPage();
        });
    });
}

function renderDetailPage() {
    const pkg = packagesData.find(p => p.type === appState.selectedPackage);

    const hotelToWisata = calculateDistance(pkg.hotel.lat, pkg.hotel.lng, pkg.wisata.lat, pkg.wisata.lng);
    const wisataToMakan = calculateDistance(pkg.wisata.lat, pkg.wisata.lng, pkg.makan.lat, pkg.makan.lng);
    const makanToHotel = calculateDistance(pkg.makan.lat, pkg.makan.lng, pkg.hotel.lat, pkg.hotel.lng);
    const totalDistance = (parseFloat(hotelToWisata) + parseFloat(wisataToMakan) + parseFloat(makanToHotel)).toFixed(1);

    const avgTotal = pkg.makan.price * appState.budgetData.participants * appState.budgetData.duration * 3;

    const container = document.createElement('div');
    container.className = 'min-h-screen py-8 px-4';

    container.innerHTML = `
        <div class="max-w-7xl mx-auto">
            <!-- Page Title -->
            <div class="mb-6">
                <button id="back-to-results" class="text-teal-600 hover:text-teal-700 mb-3 inline-flex items-center gap-2 font-medium">
                    ← Kembali ke Pilihan
                </button>
                <h1 class="text-3xl font-bold text-gray-900">
                    Detail Paket: ${pkg.title} - Rp ${formatCurrency(pkg.totalPrice)}
                </h1>
            </div>
            
            <!-- Split Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-5 gap-6">
                <!-- Left Side - Details (60%) -->
                <div class="lg:col-span-3 space-y-6">
                    <!-- Hotel Section -->
                    <div class="bg-white rounded-xl shadow-lg overflow-hidden">
                        <div class="aspect-video bg-gradient-to-br from-blue-200 to-blue-300 flex items-center justify-center">
                            <svg width="64" height="64" fill="none" stroke="currentColor" class="text-blue-600" style="opacity: 0.4" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                            </svg>
                        </div>
                        <div class="p-6">
                            <div class="flex items-start justify-between mb-3">
                                <div>
                                    <div class="text-xs font-bold text-gray-500 mb-1">HOTEL</div>
                                    <h3 class="text-xl font-bold text-gray-900">${pkg.hotel.fullName}</h3>
                                </div>
                                <div class="bg-teal-100 text-teal-700 font-bold px-3 py-1 rounded-lg text-sm whitespace-nowrap">
                                    Rp ${formatCurrency(pkg.hotel.price)} /malam
                                </div>
                            </div>
                            <div class="flex items-center gap-3 text-sm">
                                <div class="flex items-center gap-1 text-gray-600">
                                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                    </svg>
                                    <span>${pkg.hotel.coords}</span>
                                </div>
                                <button class="copy-coords text-teal-600 hover:text-teal-700 flex items-center gap-1" data-coords="${pkg.hotel.coords}">
                                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                                    </svg>
                                    <span>Salin</span>
                                </button>
                                <a href="https://www.google.com/maps?q=${pkg.hotel.coords}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-700">
                                    Lihat di Google Maps
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Wisata Section -->
                    <div class="bg-white rounded-xl shadow-lg overflow-hidden">
                        <div class="aspect-video bg-gradient-to-br from-green-200 to-green-300 flex items-center justify-center">
                            <svg width="64" height="64" fill="none" stroke="currentColor" class="text-green-600" style="opacity: 0.4" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            </svg>
                        </div>
                        <div class="p-6">
                            <div class="flex items-start justify-between mb-3">
                                <div>
                                    <div class="text-xs font-bold text-gray-500 mb-1">WISATA</div>
                                    <h3 class="text-xl font-bold text-gray-900">${pkg.wisata.fullName}</h3>
                                </div>
                                <div class="bg-teal-100 text-teal-700 font-bold px-3 py-1 rounded-lg text-sm whitespace-nowrap">
                                    Rp ${formatCurrency(pkg.wisata.price)} /tiket
                                </div>
                            </div>
                            <div class="flex items-center gap-3 text-sm">
                                <div class="flex items-center gap-1 text-gray-600">
                                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                    </svg>
                                    <span>${pkg.wisata.coords}</span>
                                </div>
                                <button class="copy-coords text-teal-600 hover:text-teal-700 flex items-center gap-1" data-coords="${pkg.wisata.coords}">
                                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                                    </svg>
                                    <span>Salin</span>
                                </button>
                                <a href="https://www.google.com/maps?q=${pkg.wisata.coords}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-700">
                                    Lihat di Google Maps
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Makan Section -->
                    <div class="bg-white rounded-xl shadow-lg overflow-hidden">
                        <div class="aspect-video bg-gradient-to-br from-orange-200 to-orange-300 flex items-center justify-center">
                            <svg width="64" height="64" fill="none" stroke="currentColor" class="text-orange-600" style="opacity: 0.4" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path>
                            </svg>
                        </div>
                        <div class="p-6">
                            <div class="flex items-start justify-between mb-3">
                                <div>
                                    <div class="text-xs font-bold text-gray-500 mb-1">MAKAN</div>
                                    <h3 class="text-xl font-bold text-gray-900">${pkg.makan.fullName}</h3>
                                </div>
                                <div class="bg-teal-100 text-teal-700 font-bold px-3 py-1 rounded-lg text-sm whitespace-nowrap">
                                    Rp ${formatCurrency(pkg.makan.price)} /porsi
                                </div>
                            </div>
                            <div class="text-sm text-gray-600 mb-2">
                                Rata-rata untuk ${appState.budgetData.participants * appState.budgetData.duration * 3}x makan:
                                <span class="font-bold text-gray-900">Rp ${formatCurrency(pkg.totalMakan)}</span>
                            </div>
                            <div class="flex items-center gap-3 text-sm">
                                <div class="flex items-center gap-1 text-gray-600">
                                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                    </svg>
                                    <span>${pkg.makan.coords}</span>
                                </div>
                                <button class="copy-coords text-teal-600 hover:text-teal-700 flex items-center gap-1" data-coords="${pkg.makan.coords}">
                                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                                    </svg>
                                    <span>Salin</span>
                                </button>
                                <a href="https://www.google.com/maps?q=${pkg.makan.coords}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-700">
                                    Lihat di Google Maps
                                </a>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Rincian Biaya Panel -->
                    <div class="bg-white rounded-xl shadow-lg p-6">
                        <h3 class="font-bold text-lg mb-4">RINCIAN BIAYA:</h3>
                        <div class="space-y-3">
                            <div class="flex justify-between items-center py-2 border-b border-gray-200">
                                <span class="text-gray-700 flex items-center gap-2">
                                    <svg class="text-green-600" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                    </svg>
                                    Hotel
                                </span>
                                <span class="font-bold">Rp ${formatCurrency(pkg.totalHotel)}</span>
                            </div>
                            <div class="flex justify-between items-center py-2 border-b border-gray-200">
                                <span class="text-gray-700 flex items-center gap-2">
                                    <svg class="text-green-600" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                    </svg>
                                    Wisata
                                </span>
                                <span class="font-bold">Rp ${formatCurrency(pkg.totalWisata)}</span>
                            </div>
                            <div class="flex justify-between items-center py-2 border-b border-gray-200">
                                <span class="text-gray-700 flex items-center gap-2">
                                    <svg class="text-green-600" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                                    </svg>
                                    Makan
                                </span>
                                <span class="font-bold">Rp ${formatCurrency(pkg.totalMakan)}</span>
                            </div>
                            <div class="flex justify-between items-center pt-3 border-t-2 border-gray-300">
                                <span class="font-bold text-lg">TOTAL</span>
                                <span class="font-bold text-2xl text-teal-600">Rp ${formatCurrency(pkg.totalPrice)}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Distance Info Panel -->
                    <div class="bg-teal-50 rounded-xl p-6 border-2 border-teal-100">
                        <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                            <svg class="text-teal-600" width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
                            </svg>
                            INFORMASI JARAK:
                        </h3>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-700">Hotel → Wisata:</span>
                                <span class="font-bold">${hotelToWisata} km</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-700">Wisata → Makan:</span>
                                <span class="font-bold">${wisataToMakan} km</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-700">Makan → Hotel:</span>
                                <span class="font-bold">${makanToHotel} km</span>
                            </div>
                            <div class="flex justify-between pt-2 border-t border-teal-200">
                                <span class="font-bold">Total jarak tempuh:</span>
                                <span class="font-bold text-teal-700">${totalDistance} km</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div class="flex gap-4">
                        <button class="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 px-6 rounded-lg transition-colors">
                            Simpan Paket
                        </button>
                        <button id="back-to-results-2" class="flex-1 bg-white hover:bg-gray-50 text-gray-700 font-bold py-3 px-6 rounded-lg border-2 border-gray-300 transition-colors">
                            Kembali ke Pilihan
                        </button>
                    </div>
                </div>
                
                <!-- Right Side - Map (40%) -->
                <div class="lg:col-span-2">
                    <div class="bg-white rounded-xl shadow-lg overflow-hidden sticky top-8">
                        <!-- Map Container -->
                        <div id="map-container" class="relative bg-gradient-to-br from-slate-100 to-slate-200 aspect-square">
                            <svg viewBox="0 0 400 400" class="w-full h-full" id="map-svg">
                                <!-- Background grid -->
                                <defs>
                                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                                        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e5e7eb" stroke-width="1"/>
                                    </pattern>
                                </defs>
                                <rect width="400" height="400" fill="url(#grid)"/>
                                
                                <!-- Routes (dotted lines) -->
                                <line x1="150" y1="200" x2="280" y2="120" stroke="#14B8A6" stroke-width="2" stroke-dasharray="5,5" opacity="0.6"/>
                                <line x1="280" y1="120" x2="320" y2="280" stroke="#14B8A6" stroke-width="2" stroke-dasharray="5,5" opacity="0.6"/>
                                <line x1="320" y1="280" x2="150" y2="200" stroke="#14B8A6" stroke-width="2" stroke-dasharray="5,5" opacity="0.6"/>
                                
                                <!-- Hotel Pin (Blue) -->
                                <g class="map-pin cursor-pointer">
                                    <circle cx="150" cy="200" r="20" fill="#3B82F6" opacity="0.2"/>
                                    <path d="M 150 180 C 140 180 132 188 132 198 C 132 213 150 220 150 220 C 150 220 168 213 168 198 C 168 188 160 180 150 180 Z" fill="#3B82F6" stroke="white" stroke-width="2"/>
                                    <circle cx="150" cy="198" r="4" fill="white"/>
                                </g>
                                
                                <!-- Wisata Pin (Green) -->
                                <g class="map-pin cursor-pointer">
                                    <circle cx="280" cy="120" r="20" fill="#10B981" opacity="0.2"/>
                                    <path d="M 280 100 C 270 100 262 108 262 118 C 262 133 280 140 280 140 C 280 140 298 133 298 118 C 298 108 290 100 280 100 Z" fill="#10B981" stroke="white" stroke-width="2"/>
                                    <circle cx="280" cy="118" r="4" fill="white"/>
                                </g>
                                
                                <!-- Makan Pin (Orange) -->
                                <g class="map-pin cursor-pointer">
                                    <circle cx="320" cy="280" r="20" fill="#F97316" opacity="0.2"/>
                                    <path d="M 320 260 C 310 260 302 268 302 278 C 302 293 320 300 320 300 C 320 300 338 293 338 278 C 338 268 330 260 320 260 Z" fill="#F97316" stroke="white" stroke-width="2"/>
                                    <circle cx="320" cy="278" r="4" fill="white"/>
                                </g>
                            </svg>
                            
                            <!-- Zoom Controls -->
                            <div class="absolute top-4 right-4 flex flex-col gap-2">
                                <button id="zoom-in" class="bg-white hover:bg-gray-100 p-2 rounded-lg shadow-lg transition-colors">
                                    <svg width="20" height="20" fill="none" stroke="currentColor" class="text-gray-700" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7"></path>
                                    </svg>
                                </button>
                                <button id="zoom-out" class="bg-white hover:bg-gray-100 p-2 rounded-lg shadow-lg transition-colors">
                                    <svg width="20" height="20" fill="none" stroke="currentColor" class="text-gray-700" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7"></path>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        
                        <!-- Map Legend -->
                        <div class="p-4 bg-gray-50 border-t border-gray-200">
                            <div class="flex justify-around text-sm">
                                <div class="flex items-center gap-2">
                                    <div class="w-4 h-4 rounded-full bg-blue-500"></div>
                                    <span class="text-gray-700">Hotel</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <div class="w-4 h-4 rounded-full bg-green-500"></div>
                                    <span class="text-gray-700">Wisata</span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <div class="w-4 h-4 rounded-full bg-orange-500"></div>
                                    <span class="text-gray-700">Makan</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    return container;
}

function setupDetailHandlers() {
    document.getElementById('back-to-results').addEventListener('click', () => {
        appState.currentPage = 'results';
        renderPage();
    });

    document.getElementById('back-to-results-2').addEventListener('click', () => {
        appState.currentPage = 'results';
        renderPage();
    });

    // Copy coordinates buttons
    document.querySelectorAll('.copy-coords').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const coords = e.currentTarget.getAttribute('data-coords');
            try {
                await navigator.clipboard.writeText(coords);
                const span = e.currentTarget.querySelector('span');
                const originalText = span.textContent;
                span.textContent = 'Tersalin!';
                setTimeout(() => {
                    span.textContent = originalText;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        });
    });

    // Zoom controls
    const mapSvg = document.getElementById('map-svg');
    let currentZoom = 1;

    document.getElementById('zoom-in').addEventListener('click', () => {
        currentZoom = Math.min(1.5, currentZoom + 0.1);
        mapSvg.style.transform = `scale(${currentZoom})`;
    });

    document.getElementById('zoom-out').addEventListener('click', () => {
        currentZoom = Math.max(0.8, currentZoom - 0.1);
        mapSvg.style.transform = `scale(${currentZoom})`;
    });
}

// Main Render Function
function renderPage() {
    const app = document.getElementById('app');
    app.innerHTML = '';

    let content;

    if (appState.currentPage === 'form') {
        content = renderFormPage();
        app.appendChild(content);
        setupFormHandlers();
    } else if (appState.currentPage === 'results') {
        content = renderResultsPage();
        app.appendChild(content);
        setupResultsHandlers();
    } else if (appState.currentPage === 'detail') {
        content = renderDetailPage();
        app.appendChild(content);
        setupDetailHandlers();
    }

    // Scroll to top
    window.scrollTo(0, 0);
}

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    renderPage();
});
