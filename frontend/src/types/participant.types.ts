export interface ParticipantData {
    email: string;
    name?: string;
    isActive: boolean;
    joinedAt: string;
    lastReadAt?: string;
}

export interface ParticipantJoinRequest {
    token: string;
    name?: string;
}

export interface ParticipantJoinResponse {
    message: string;
    conversation_id: string;
    participant_token: string;
    name?: string;
    email: string;
}

export interface ParticipantMessageMetadata {
    participant_name?: string;
    participant_email: string;
    is_owner: boolean;
}

export enum ParticipantStatus {
    ACTIVE = 'active',
    INACTIVE = 'inactive',
    LEFT = 'left'
}
