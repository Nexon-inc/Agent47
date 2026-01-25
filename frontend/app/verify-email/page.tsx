'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

function VerifyContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get('token');
    const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
    const [message, setMessage] = useState('Verifying your email...');

    useEffect(() => {
        if (!token) {
            setStatus('error');
            setMessage('Invalid verification link. Token is missing.');
            return;
        }

        const verifyEmail = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://agent47-backend-805021975902.us-central1.run.app';

                // Use backend API directly
                const response = await fetch(`${apiUrl}/api/v1/auth/verify?token=${token}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    setStatus('success');
                    setMessage('Email verified successfully! Redirecting...');
                    // Auto redirect after 3 seconds
                    setTimeout(() => {
                        router.push('/onboarding');
                    }, 3000);
                } else {
                    const data = await response.json();
                    setStatus('error');
                    setMessage(data.detail || 'Verification failed. Please try again.');
                }
            } catch (error) {
                console.error('Verification error:', error);
                setStatus('error');
                setMessage('An error occurred. Please try again later.');
            }
        };

        verifyEmail();
    }, [token, router]);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white p-4">
            <div className="w-full max-w-md p-8 bg-gray-900 rounded-lg shadow-xl border border-gray-800">
                <h1 className="text-2xl font-bold mb-6 text-center text-blue-400">Email Verification</h1>

                <div className="text-center">
                    {status === 'verifying' && (
                        <div className="flex flex-col items-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
                            <p className="text-gray-300">{message}</p>
                        </div>
                    )}

                    {status === 'success' && (
                        <div className="flex flex-col items-center">
                            <div className="h-16 w-16 bg-green-900/50 rounded-full flex items-center justify-center mb-4">
                                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                                </svg>
                            </div>
                            <p className="text-xl font-semibold text-green-400 mb-2">Success!</p>
                            <p className="text-gray-300 mb-6">{message}</p>
                            <Link
                                href="/onboarding"
                                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                            >
                                Continue to Onboarding
                            </Link>
                        </div>
                    )}

                    {status === 'error' && (
                        <div className="flex flex-col items-center">
                            <div className="h-16 w-16 bg-red-900/50 rounded-full flex items-center justify-center mb-4">
                                <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </div>
                            <p className="text-xl font-semibold text-red-400 mb-2">Verification Failed</p>
                            <p className="text-gray-300 mb-6">{message}</p>
                            <div className="flex gap-4">
                                <Link
                                    href="/auth/login"
                                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-md transition-colors"
                                >
                                    Back to Login
                                </Link>
                                <Link
                                    href="/contact"
                                    className="px-4 py-2 bg-transparent border border-gray-600 hover:bg-gray-800 text-white rounded-md transition-colors"
                                >
                                    Contact Support
                                </Link>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default function VerifyEmailPage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-gray-950 flex items-center justify-center text-white">Loading...</div>}>
            <VerifyContent />
        </Suspense>
    );
}
