import { useState } from 'react';
import FormPage from './components/FormPage';
import ResultsPage from './components/ResultsPage';
import DetailPage from './components/DetailPage';

export type BudgetData = {
  totalBudget: number;
  participants: number;
  duration: number;
};

export type PackageOption = 'hemat' | 'balanced' | 'premium';

export default function App() {
  const [currentPage, setCurrentPage] = useState<'form' | 'results' | 'detail'>('form');
  const [budgetData, setBudgetData] = useState<BudgetData>({
    totalBudget: 4500000,
    participants: 2,
    duration: 2,
  });
  const [selectedPackage, setSelectedPackage] = useState<PackageOption>('hemat');

  const handleFormSubmit = (data: BudgetData) => {
    setBudgetData(data);
    setCurrentPage('results');
  };

  const handleViewDetail = (packageType: PackageOption) => {
    setSelectedPackage(packageType);
    setCurrentPage('detail');
  };

  const handleBackToResults = () => {
    setCurrentPage('results');
  };

  const handleBackToForm = () => {
    setCurrentPage('form');
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {currentPage === 'form' && (
        <FormPage onSubmit={handleFormSubmit} initialData={budgetData} />
      )}
      {currentPage === 'results' && (
        <ResultsPage
          budgetData={budgetData}
          onViewDetail={handleViewDetail}
          onBackToForm={handleBackToForm}
        />
      )}
      {currentPage === 'detail' && (
        <DetailPage
          packageType={selectedPackage}
          budgetData={budgetData}
          onBack={handleBackToResults}
        />
      )}
    </div>
  );
}
