// FILE: src/components/BrandLogo.tsx
// PHOENIX PROTOCOL - PLATFORM IDENTITY V2.2 (KONTABILISTI AI)
// 1. UPDATED: Replaced 'Scale' icon with 'Calculator' for accountant theme.
// 2. PURPOSE: Represents the SaaS Platform ("Kontabilisti AI").
// 3. USAGE: Use ONLY in Sidebar, Navbar, and Auth screens. NEVER in user-generated content.

import React from 'react';
import { Calculator } from 'lucide-react'; // Changed from Scale to Calculator

interface BrandLogoProps {
  className?: string;
  showText?: boolean;
}

const BrandLogo: React.FC<BrandLogoProps> = ({ className = "", showText = true }) => {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Platform Icon - Calculator for Accounting */}
      <div className="w-8 h-8 flex-shrink-0 bg-white/5 border border-white/10 rounded-lg flex items-center justify-center shadow-lg backdrop-blur-md">
        <Calculator className="w-5 h-5 text-white" />
      </div>
      
      {/* Platform Name */}
      {showText && (
        <span className="text-xl font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent whitespace-nowrap">
          Kontabilisti AI
        </span>
      )}
    </div>
  );
};

export default BrandLogo;