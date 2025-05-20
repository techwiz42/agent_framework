import { NextResponse } from 'next/server';
import { api } from '@/services/api';
import type { ParticipantJoinRequest, ParticipantJoinResponse } from '@/types/participant.types';
import { AxiosError } from 'axios';

export async function POST(request: Request) {
    try {
        const body: ParticipantJoinRequest = await request.json();

        const response = await api.post<ParticipantJoinResponse>(
            '/api/conversations/join',
            body,
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );

        return NextResponse.json(response.data);
    } catch (error) {
        // Type guard to handle potential axios error
        if (error instanceof Error) {
            const axiosError = error as AxiosError;
            console.error('Error joining conversation:', error);
            
            return NextResponse.json(
                {
                    detail: axiosError.response?.data || 'Failed to join conversation'
                },
                { 
                    status: (axiosError.response as { status?: number })?.status || 500 
                }
            );
        }

        // Fallback for unexpected error types
        console.error('Unexpected error:', error);
        return NextResponse.json(
            { detail: 'An unexpected error occurred' },
            { status: 500 }
        );
    }
}
