// FILE: src/pages/MobileConnect.tsx
// PHOENIX PROTOCOL - MOBILE BRIDGE PAGE V1.2 (THEME ALIGNMENT)
// 1. FIX: Utilized 'Loader2' to resolve unused variable warning.
// 2. THEME: Updated colors to use Kontabilisti AI palette (primary-start, success-start, accent-start).
// 3. UI: Standardized loading spinner to match the rest of the application.

import React, { useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Camera, CheckCircle, AlertTriangle, UploadCloud, Loader2 } from 'lucide-react';
import { apiService } from '../services/api';

const MobileConnect: React.FC = () => {
    const { token } = useParams<{ token: string }>();
    const [status, setStatus] = useState<'IDLE' | 'UPLOADING' | 'SUCCESS' | 'ERROR'>('IDLE');
    const [errorMessage, setErrorMessage] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !token) return;

        setStatus('UPLOADING');
        try {
            await apiService.publicMobileUpload(token, file);
            setStatus('SUCCESS');
        } catch (err: any) {
            console.error(err);
            setStatus('ERROR');
            setErrorMessage(err.response?.data?.detail || "Ngarkimi dështoi.");
        }
    };

    if (!token) return <div className="h-screen flex items-center justify-center bg-background-dark text-accent-start">Token mungon.</div>;

    return (
        <div className="min-h-screen bg-background-dark flex flex-col items-center justify-center p-6 text-center">
            {/* Header / Branding */}
            <div className="mb-12">
                <div className="w-16 h-16 bg-primary-start/20 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-primary-start/30">
                    <UploadCloud size={32} className="text-primary-start" />
                </div>
                <h1 className="text-2xl font-bold text-white mb-2">Kontabilisti AI Connect</h1>
                <p className="text-text-secondary text-sm">Skanoni dokumentin për analizë të menjëhershme në desktop.</p>
            </div>

            {/* Main Action Area */}
            <div className="w-full max-w-sm">
                {status === 'IDLE' && (
                    <div 
                        onClick={() => fileInputRef.current?.click()}
                        className="bg-gradient-to-b from-gray-800 to-gray-900 border border-gray-700 rounded-3xl p-10 cursor-pointer active:scale-95 transition-transform shadow-2xl"
                    >
                        <input 
                            type="file" 
                            ref={fileInputRef} 
                            className="hidden" 
                            accept="image/*" 
                            capture="environment" 
                            onChange={handleFileChange}
                        />
                        <div className="w-24 h-24 bg-primary-start rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-primary-start/30 animate-pulse">
                            <Camera size={40} className="text-white" />
                        </div>
                        <h2 className="text-xl font-bold text-white mb-2">Hap Kamerën</h2>
                        <p className="text-text-secondary text-xs">Ose zgjidhni një foto nga galeria</p>
                    </div>
                )}

                {status === 'UPLOADING' && (
                    <div className="bg-gray-900 border border-gray-800 rounded-3xl p-10">
                        <Loader2 className="w-20 h-20 text-primary-start animate-spin mx-auto mb-6" />
                        <h2 className="text-lg font-bold text-white">Duke analizuar...</h2>
                        <p className="text-text-secondary text-sm mt-2">Ju lutem prisni, po dërgojmë të dhënat.</p>
                    </div>
                )}

                {status === 'SUCCESS' && (
                    <div className="bg-success-start/10 border border-success-start/30 rounded-3xl p-10 animate-in zoom-in">
                        <div className="w-20 h-20 bg-success-start rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-success-start/20">
                            <CheckCircle size={40} className="text-white" />
                        </div>
                        <h2 className="text-xl font-bold text-white mb-2">Sukses!</h2>
                        <p className="text-text-secondary text-sm">Dokumenti u analizua. Shikoni ekranin e kompjuterit tuaj.</p>
                        <button onClick={() => setStatus('IDLE')} className="mt-8 px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-xl text-sm font-medium transition-colors">
                            Skano tjetër
                        </button>
                    </div>
                )}

                {status === 'ERROR' && (
                    <div className="bg-accent-start/10 border border-accent-start/30 rounded-3xl p-10 animate-in shake">
                        <div className="w-20 h-20 bg-accent-start rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-accent-start/20">
                            <AlertTriangle size={40} className="text-white" />
                        </div>
                        <h2 className="text-xl font-bold text-white mb-2">Gabim</h2>
                        <p className="text-accent-start/80 text-sm">{errorMessage}</p>
                        <button onClick={() => setStatus('IDLE')} className="mt-8 px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-xl text-sm font-medium transition-colors">
                            Provo përsëri
                        </button>
                    </div>
                )}
            </div>
            
            <div className="mt-12 text-text-secondary/60 text-xs">
                &copy; {new Date().getFullYear()} Kontabilisti AI | Secured Connection
            </div>
        </div>
    );
};

export default MobileConnect;