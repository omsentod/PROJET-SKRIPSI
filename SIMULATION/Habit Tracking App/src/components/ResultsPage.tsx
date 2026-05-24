import { useState } from 'react';
import { Hotel, MapPin, UtensilsCrossed, ChevronDown, ChevronUp } from 'lucide-react';
import type { BudgetData, PackageOption } from '../App';

type ResultsPageProps = {
  budgetData: BudgetData;
  onViewDetail: (packageType: PackageOption) => void;
  onBackToForm: () => void;
};

type PackageData = {
  type: PackageOption;
  badge: string;
  badgeColor: string;
  status: string;
  hotel: {
    name: string;
    price: number;
    coords: string;
  };
  wisata: {
    name: string;
    price: number;
    coords: string;
  };
  makan: {
    name: string;
    price: number;
    coords: string;
  };
  totalHotel: number;
  totalWisata: number;
  totalMakan: number;
  totalPrice: number;
};

export default function ResultsPage({ budgetData, onViewDetail, onBackToForm }: ResultsPageProps) {
  const [expandedCard, setExpandedCard] = useState<PackageOption | null>(null);

  const packages: PackageData[] = [
    {
      type: 'hemat',
      badge: 'HEMAT',
      badgeColor: 'bg-green-500',
      status: 'Budget: Hemat',
      hotel: {
        name: 'SUPER OYO Flagship 90502 Holistay...',
        price: 347052,
        coords: '-7.9666, 112.6326',
      },
      wisata: {
        name: 'Masjid Tiban Malang',
        price: 10000,
        coords: '-8.0045, 112.6789',
      },
      makan: {
        name: 'Depot Gang Djangkrik Kawi Atas',
        price: 27049,
        coords: '-7.9756, 112.6298',
      },
      totalHotel: 347052,
      totalWisata: 20000,
      totalMakan: 324588,
      totalPrice: 691640,
    },
    {
      type: 'balanced',
      badge: 'BALANCED',
      badgeColor: 'bg-blue-500',
      status: 'Budget: Pas',
      hotel: {
        name: 'OYO Life 91931 Permata Brantas',
        price: 590409,
        coords: '-7.9556, 112.6198',
      },
      wisata: {
        name: 'Makam Ki Ageng Gribig',
        price: 5000,
        coords: '-8.0123, 112.6543',
      },
      makan: {
        name: 'Resto 52',
        price: 117331,
        coords: '-7.9623, 112.6412',
      },
      totalHotel: 590409,
      totalWisata: 10000,
      totalMakan: 1407972,
      totalPrice: 2008381,
    },
    {
      type: 'premium',
      badge: 'PREMIUM',
      badgeColor: 'bg-amber-500',
      status: 'Budget: Fancy',
      hotel: {
        name: 'Villa Malang MARRY IND Puncak Buring',
        price: 3644629,
        coords: '-7.9234, 112.6789',
      },
      wisata: {
        name: 'Pura Luhur Giri Arjuno',
        price: 2000,
        coords: '-7.8956, 112.7012',
      },
      makan: {
        name: 'Harmoni Cafe & Resto',
        price: 144714,
        coords: '-7.9445, 112.6534',
      },
      totalHotel: 3644629,
      totalWisata: 4000,
      totalMakan: 1736568,
      totalPrice: 5385197,
    },
  ];

  const toggleExpand = (packageType: PackageOption) => {
    setExpandedCard(expandedCard === packageType ? null : packageType);
  };

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <button
            onClick={onBackToForm}
            className="text-teal-600 hover:text-teal-700 mb-4 inline-flex items-center gap-2 font-medium"
          >
            ← Kembali ke Form
          </button>
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Rekomendasi Paket Wisata Untuk Anda
          </h1>
          <p className="text-lg text-gray-600">
            Pilih paket yang sesuai dengan budget dan preferensi Anda
          </p>
        </div>

        {/* Package Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {packages.map((pkg) => (
            <div
              key={pkg.type}
              className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow overflow-hidden"
            >
              {/* Badge */}
              <div className={`${pkg.badgeColor} text-white text-center py-2 font-bold text-sm tracking-wider`}>
                {pkg.badge}
              </div>

              <div className="p-6">
                {/* Status */}
                <div className="text-gray-600 mb-6 font-medium">{pkg.status}</div>

                {/* Hotel */}
                <div className="mb-5">
                  <div className="flex items-start gap-2 mb-1">
                    <Hotel size={18} className="text-teal-600 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-bold text-xs text-gray-500 mb-1">HOTEL</div>
                      <div className="font-medium text-gray-900 text-sm mb-1">
                        {pkg.hotel.name}
                      </div>
                      <div className="text-teal-600 font-bold">
                        Rp {pkg.hotel.price.toLocaleString('id-ID')} /malam
                      </div>
                      <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
                        <MapPin size={12} />
                        <span>{pkg.hotel.coords}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Wisata */}
                <div className="mb-5">
                  <div className="flex items-start gap-2 mb-1">
                    <MapPin size={18} className="text-teal-600 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-bold text-xs text-gray-500 mb-1">WISATA</div>
                      <div className="font-medium text-gray-900 text-sm mb-1">
                        {pkg.wisata.name}
                      </div>
                      <div className="text-teal-600 font-bold">
                        Rp {pkg.wisata.price.toLocaleString('id-ID')} /orang
                      </div>
                      <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
                        <MapPin size={12} />
                        <span>{pkg.wisata.coords}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Makan */}
                <div className="mb-5">
                  <div className="flex items-start gap-2 mb-1">
                    <UtensilsCrossed size={18} className="text-teal-600 mt-1 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="font-bold text-xs text-gray-500 mb-1">MAKAN</div>
                      <div className="font-medium text-gray-900 text-sm mb-1">
                        {pkg.makan.name}
                      </div>
                      <div className="text-teal-600 font-bold">
                        Rp {pkg.makan.price.toLocaleString('id-ID')} /porsi
                      </div>
                      <div className="flex items-center gap-1 text-xs text-gray-500 mt-1">
                        <MapPin size={12} />
                        <span>{pkg.makan.coords}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Rincian Biaya Toggle */}
                <button
                  onClick={() => toggleExpand(pkg.type)}
                  className="w-full flex items-center justify-between text-sm font-bold text-gray-700 py-2 border-t border-gray-200 hover:bg-gray-50 transition-colors"
                >
                  <span>Rincian Biaya</span>
                  {expandedCard === pkg.type ? (
                    <ChevronUp size={18} />
                  ) : (
                    <ChevronDown size={18} />
                  )}
                </button>

                {/* Expandable Cost Details */}
                {expandedCard === pkg.type && (
                  <div className="mt-3 pt-3 border-t border-gray-200 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Biaya Hotel:</span>
                      <span className="font-medium">Rp {pkg.totalHotel.toLocaleString('id-ID')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Biaya Wisata:</span>
                      <span className="font-medium">Rp {pkg.totalWisata.toLocaleString('id-ID')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Total Biaya Makan:</span>
                      <span className="font-medium">Rp {pkg.totalMakan.toLocaleString('id-ID')}</span>
                    </div>
                    <div className="border-t-2 border-gray-300 pt-2 mt-2"></div>
                  </div>
                )}

                {/* Total Price */}
                <div className="bg-teal-50 rounded-lg p-4 mt-4 border-2 border-teal-100">
                  <div className="text-xs font-bold text-gray-600 mb-1">
                    TOTAL HARGA PAKET
                  </div>
                  <div className="text-2xl font-bold text-teal-700">
                    Rp {pkg.totalPrice.toLocaleString('id-ID')}
                  </div>
                </div>

                {/* Remaining Budget */}
                <div className={`rounded-lg p-4 mt-3 border-2 ${
                  budgetData.totalBudget - pkg.totalPrice >= 0 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="text-xs font-bold text-gray-600 mb-1">
                    SISA ANGGARAN
                  </div>
                  <div className={`text-xl font-bold ${
                    budgetData.totalBudget - pkg.totalPrice >= 0 
                      ? 'text-green-700' 
                      : 'text-red-700'
                  }`}>
                    {budgetData.totalBudget - pkg.totalPrice >= 0 ? '+' : ''}
                    Rp {(budgetData.totalBudget - pkg.totalPrice).toLocaleString('id-ID')}
                  </div>
                  {budgetData.totalBudget - pkg.totalPrice < 0 && (
                    <div className="text-xs text-red-600 mt-1">
                      Melebihi budget Anda
                    </div>
                  )}
                </div>

                {/* Action Button */}
                <button
                  onClick={() => onViewDetail(pkg.type)}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 px-4 rounded-lg transition-colors mt-4"
                >
                  Lihat Detail & Peta
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}