import React from 'react';

const ErrorFallback = ({ error, resetErrorBoundary }) => {
    return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100 p-4">
            <div className="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden p-8 border border-gray-100 text-center">
                <div className="mb-6 flex justify-center">
                    <div className="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                    </div>
                </div>

                <h2 className="text-2xl font-bold text-gray-800 mb-2">Oops! Something went wrong</h2>
                <p className="text-gray-600 text-sm mb-6">
                    We've encountered an unexpected error. Our team has been notified.
                </p>

                {/* Developer view - uncomment for debugging in production but safe to show locally */}
                <div className="bg-red-50 p-4 rounded-lg text-left overflow-auto mb-6 max-h-32 text-xs text-red-800 border border-red-100 font-mono">
                    {error.message}
                </div>

                <button
                    onClick={resetErrorBoundary}
                    className="w-full bg-[#FF8000] text-white py-3 px-4 shadow-md rounded-[50px] font-semibold hover:bg-orange-600 transition duration-300"
                >
                    Try Again
                </button>
                <button
                    onClick={() => window.location.href = '/'}
                    className="w-full mt-3 bg-white text-gray-600 py-3 px-4 shadow-sm border border-gray-200 rounded-[50px] font-semibold hover:bg-gray-50 transition duration-300"
                >
                    Return Home
                </button>
            </div>
        </div>
    );
};

export default ErrorFallback;
