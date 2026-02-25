import React, { createContext, useState, useContext, useEffect } from 'react';
import translations from '../i18n/translations.json';

const LanguageContext = createContext();

export const LanguageProvider = ({ children }) => {
    const [language, setLanguage] = useState(localStorage.getItem('language') || 'EN');

    const toggleLanguage = () => {
        const newLang = language === 'EN' ? 'ID' : 'EN';
        setLanguage(newLang);
        localStorage.setItem('language', newLang);
    };

    const t = (key) => {
        return translations[language][key] || key;
    };

    useEffect(() => {
        // Sync with other tabs/windows if needed
        const handleStorageChange = (e) => {
            if (e.key === 'language') {
                setLanguage(e.newValue);
            }
        };
        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, []);

    return (
        <LanguageContext.Provider value={{ language, toggleLanguage, setLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
};

export const useLanguage = () => {
    const context = useContext(LanguageContext);
    if (!context) {
        throw new Error('useLanguage must be used within a LanguageProvider');
    }
    return context;
};
