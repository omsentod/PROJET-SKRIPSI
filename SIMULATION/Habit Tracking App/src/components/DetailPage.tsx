import { useState } from 'react';
import { MapPin, Copy, Check, Maximize2, ZoomIn, ZoomOut, Hotel, UtensilsCrossed } from 'lucide-react';
import type { BudgetData, PackageOption } from '../App';

type DetailPageProps = {
  packageType: PackageOption;
  budgetData: BudgetData;
  onBack: () => void;
};

type PackageDetails = {
  title: string;
  totalPrice: number;
  hotel: {
    name: string;
    fullName: string;
    price: number;
    coords: string;
    lat: number;
    lng: number;
  };
  wisata: {
    name: string;
    fullName: string;
    price: number;
    coords: string;
    lat: number;
    lng: number;
  };
  makan: {
    name: string;
    fullName: string;
    price: number;
    avgTotal: number;
    coords: string;
    lat: number;
    lng: number;
  };
  totalHotel: number;
  totalWisata: number;
  totalMakan: number;
};

export default function DetailPage({ packageType, budgetData, onBack }: DetailPageProps) {
  const [copiedCoord, setCopiedCoord] = useState<string | null>(null);
  const [mapZoom, setMapZoom] = useState(13);
  const [hoveredPin, setHoveredPin] = useState<'hotel' | 'wisata' | 'makan' | null>(null);

  const packageDetails: Record<PackageOption, PackageDetails> = {
    hemat: {
      title: 'Opsi 1 (Hemat)',
      totalPrice: 691640,
      hotel: {
        name: 'SUPER OYO Flagship 90502',
        fullName: 'SUPER OYO Flagship 90502 Holistay Malang New',
        price: 347052,
        coords: '-7.9666, 112.6326',
        lat: -7.9666,
        lng: 112.6326,
      },
      wisata: {
        name: 'Masjid Tiban Malang',
        fullName: 'Masjid Tiban Malang (pp.Salafiah Bihaaru Bahri)',
        price: 10000,
        coords: '-8.0045, 112.6789',
        lat: -8.0045,
        lng: 112.6789,
      },
      makan: {
        name: 'Depot Gang Djangkrik',
        fullName: 'Depot Gang Djangkrik Kawi Atas Malang',
        price: 27049,
        avgTotal: 324588,
        coords: '-7.9756, 112.6298',
        lat: -7.9756,
        lng: 112.6298,
      },
      totalHotel: 347052,
      totalWisata: 20000,
      totalMakan: 324588,
    },
    balanced: {
      title: 'Opsi 2 (Balanced)',
      totalPrice: 2008381,
      hotel: {
        name: 'OYO Life 91931',
        fullName: 'OYO Life 91931 Permata Brantas',
        price: 590409,
        coords: '-7.9556, 112.6198',
        lat: -7.9556,
        lng: 112.6198,
      },
      wisata: {
        name: 'Makam Ki Ageng Gribig',
        fullName: 'Makam Ki Ageng Gribig',
        price: 5000,
        coords: '-8.0123, 112.6543',
        lat: -8.0123,
        lng: 112.6543,
      },
      makan: {
        name: 'Resto 52',
        fullName: 'Resto 52',
        price: 117331,
        avgTotal: 1407972,
        coords: '-7.9623, 112.6412',
        lat: -7.9623,
        lng: 112.6412,
      },
      totalHotel: 590409,
      totalWisata: 10000,
      totalMakan: 1407972,
    },
    premium: {
      title: 'Opsi 3 (Premium)',
      totalPrice: 5385197,
      hotel: {
        name: 'Villa Malang MARRY IND',
        fullName: 'Villa Malang MARRY IND Puncak Buring',
        price: 3644629,
        coords: '-7.9234, 112.6789',
        lat: -7.9234,
        lng: 112.6789,
      },
      wisata: {
        name: 'Pura Luhur Giri Arjuno',
        fullName: 'Pura Luhur Giri Arjuno',
        price: 2000,
        coords: '-7.8956, 112.7012',
        lat: -7.8956,
        lng: 112.7012,
      },
      makan: {
        name: 'Harmoni Cafe & Resto',
        fullName: 'Harmoni Cafe & Resto',
        price: 144714,
        avgTotal: 1736568,
        coords: '-7.9445, 112.6534',
        lat: -7.9445,
        lng: 112.6534,
      },
      totalHotel: 3644629,
      totalWisata: 4000,
      totalMakan: 1736568,
    },
  };

  const pkg = packageDetails[packageType];

  const calculateDistance = (lat1: number, lng1: number, lat2: number, lng2: number) => {
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
  };

  const hotelToWisata = calculateDistance(
    pkg.hotel.lat,
    pkg.hotel.lng,
    pkg.wisata.lat,
    pkg.wisata.lng
  );
  const wisataToMakan = calculateDistance(
    pkg.wisata.lat,
    pkg.wisata.lng,
    pkg.makan.lat,
    pkg.makan.lng
  );
  const makanToHotel = calculateDistance(
    pkg.makan.lat,
    pkg.makan.lng,
    pkg.hotel.lat,
    pkg.hotel.lng
  );
  const totalDistance = (
    parseFloat(hotelToWisata) +
    parseFloat(wisataToMakan) +
    parseFloat(makanToHotel)
  ).toFixed(1);

  const copyCoords = (coords: string) => {
    navigator.clipboard.writeText(coords);
    setCopiedCoord(coords);
    setTimeout(() => setCopiedCoord(null), 2000);
  };

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Page Title */}
        <div className="mb-6">
          <button
            onClick={onBack}
            className="text-teal-600 hover:text-teal-700 mb-3 inline-flex items-center gap-2 font-medium"
          >
            ← Kembali ke Pilihan
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            Detail Paket: {pkg.title} - Rp {pkg.totalPrice.toLocaleString('id-ID')}
          </h1>
        </div>

        {/* Split Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left Side - Details (60%) */}
          <div className="lg:col-span-3 space-y-6">
            {/* Hotel Section */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="aspect-video bg-gradient-to-br from-blue-200 to-blue-300 flex items-center justify-center">
                <Hotel size={64} className="text-blue-600 opacity-40" />
              </div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="text-xs font-bold text-gray-500 mb-1">HOTEL</div>
                    <h3 className="text-xl font-bold text-gray-900">{pkg.hotel.fullName}</h3>
                  </div>
                  <div className="bg-teal-100 text-teal-700 font-bold px-3 py-1 rounded-lg text-sm whitespace-nowrap">
                    Rp {pkg.hotel.price.toLocaleString('id-ID')} /malam
                  </div>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <div className="flex items-center gap-1 text-gray-600">
                    <MapPin size={14} />
                    <span>{pkg.hotel.coords}</span>
                  </div>
                  <button
                    onClick={() => copyCoords(pkg.hotel.coords)}
                    className="text-teal-600 hover:text-teal-700 flex items-center gap-1"
                  >
                    {copiedCoord === pkg.hotel.coords ? (
                      <>
                        <Check size={14} />
                        <span>Tersalin</span>
                      </>
                    ) : (
                      <>
                        <Copy size={14} />
                        <span>Salin</span>
                      </>
                    )}
                  </button>
                  <a
                    href={`https://www.google.com/maps?q=${pkg.hotel.coords}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700"
                  >
                    Lihat di Google Maps
                  </a>
                </div>
              </div>
            </div>

            {/* Wisata Section */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="aspect-video bg-gradient-to-br from-green-200 to-green-300 flex items-center justify-center">
                <MapPin size={64} className="text-green-600 opacity-40" />
              </div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="text-xs font-bold text-gray-500 mb-1">WISATA</div>
                    <h3 className="text-xl font-bold text-gray-900">{pkg.wisata.fullName}</h3>
                  </div>
                  <div className="bg-teal-100 text-teal-700 font-bold px-3 py-1 rounded-lg text-sm whitespace-nowrap">
                    Rp {pkg.wisata.price.toLocaleString('id-ID')} /tiket
                  </div>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <div className="flex items-center gap-1 text-gray-600">
                    <MapPin size={14} />
                    <span>{pkg.wisata.coords}</span>
                  </div>
                  <button
                    onClick={() => copyCoords(pkg.wisata.coords)}
                    className="text-teal-600 hover:text-teal-700 flex items-center gap-1"
                  >
                    {copiedCoord === pkg.wisata.coords ? (
                      <>
                        <Check size={14} />
                        <span>Tersalin</span>
                      </>
                    ) : (
                      <>
                        <Copy size={14} />
                        <span>Salin</span>
                      </>
                    )}
                  </button>
                  <a
                    href={`https://www.google.com/maps?q=${pkg.wisata.coords}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700"
                  >
                    Lihat di Google Maps
                  </a>
                </div>
              </div>
            </div>

            {/* Makan Section */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="aspect-video bg-gradient-to-br from-orange-200 to-orange-300 flex items-center justify-center">
                <UtensilsCrossed size={64} className="text-orange-600 opacity-40" />
              </div>
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="text-xs font-bold text-gray-500 mb-1">MAKAN</div>
                    <h3 className="text-xl font-bold text-gray-900">{pkg.makan.fullName}</h3>
                  </div>
                  <div className="bg-teal-100 text-teal-700 font-bold px-3 py-1 rounded-lg text-sm whitespace-nowrap">
                    Rp {pkg.makan.price.toLocaleString('id-ID')} /porsi
                  </div>
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  Rata-rata untuk {budgetData.participants * budgetData.duration * 3}x makan:{' '}
                  <span className="font-bold text-gray-900">
                    Rp {pkg.makan.avgTotal.toLocaleString('id-ID')}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <div className="flex items-center gap-1 text-gray-600">
                    <MapPin size={14} />
                    <span>{pkg.makan.coords}</span>
                  </div>
                  <button
                    onClick={() => copyCoords(pkg.makan.coords)}
                    className="text-teal-600 hover:text-teal-700 flex items-center gap-1"
                  >
                    {copiedCoord === pkg.makan.coords ? (
                      <>
                        <Check size={14} />
                        <span>Tersalin</span>
                      </>
                    ) : (
                      <>
                        <Copy size={14} />
                        <span>Salin</span>
                      </>
                    )}
                  </button>
                  <a
                    href={`https://www.google.com/maps?q=${pkg.makan.coords}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700"
                  >
                    Lihat di Google Maps
                  </a>
                </div>
              </div>
            </div>

            {/* Rincian Biaya Panel */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="font-bold text-lg mb-4">RINCIAN BIAYA:</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2 border-b border-gray-200">
                  <span className="text-gray-700 flex items-center gap-2">
                    <Check className="text-green-600" size={18} />
                    Hotel
                  </span>
                  <span className="font-bold">Rp {pkg.totalHotel.toLocaleString('id-ID')}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-200">
                  <span className="text-gray-700 flex items-center gap-2">
                    <Check className="text-green-600" size={18} />
                    Wisata
                  </span>
                  <span className="font-bold">Rp {pkg.totalWisata.toLocaleString('id-ID')}</span>
                </div>
                <div className="flex justify-between items-center py-2 border-b border-gray-200">
                  <span className="text-gray-700 flex items-center gap-2">
                    <Check className="text-green-600" size={18} />
                    Makan
                  </span>
                  <span className="font-bold">Rp {pkg.totalMakan.toLocaleString('id-ID')}</span>
                </div>
                <div className="flex justify-between items-center pt-3 border-t-2 border-gray-300">
                  <span className="font-bold text-lg">TOTAL</span>
                  <span className="font-bold text-2xl text-teal-600">
                    Rp {pkg.totalPrice.toLocaleString('id-ID')}
                  </span>
                </div>
              </div>
            </div>

            {/* Distance Info Panel */}
            <div className="bg-teal-50 rounded-xl p-6 border-2 border-teal-100">
              <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                <MapPin className="text-teal-600" />
                INFORMASI JARAK:
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-700">Hotel → Wisata:</span>
                  <span className="font-bold">{hotelToWisata} km</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">Wisata → Makan:</span>
                  <span className="font-bold">{wisataToMakan} km</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-700">Makan → Hotel:</span>
                  <span className="font-bold">{makanToHotel} km</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-teal-200">
                  <span className="font-bold">Total jarak tempuh:</span>
                  <span className="font-bold text-teal-700">{totalDistance} km</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button className="flex-1 bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 px-6 rounded-lg transition-colors">
                Simpan Paket
              </button>
              <button
                onClick={onBack}
                className="flex-1 bg-white hover:bg-gray-50 text-gray-700 font-bold py-3 px-6 rounded-lg border-2 border-gray-300 transition-colors"
              >
                Kembali ke Pilihan
              </button>
            </div>
          </div>

          {/* Right Side - Map (40%) */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-lg overflow-hidden sticky top-8">
              {/* Map Container */}
              <div className="relative bg-gradient-to-br from-slate-100 to-slate-200 aspect-square">
                {/* Mock Map */}
                <svg
                  viewBox="0 0 400 400"
                  className="w-full h-full"
                  style={{ transform: `scale(${1 + (mapZoom - 13) * 0.1})` }}
                >
                  {/* Background grid */}
                  <defs>
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path
                        d="M 40 0 L 0 0 0 40"
                        fill="none"
                        stroke="#e5e7eb"
                        strokeWidth="1"
                      />
                    </pattern>
                  </defs>
                  <rect width="400" height="400" fill="url(#grid)" />

                  {/* Routes (dotted lines) */}
                  <line
                    x1="150"
                    y1="200"
                    x2="280"
                    y2="120"
                    stroke="#14B8A6"
                    strokeWidth="2"
                    strokeDasharray="5,5"
                    opacity="0.6"
                  />
                  <line
                    x1="280"
                    y1="120"
                    x2="320"
                    y2="280"
                    stroke="#14B8A6"
                    strokeWidth="2"
                    strokeDasharray="5,5"
                    opacity="0.6"
                  />
                  <line
                    x1="320"
                    y1="280"
                    x2="150"
                    y2="200"
                    stroke="#14B8A6"
                    strokeWidth="2"
                    strokeDasharray="5,5"
                    opacity="0.6"
                  />

                  {/* Hotel Pin (Blue) */}
                  <g
                    onMouseEnter={() => setHoveredPin('hotel')}
                    onMouseLeave={() => setHoveredPin(null)}
                    className="cursor-pointer"
                  >
                    <circle cx="150" cy="200" r="20" fill="#3B82F6" opacity="0.2" />
                    <path
                      d="M 150 180 C 140 180 132 188 132 198 C 132 213 150 220 150 220 C 150 220 168 213 168 198 C 168 188 160 180 150 180 Z"
                      fill="#3B82F6"
                      stroke="white"
                      strokeWidth="2"
                    />
                    <circle cx="150" cy="198" r="4" fill="white" />
                    {hoveredPin === 'hotel' && (
                      <g>
                        <rect
                          x="90"
                          y="155"
                          width="120"
                          height="20"
                          fill="white"
                          stroke="#3B82F6"
                          strokeWidth="2"
                          rx="4"
                        />
                        <text
                          x="150"
                          y="169"
                          textAnchor="middle"
                          fontSize="10"
                          fill="#1F2937"
                          fontWeight="bold"
                        >
                          {pkg.hotel.name}
                        </text>
                      </g>
                    )}
                  </g>

                  {/* Wisata Pin (Green) */}
                  <g
                    onMouseEnter={() => setHoveredPin('wisata')}
                    onMouseLeave={() => setHoveredPin(null)}
                    className="cursor-pointer"
                  >
                    <circle cx="280" cy="120" r="20" fill="#10B981" opacity="0.2" />
                    <path
                      d="M 280 100 C 270 100 262 108 262 118 C 262 133 280 140 280 140 C 280 140 298 133 298 118 C 298 108 290 100 280 100 Z"
                      fill="#10B981"
                      stroke="white"
                      strokeWidth="2"
                    />
                    <circle cx="280" cy="118" r="4" fill="white" />
                    {hoveredPin === 'wisata' && (
                      <g>
                        <rect
                          x="220"
                          y="75"
                          width="120"
                          height="20"
                          fill="white"
                          stroke="#10B981"
                          strokeWidth="2"
                          rx="4"
                        />
                        <text
                          x="280"
                          y="89"
                          textAnchor="middle"
                          fontSize="10"
                          fill="#1F2937"
                          fontWeight="bold"
                        >
                          {pkg.wisata.name}
                        </text>
                      </g>
                    )}
                  </g>

                  {/* Makan Pin (Orange) */}
                  <g
                    onMouseEnter={() => setHoveredPin('makan')}
                    onMouseLeave={() => setHoveredPin(null)}
                    className="cursor-pointer"
                  >
                    <circle cx="320" cy="280" r="20" fill="#F97316" opacity="0.2" />
                    <path
                      d="M 320 260 C 310 260 302 268 302 278 C 302 293 320 300 320 300 C 320 300 338 293 338 278 C 338 268 330 260 320 260 Z"
                      fill="#F97316"
                      stroke="white"
                      strokeWidth="2"
                    />
                    <circle cx="320" cy="278" r="4" fill="white" />
                    {hoveredPin === 'makan' && (
                      <g>
                        <rect
                          x="260"
                          y="235"
                          width="120"
                          height="20"
                          fill="white"
                          stroke="#F97316"
                          strokeWidth="2"
                          rx="4"
                        />
                        <text
                          x="320"
                          y="249"
                          textAnchor="middle"
                          fontSize="10"
                          fill="#1F2937"
                          fontWeight="bold"
                        >
                          {pkg.makan.name}
                        </text>
                      </g>
                    )}
                  </g>
                </svg>

                {/* Zoom Controls */}
                <div className="absolute top-4 right-4 flex flex-col gap-2">
                  <button
                    onClick={() => setMapZoom(Math.min(15, mapZoom + 1))}
                    className="bg-white hover:bg-gray-100 p-2 rounded-lg shadow-lg transition-colors"
                  >
                    <ZoomIn size={20} className="text-gray-700" />
                  </button>
                  <button
                    onClick={() => setMapZoom(Math.max(11, mapZoom - 1))}
                    className="bg-white hover:bg-gray-100 p-2 rounded-lg shadow-lg transition-colors"
                  >
                    <ZoomOut size={20} className="text-gray-700" />
                  </button>
                  <button className="bg-white hover:bg-gray-100 p-2 rounded-lg shadow-lg transition-colors">
                    <Maximize2 size={20} className="text-gray-700" />
                  </button>
                </div>
              </div>

              {/* Map Legend */}
              <div className="p-4 bg-gray-50 border-t border-gray-200">
                <div className="flex justify-around text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full bg-blue-500"></div>
                    <span className="text-gray-700">Hotel</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full bg-green-500"></div>
                    <span className="text-gray-700">Wisata</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full bg-orange-500"></div>
                    <span className="text-gray-700">Makan</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
