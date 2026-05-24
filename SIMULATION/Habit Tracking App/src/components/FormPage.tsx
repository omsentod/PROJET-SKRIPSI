import { useState } from 'react';
import { Wallet, Users, Calendar } from 'lucide-react';
import type { BudgetData } from '../App';

type FormPageProps = {
  onSubmit: (data: BudgetData) => void;
  initialData: BudgetData;
};

export default function FormPage({ onSubmit, initialData }: FormPageProps) {
  const [totalBudget, setTotalBudget] = useState(initialData.totalBudget);
  const [participants, setParticipants] = useState(initialData.participants);
  const [duration, setDuration] = useState(initialData.duration);
  const [budgetInput, setBudgetInput] = useState(initialData.totalBudget.toLocaleString('id-ID'));

  // Auto-calculations
  const budgetPerPerson = Math.floor(totalBudget / participants);
  const hotelRooms = Math.ceil(participants / 2);
  const mealCount = participants * duration * 3;

  const handleBudgetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '');
    setBudgetInput(value ? parseInt(value).toLocaleString('id-ID') : '');
    setTotalBudget(value ? parseInt(value) : 0);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ totalBudget, participants, duration });
  };

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Rencanakan Liburan Malang Anda
          </h1>
          <p className="text-lg text-gray-600">
            Isi detail perjalanan untuk mendapatkan rekomendasi paket wisata
          </p>
        </div>

        {/* Form Card */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-sm font-bold text-gray-500 tracking-wider mb-6">
            FORMULIR PENCARIAN PAKET
          </h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Total Budget */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Total Anggaran (Rupiah)
              </label>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-teal-600">
                  <Wallet size={20} />
                </div>
                <div className="absolute left-14 top-1/2 -translate-y-1/2 text-gray-500 font-medium">
                  Rp
                </div>
                <input
                  type="text"
                  value={budgetInput}
                  onChange={handleBudgetChange}
                  placeholder="Contoh: 4.500.000"
                  className="w-full pl-24 pr-4 py-3 border-2 border-gray-200 rounded-lg focus:border-teal-500 focus:outline-none transition-colors"
                  required
                />
              </div>
            </div>

            {/* Participants */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Jumlah Peserta (Orang)
              </label>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-teal-600">
                  <Users size={20} />
                </div>
                <div className="flex items-center">
                  <input
                    type="number"
                    value={participants}
                    onChange={(e) => setParticipants(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-full pl-14 pr-24 py-3 border-2 border-gray-200 rounded-lg focus:border-teal-500 focus:outline-none transition-colors"
                    min="1"
                    required
                  />
                  <div className="absolute right-2 flex gap-1">
                    <button
                      type="button"
                      onClick={() => setParticipants(Math.max(1, participants - 1))}
                      className="w-8 h-8 bg-gray-100 hover:bg-gray-200 rounded-lg font-bold text-gray-700 transition-colors"
                    >
                      −
                    </button>
                    <button
                      type="button"
                      onClick={() => setParticipants(participants + 1)}
                      className="w-8 h-8 bg-gray-100 hover:bg-gray-200 rounded-lg font-bold text-gray-700 transition-colors"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Duration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Durasi Liburan (Hari)
              </label>
              <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-teal-600">
                  <Calendar size={20} />
                </div>
                <div className="flex items-center">
                  <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-full pl-14 pr-24 py-3 border-2 border-gray-200 rounded-lg focus:border-teal-500 focus:outline-none transition-colors"
                    min="1"
                    required
                  />
                  <div className="absolute right-2 flex gap-1">
                    <button
                      type="button"
                      onClick={() => setDuration(Math.max(1, duration - 1))}
                      className="w-8 h-8 bg-gray-100 hover:bg-gray-200 rounded-lg font-bold text-gray-700 transition-colors"
                    >
                      −
                    </button>
                    <button
                      type="button"
                      onClick={() => setDuration(duration + 1)}
                      className="w-8 h-8 bg-gray-100 hover:bg-gray-200 rounded-lg font-bold text-gray-700 transition-colors"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Auto-calculation Panel */}
            <div className="bg-teal-50 rounded-lg p-6 border-2 border-teal-100">
              <h3 className="text-sm font-bold text-teal-900 mb-4 tracking-wider">
                HITUNGAN OTOMATIS:
              </h3>
              <div className="space-y-3">
                <div>
                  <div className="text-lg font-bold text-gray-900">
                    Budget Per Orang: Rp {budgetPerPerson.toLocaleString('id-ID')}
                  </div>
                  <div className="text-sm text-gray-600">
                    (total anggaran / orang)
                  </div>
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">
                    Kebutuhan Kamar Hotel: {hotelRooms} kamar
                  </div>
                  <div className="text-sm text-gray-600">
                    (1 kamar max 2 orang)
                  </div>
                </div>
                <div>
                  <div className="text-lg font-bold text-gray-900">
                    Kebutuhan Makan: {mealCount} kali
                  </div>
                  <div className="text-sm text-gray-600">
                    (Jumlah Orang × Jumlah Hari × 3 kali makan)
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-4 px-6 rounded-lg transition-colors shadow-lg hover:shadow-xl text-lg"
            >
              Cari Paket Wisata
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
