export interface ParticipantSession {
    token: string;
    conversationId: string;
    name?: string;
    email: string;
    invitationToken?: string;
}

export const participantStorage = {
    getSession(conversationId: string): ParticipantSession | null {
        // Check if sessionStorage is available (client-side)
        if (typeof sessionStorage !== 'undefined') {
            try {
                const key = `participant_session_${conversationId}`;
                const data = sessionStorage.getItem(key);
                return data ? JSON.parse(data) : null;
            } catch (e) {
                console.error('Error reading participant session:', e);
                return null;
            }
        }
        // Return null if not in browser environment
        return null;
    },

    setSession(conversationId: string, session: ParticipantSession): void {
        if (typeof sessionStorage !== 'undefined') {
            try {
                const key = `participant_session_${conversationId}`;
                sessionStorage.setItem(key, JSON.stringify(session));
            } catch (e) {
                console.error('Error saving participant session:', e);
            }
        }
    },

    // Similar modifications for other methods...
    getAllSessions(): ParticipantSession[] {
        if (typeof sessionStorage !== 'undefined') {
            const sessions: ParticipantSession[] = [];
            try {
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    if (key?.startsWith('participant_session_')) {
                        const data = sessionStorage.getItem(key);
                        if (data) {
                            sessions.push(JSON.parse(data));
                        }
                    }
                }
            } catch (e) {
                console.error('Error reading all sessions:', e);
            }
            return sessions;
        }
        return [];
    },

    clearSession(conversationId: string): void {
        if (typeof sessionStorage !== 'undefined') {
            const key = `participant_session_${conversationId}`;
            sessionStorage.removeItem(key);
        }
    },

    isParticipant(conversationId: string): boolean {
        return !!this.getSession(conversationId);
    }
};
