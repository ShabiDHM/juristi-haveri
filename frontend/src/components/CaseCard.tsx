// FILE: src/components/CaseCard.tsx
// PHOENIX PROTOCOL - CASE CARD V7.0 (ACCOUNTING TRANSFORMATION)
// 1. REFACTOR: Transformed UI from "Legal Case" to "Client / Business Profile".
// 2. ICONS: Swapped generic icons for Financial/Business icons (Building, Receipt, Calculator).
// 3. LOGIC: Highlighted Company Name and Fiscal details.
// 4. STATUS: 100% Accounting Aligned.

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Case } from '../data/types';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Trash2, Receipt, AlertTriangle, Calculator, Building2, Mail, Phone, TrendingUp } from 'lucide-react';

interface CaseCardProps {
  caseData: Case;
  onDelete: (caseId: string) => void;
}

const CaseCard: React.FC<CaseCardProps> = ({ caseData, onDelete }) => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const handleCardClick = () => {
    navigate(`/cases/${caseData.id}`);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation(); 
    onDelete(caseData.id);
  };

  const handleCalendarNav = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigate('/calendar');
  };

  const formattedDate = new Date(caseData.created_at).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).replace(/\//g, '.');

  // Logic: In Accounting, "Title" is usually the Company Name
  const hasTitle = caseData.title && caseData.title.trim() !== '';
  const displayTitle = hasTitle ? caseData.title : (t('caseView.unnamedCase', 'Klient pa Emër'));

  return (
    <motion.div 
      onClick={handleCardClick}
      className="glass-panel group relative flex flex-col justify-between h-full p-6 rounded-2xl transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl cursor-pointer border border-white/5 hover:border-primary-start/30"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      whileTap={{ scale: 0.99 }}
    >
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-primary-start/5 to-secondary-end/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />

      <div>
        {/* Header Section: Company Identity */}
        <div className="flex flex-col mb-4 relative z-10">
          <div className="flex justify-between items-start gap-2">
            <div className="flex flex-col">
                <div className="flex items-center gap-2 mb-1">
                    <Building2 className="w-4 h-4 text-primary-start" />
                    <span className="text-[10px] font-bold text-primary-start uppercase tracking-widest">{t('caseCard.companyLabel', 'KOMPANIA / KLIENTI')}</span>
                </div>
                <h2 className={`text-lg font-black line-clamp-2 leading-tight tracking-tight uppercase ${!hasTitle ? 'text-text-secondary italic' : 'text-white group-hover:text-primary-start transition-colors'}`}>
                    {displayTitle}
                </h2>
            </div>
          </div>
          
          <div className="flex items-center gap-2 mt-2">
            <p className="text-[10px] text-text-secondary font-bold uppercase tracking-wider opacity-60">
                Regjistruar: <span className="text-white">{formattedDate}</span>
            </p>
          </div>
        </div>
        
        {/* Contact Representative Section */}
        <div className="flex flex-col mb-6 relative z-10 bg-white/5 rounded-xl p-3 border border-white/5">
          <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/5">
             <span className="text-[10px] font-bold text-text-secondary uppercase tracking-widest">{t('caseCard.contactLabel', 'Përfaqësuesi')}</span>
          </div>
          
          <div className="space-y-1.5 pl-1">
              <p className="text-sm font-bold text-white truncate">
                {caseData.client?.name || t('general.notAvailable', 'N/A')}
              </p>
              
              {caseData.client?.email && (
                  <div className="flex items-center gap-2 text-xs text-text-secondary font-medium">
                      <Mail className="w-3 h-3 text-primary-start" />
                      <span className="truncate">{caseData.client.email}</span>
                  </div>
              )}
              {caseData.client?.phone && (
                  <div className="flex items-center gap-2 text-xs text-text-secondary font-medium">
                      <Phone className="w-3 h-3 text-primary-start" />
                      <span className="truncate">{caseData.client.phone}</span>
                  </div>
              )}
          </div>
        </div>
      </div>
      
      <div className="relative z-10 mt-auto">
        {/* Statistics Section */}
        <div className="pt-4 border-t border-white/5 flex items-center justify-between gap-2">
          
          <div className="flex items-center gap-3">
              {/* Invoices/Documents */}
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5" title={`${caseData.document_count || 0} Dokumente`}>
                <Receipt className="h-3.5 w-3.5 text-blue-400" />
                <span className="text-xs font-bold text-white">{caseData.document_count || 0}</span>
              </div>

              {/* Tax Deadlines (Alerts) */}
              <button 
                onClick={handleCalendarNav}
                className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-accent-start/10 border border-accent-start/20 hover:bg-accent-start/20 transition-colors" 
                title={`${caseData.alert_count || 0} Afate Tatimore`}
              >
                <AlertTriangle className="h-3.5 w-3.5 text-accent-start animate-pulse" />
                <span className="text-xs font-bold text-accent-start">{caseData.alert_count || 0}</span>
              </button>

              {/* Financial Events */}
              <button 
                onClick={handleCalendarNav}
                className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-secondary-start/10 border border-secondary-start/20 hover:bg-secondary-start/20 transition-colors" 
                title={`${caseData.event_count || 0} Ngjarje Financiare`}
              >
                <Calculator className="h-3.5 w-3.5 text-secondary-start" />
                <span className="text-xs font-bold text-secondary-start">{caseData.event_count || 0}</span>
              </button>
          </div>
        </div>

        {/* Footer: Actions */}
        <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
          <span className="text-[10px] font-black uppercase tracking-widest text-primary-start group-hover:text-primary-end transition-colors flex items-center gap-2">
            <TrendingUp size={14} />
            {t('general.view', 'Shiko Pasqyrën')} 
          </span>
          
          <motion.button
            onClick={handleDeleteClick}
            className="p-2 -mr-2 rounded-lg text-text-secondary hover:text-red-400 hover:bg-red-500/10 transition-colors z-20 relative"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            title={t('general.delete', 'Fshij')}
          >
            <Trash2 className="h-4 w-4" />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};

export default CaseCard;